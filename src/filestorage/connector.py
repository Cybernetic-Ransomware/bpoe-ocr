import boto3
import botocore.exceptions

from src.config import MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_ENDPOINT, MINIO_BUCKET_NAME
from src.filestorage.exceptions import MinIOConnectorError


class S3ConnectorContextManager:
    def __init__(self, access_key: str = MINIO_ACCESS_KEY, secret_key: str = MINIO_SECRET_KEY):
        self.endpoint_url  = MINIO_ENDPOINT
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = MINIO_BUCKET_NAME

    def __enter__(self):
        try:
            self.client = boto3.client(
                "s3",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint_url,
            )
            self.client.list_buckets()  # to check exceptions
            return self

        except botocore.exceptions.EndpointConnectionError:
            raise MinIOConnectorError(code=503, message="MinIO is unavailable")

        except botocore.exceptions.ClientError as e:
            raise MinIOConnectorError(code=500, message=f"MinIO error: {str(e)}")

    def __exit__(self, exc_type, exc_value, traceback):
        self.client = None
