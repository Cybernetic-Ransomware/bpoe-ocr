from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymongo.errors import ServerSelectionTimeoutError

from src.core.documentstorage.exceptions import MongoDBConnectorError
from src.core.documentstorage.utils import MongoConnectorBuilder, MongoConnectorRunner


def _mock_client():
    client = AsyncMock()
    client.server_info = AsyncMock(return_value={"version": "7.0"})
    client.close = AsyncMock()
    client.__getitem__ = MagicMock(return_value=AsyncMock())
    return client


@pytest.mark.unit
async def test_runner_enters_and_exits():
    mock_client = _mock_client()
    with (
        patch("src.core.documentstorage.utils.AsyncMongoClient", return_value=mock_client),
        patch("src.core.documentstorage.utils.DEBUG", True),
    ):
        async with MongoConnectorRunner() as runner:
            assert runner.client is not None
        assert runner.client is None
        mock_client.close.assert_called_once()


@pytest.mark.unit
async def test_runner_closes_on_exception_inside_block():
    mock_client = _mock_client()
    with (
        patch("src.core.documentstorage.utils.AsyncMongoClient", return_value=mock_client),
        patch("src.core.documentstorage.utils.DEBUG", True),
        pytest.raises(ValueError),
    ):
        async with MongoConnectorRunner():
            raise ValueError("simulated error")

    mock_client.close.assert_called_once()


@pytest.mark.unit
async def test_runner_connection_error():
    mock_client = AsyncMock()
    mock_client.server_info = AsyncMock(side_effect=ServerSelectionTimeoutError("timeout"))
    mock_client.close = AsyncMock()
    mock_client.__getitem__ = MagicMock(return_value=AsyncMock())

    with (
        patch("src.core.documentstorage.utils.AsyncMongoClient", return_value=mock_client),
        pytest.raises(MongoDBConnectorError) as exc_info,
    ):
        async with MongoConnectorRunner():
            pass

    assert exc_info.value.status_code == 503


@pytest.mark.unit
async def test_upload_ocr_result_success():
    mock_insert_result = MagicMock(inserted_id="abc123")
    mock_collection = AsyncMock()
    mock_collection.insert_one = AsyncMock(return_value=mock_insert_result)

    mock_database = MagicMock()
    mock_database.__getitem__ = MagicMock(return_value=mock_collection)

    mock_client = AsyncMock()
    mock_client.server_info = AsyncMock(return_value={})
    mock_client.__getitem__ = MagicMock(return_value=mock_database)
    mock_client.close = AsyncMock()

    with (
        patch("src.core.documentstorage.utils.AsyncMongoClient", return_value=mock_client),
        patch("src.core.documentstorage.utils.DEBUG", True),
    ):
        async with MongoConnectorRunner() as runner:
            result = await runner.upload_ocr_result("file.jpg", ["Hello", "World"], "user@example.com")

    assert result == "abc123"


@pytest.mark.unit
async def test_initialize_creates_collection_when_missing():
    mock_database = AsyncMock()
    mock_database.list_collection_names = AsyncMock(return_value=[])
    mock_database.create_collection = AsyncMock()

    mock_client = AsyncMock()
    mock_client.server_info = AsyncMock(return_value={})
    mock_client.close = AsyncMock()
    mock_client.__getitem__ = MagicMock(return_value=mock_database)

    with (
        patch("src.core.documentstorage.utils.AsyncMongoClient", return_value=mock_client),
        patch.object(MongoConnectorBuilder, "enable_sharding", new=AsyncMock()),
    ):
        await MongoConnectorBuilder(mongo_db="existing_db", mongo_collection="new_col").initialize()

    mock_database.create_collection.assert_called_once()
    _, kwargs = mock_database.create_collection.call_args
    assert "validator" in kwargs


@pytest.mark.unit
async def test_initialize_skips_creation_when_collection_exists():
    mock_database = AsyncMock()
    mock_database.list_collection_names = AsyncMock(return_value=["existing_col"])
    mock_database.create_collection = AsyncMock()

    mock_client = AsyncMock()
    mock_client.server_info = AsyncMock(return_value={})
    mock_client.close = AsyncMock()
    mock_client.__getitem__ = MagicMock(return_value=mock_database)

    with (
        patch("src.core.documentstorage.utils.AsyncMongoClient", return_value=mock_client),
        patch.object(MongoConnectorBuilder, "enable_sharding", new=AsyncMock()),
    ):
        await MongoConnectorBuilder(mongo_db="existing_db", mongo_collection="existing_col").initialize()

    mock_database.create_collection.assert_not_called()


@pytest.mark.unit
async def test_ensure_non_admin_user_raises_when_no_users():
    mock_database = AsyncMock()
    mock_database.command = AsyncMock(return_value={"users": []})

    mock_client = _mock_client()
    with patch("src.core.documentstorage.utils.AsyncMongoClient", return_value=mock_client):
        async with MongoConnectorRunner() as runner:
            runner.database = mock_database
            with pytest.raises(MongoDBConnectorError) as exc_info:
                await runner.ensure_non_admin_user()

    assert "No users found" in exc_info.value.detail


@pytest.mark.unit
async def test_ensure_non_admin_user_raises_with_forbidden_role():
    mock_database = AsyncMock()
    mock_database.command = AsyncMock(
        return_value={"users": [{"roles": [{"role": "dbAdmin", "db": "ocr"}]}]}
    )

    mock_client = _mock_client()
    with patch("src.core.documentstorage.utils.AsyncMongoClient", return_value=mock_client):
        async with MongoConnectorRunner() as runner:
            runner.database = mock_database
            with pytest.raises(MongoDBConnectorError) as exc_info:
                await runner.ensure_non_admin_user()

    assert "dbAdmin" in exc_info.value.detail


@pytest.mark.unit
async def test_ensure_non_admin_user_passes_with_allowed_role():
    mock_database = AsyncMock()
    mock_database.command = AsyncMock(
        return_value={"users": [{"roles": [{"role": "readWrite", "db": "ocr"}]}]}
    )

    mock_client = _mock_client()
    with patch("src.core.documentstorage.utils.AsyncMongoClient", return_value=mock_client):
        async with MongoConnectorRunner() as runner:
            runner.database = mock_database
            await runner.ensure_non_admin_user()


@pytest.mark.unit
async def test_upload_ocr_result_not_initialized():
    mock_client = _mock_client()
    with (
        patch("src.core.documentstorage.utils.AsyncMongoClient", return_value=mock_client),
        patch("src.core.documentstorage.utils.DEBUG", True),
    ):
        async with MongoConnectorRunner() as runner:
            runner.database = None
            with pytest.raises(MongoDBConnectorError):
                await runner.upload_ocr_result("file.jpg", ["text"], "user@example.com")
