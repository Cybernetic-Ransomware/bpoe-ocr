import botocore.exceptions
from fastapi.responses import StreamingResponse
from typing import BinaryIO

from src.filestorage.connector import S3ConnectorContextManager
from src.filestorage.exceptions import MinIOConnectorError


class S3ImageUploader(S3ConnectorContextManager):
    def __init__(self, access_key: str, secret_key: str):
        super().__init__(access_key, secret_key)

    def upload_file(self, file_obj: BinaryIO, file_name: str):
        try:
            self.client.upload_fileobj(file_obj, self.bucket_name, file_name)
            return True
        except botocore.exceptions.ClientError as e:
            raise MinIOConnectorError(code=500, message=f"Cannot upload file: {e}")
        except Exception as e:
            raise MinIOConnectorError(code=500, message=f"Unexpected error: {e}")


class S3ImageReader(S3ConnectorContextManager):
    def __init__(self, access_key: str, secret_key: str):
        super().__init__(access_key, secret_key)

    def download_file(self, file_name: str):
        try:
            response = self.client.get_object(self.bucket_name, file_name)
            return StreamingResponse(
                response["Body"],
                media_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="{file_name}"'}
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise MinIOConnectorError(code=404, message=f"File not found: {file_name}")
            raise MinIOConnectorError(code=500, message=f"MinIO error: {str(e)}")
        except Exception as e:
            raise MinIOConnectorError(code=500, message=f"Unexpected error: {e}")
