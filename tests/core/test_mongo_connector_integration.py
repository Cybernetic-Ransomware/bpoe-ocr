from unittest.mock import AsyncMock, patch

import pytest

from src.core.documentstorage.utils import MongoConnectorBuilder, MongoConnectorRunner


@pytest.mark.integration
async def test_runner_connects_and_disconnects(mongo_connection_url: str):
    with patch("src.core.documentstorage.utils.DEBUG", True):
        async with MongoConnectorRunner(
            mongo_uri=mongo_connection_url, mongo_db="test_db", mongo_collection="test_ocr"
        ) as runner:
            assert runner.client is not None
            assert runner.database is not None
    assert runner.client is None


@pytest.mark.integration
async def test_upload_ocr_result_persists(mongo_connection_url: str):
    with patch("src.core.documentstorage.utils.DEBUG", True):
        async with MongoConnectorRunner(
            mongo_uri=mongo_connection_url, mongo_db="test_db", mongo_collection="test_ocr"
        ) as runner:
            inserted_id = await runner.upload_ocr_result("photo.jpg", ["line one", "line two"], "user@example.com")

    assert isinstance(inserted_id, str)
    assert len(inserted_id) > 0


@pytest.mark.integration
async def test_builder_creates_collection(mongo_connection_url: str):
    with patch.object(MongoConnectorBuilder, "enable_sharding", new=AsyncMock()):
        builder = MongoConnectorBuilder(
            mongo_uri=mongo_connection_url,
            mongo_db="test_builder_db",
            mongo_collection="test_ocr",
        )
        # Should not raise — collection is created with schema validation
        await builder.initialize()
