from unittest.mock import MagicMock, patch

import botocore.exceptions
import pytest

from src.core.filestorage.abc_connector import S3ConnectorContextManager
from src.core.filestorage.exceptions import MinIOConnectorError


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
        pytest.raises(MinIOConnectorError) as exc_info,
        _Connector(),
    ):
        pass

    assert exc_info.value.status_code == 503
    assert "MinIO is unavailable" in exc_info.value.detail


@pytest.mark.unit
def test_s3_connector_client_error():
    mock_client = MagicMock()
    mock_client.list_buckets.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "500", "Message": "Internal Server Error"}}, "ListBuckets"
    )
    with (
        patch("boto3.client", return_value=mock_client),
        pytest.raises(MinIOConnectorError) as exc_info,
        _Connector(),
    ):
        pass

    assert exc_info.value.status_code == 500
    assert "MinIO error" in exc_info.value.detail


@pytest.mark.unit
def test_s3_connector_exit():
    mock_client = MagicMock()
    mock_client.list_buckets.return_value = {"Buckets": []}
    with patch("boto3.client", return_value=mock_client), _Connector() as connector:
        pass

    assert connector.client is None