import botocore.exceptions
import cv2
import numpy as np

from fastapi.responses import StreamingResponse
from typing import BinaryIO

from src.api.exceptions import FileBlobHasNoExtension
from src.core.filestorage.abc_connector import S3ConnectorContextManager
from src.core.filestorage.exceptions import MinIOConnectorError, ConnectorMethodNotAllowed


class S3ImageUploader(S3ConnectorContextManager):
    def __init__(self, access_key: str, secret_key: str):
        super().__init__(access_key, secret_key)

    def download_file(self, **kwargs):
        raise ConnectorMethodNotAllowed(class_name=self.__class__.__name__)

    def upload_file(self, file_obj: BinaryIO, file_name: str) -> True:
        if "." not in file_name:
            raise FileBlobHasNoExtension()
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=file_name)
            raise MinIOConnectorError(code=409, message="File already exists in bucket")
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                try:
                    self.client.upload_fileobj(file_obj, self.bucket_name, file_name)
                    return True
                except botocore.exceptions.ClientError as e:
                    raise MinIOConnectorError(code=500, message=f"Cannot upload file: {e}") from e
        except Exception as e:
            raise MinIOConnectorError(code=500, message=f"Unexpected error: {e}") from e

    def delete_object(self, file_name: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket_name, key=file_name)
        except botocore.exceptions.ClientError as e:
            raise MinIOConnectorError(code=500, message=f"MinIO error: {str(e)}") from e
        except Exception as e:
            raise MinIOConnectorError(code=500, message=f"Unexpected error: {e}") from e


class S3ImageReader(S3ConnectorContextManager):
    def __init__(self, access_key: str, secret_key: str) -> None:
        super().__init__(access_key, secret_key)

    def download_file(self, file_name: str):
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=file_name)
            return StreamingResponse(
                response["Body"],
                media_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="{file_name}"'}
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise MinIOConnectorError(code=404, message=f"File not found: {file_name}") from e
            raise MinIOConnectorError(code=500, message=f"MinIO error: {str(e)}") from e
        except Exception as e:
            raise MinIOConnectorError(code=500, message=f"Unexpected error: {e}") from e

    def upload_file(self, **kwargs):
        raise ConnectorMethodNotAllowed(class_name=self.__class__.__name__)

    def get_image_as_numpy(self, file_name: str) -> np.ndarray:
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=file_name)
            image_bytes = response["Body"].read()

            image_array = np.asarray(bytearray(image_bytes), dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if image is None:
                raise MinIOConnectorError(code=404, message=f"File not found: {file_name}")

            return image

        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise MinIOConnectorError(code=404, message=f"File not found: {file_name}") from e
            raise MinIOConnectorError(code=500, message=f"MinIO error: {str(e)}") from e
        except Exception as e:
            raise MinIOConnectorError(code=500, message=f"Unexpected error: {e}") from e

    def list_images(self) -> list[str]:
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name)
            if "Contents" not in response:
                return []

            image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"}
            image_files = [
                obj["Key"] for obj in response["Contents"]
                if any(obj["Key"].lower().endswith(ext) for ext in image_extensions)
            ]

            return image_files

        except botocore.exceptions.ClientError as e:
            raise MinIOConnectorError(code=500, message=f"MinIO error: {str(e)}") from e
        except Exception as e:
            raise MinIOConnectorError(code=500, message=f"Unexpected error: {e}") from e
