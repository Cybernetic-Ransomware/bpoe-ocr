import pytest
from unittest.mock import patch, MagicMock
import botocore.exceptions

from src.core.filestorage.abc_connector import S3ConnectorContextManager
from src.core.filestorage.exceptions import MinIOConnectorError


def test_s3_connector_success():
    with patch("boto3.client") as mock_boto_client, S3ConnectorContextManager() as connector:
        mock_client_instance = MagicMock()
        mock_boto_client.return_value = mock_client_instance
        mock_client_instance.list_buckets.return_value = {"Buckets": []}

        assert connector.client is not None
        mock_client_instance.list_buckets.assert_called_once()

def test_s3_connector_endpoint_connection_error():
    with patch("boto3.client", side_effect=botocore.exceptions.EndpointConnectionError(endpoint_url="http://minio")), \
            pytest.raises(MinIOConnectorError) as exc_info, \
            S3ConnectorContextManager():
        pass

    assert exc_info.value.code == 503
    assert "MinIO is unavailable" in str(exc_info.value)

def test_s3_connector_client_error():
    with patch("boto3.client") as mock_boto_client, \
            pytest.raises(MinIOConnectorError) as exc_info, \
            S3ConnectorContextManager():
        mock_client_instance = MagicMock()
        mock_boto_client.return_value = mock_client_instance

        mock_client_instance.list_buckets.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "500", "Message": "Internal Server Error"}}, "ListBuckets"
        )

    assert exc_info.value.code == 500
    assert "MinIO error" in str(exc_info.value)

def test_s3_connector_exit():
    with patch("boto3.client") as mock_boto_client:
        mock_client_instance = MagicMock()
        mock_boto_client.return_value = mock_client_instance
        mock_client_instance.list_buckets.return_value = {"Buckets": []}

        with S3ConnectorContextManager() as connector:
            pass

        assert connector.client is None
