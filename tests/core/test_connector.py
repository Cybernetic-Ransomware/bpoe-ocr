from unittest.mock import MagicMock, patch

import botocore.exceptions
import pytest

from src.api.exceptions import FileBlobHasNoExtension
from src.core.filestorage.abc_connector import S3ConnectorContextManager
from src.core.filestorage.exceptions import MinIOConnectorError
from src.core.filestorage.utils import S3ImageUploader


class _Connector(S3ConnectorContextManager):
    def download_file(self, **kwargs): ...
    def upload_file(self, **kwargs): ...


@pytest.mark.unit
def test_s3_connector_success():
    mock_client = MagicMock()
    mock_client.list_buckets.return_value = {"Buckets": []}
    with patch("boto3.client", return_value=mock_client), _Connector() as connector:
        assert connector.client is not None
        mock_client.list_buckets.assert_called_once()


@pytest.mark.unit
def test_s3_connector_endpoint_connection_error():
    with (
        patch("boto3.client", side_effect=botocore.exceptions.EndpointConnectionError(endpoint_url="http://minio")),
        patch("src.core.filestorage.exceptions.DEBUG", False),
        pytest.raises(MinIOConnectorError) as exc_info,
        _Connector(),
    ):
        pass

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Storage error"


@pytest.mark.unit
def test_s3_connector_client_error():
    mock_client = MagicMock()
    mock_client.list_buckets.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "500", "Message": "Internal Server Error"}}, "ListBuckets"
    )
    with (
        patch("boto3.client", return_value=mock_client),
        patch("src.core.filestorage.exceptions.DEBUG", False),
        pytest.raises(MinIOConnectorError) as exc_info,
        _Connector(),
    ):
        pass

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Storage error"


@pytest.mark.unit
def test_minio_error_5xx_preserves_detail_in_debug():
    with patch("src.core.filestorage.exceptions.DEBUG", True):
        error = MinIOConnectorError(code=500, message="MinIO error: endpoint unreachable")
    assert error.detail == "MinIO error: endpoint unreachable"


@pytest.mark.unit
def test_minio_error_4xx_always_preserves_detail():
    error = MinIOConnectorError(code=404, message="File not found: abc.jpg")
    assert error.detail == "File not found: abc.jpg"


@pytest.mark.unit
@pytest.mark.parametrize(
    "file_name",
    [
        ".gitignore",
        "file.",
        "document.pdf",
        "script.py",
    ],
)
def test_upload_file_rejects_invalid_extension(file_name: str):
    uploader = S3ImageUploader("fake_key", "fake_secret")
    with pytest.raises(FileBlobHasNoExtension):
        uploader.upload_file(MagicMock(), file_name)


@pytest.mark.unit
def test_upload_file_accepts_valid_image_extension():
    uploader = S3ImageUploader("fake_key", "fake_secret")
    mock_client = MagicMock()
    mock_client.head_object.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
    )
    uploader._client = mock_client

    result = uploader.upload_file(MagicMock(), "image.jpg")

    assert result is True


@pytest.mark.unit
def test_s3_connector_exit():
    mock_client = MagicMock()
    mock_client.list_buckets.return_value = {"Buckets": []}
    with patch("boto3.client", return_value=mock_client), _Connector() as connector:
        pass

    assert connector._client is None