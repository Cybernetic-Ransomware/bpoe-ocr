from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app

BASE_URL = "http://test"


@pytest.mark.unit
async def test_root_healthcheck():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


@pytest.mark.unit
async def test_upload_file_success():
    mock_uploader = MagicMock()
    mock_uploader.__enter__ = MagicMock(return_value=mock_uploader)
    mock_uploader.__exit__ = MagicMock(return_value=False)
    mock_uploader.upload_file = MagicMock(return_value=True)

    with patch("src.api.routers.S3ImageUploader", return_value=mock_uploader):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.post(
                "/api/upload/test_file.jpg",
                files={"file": ("test.jpg", b"fake image data", "image/jpeg")},
            )

    assert response.status_code == 200
    assert response.json()["message"] == "File 'test_file.jpg' uploaded successfully"


@pytest.mark.unit
async def test_upload_file_transfer_interrupted():
    mock_uploader = MagicMock()
    mock_uploader.__enter__ = MagicMock(return_value=mock_uploader)
    mock_uploader.__exit__ = MagicMock(return_value=False)
    mock_uploader.upload_file = MagicMock(return_value=False)

    with patch("src.api.routers.S3ImageUploader", return_value=mock_uploader):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.post(
                "/api/upload/test_file.jpg",
                files={"file": ("test.jpg", b"fake image data", "image/jpeg")},
            )

    assert response.status_code == 500
    body = response.json()
    assert body["status_code"] == 500
    assert body["error"] == "FileTransferInterrupted"


@pytest.mark.unit
async def test_download_not_allowed_in_production():
    with patch("src.api.routers.DEBUG", False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get("/api/download/some_file.jpg")

    assert response.status_code == 403
    body = response.json()
    assert body["error"] == "EndpointNotAllowed"


@pytest.mark.unit
async def test_http_exception_handler_5xx_sanitizes_detail_in_production():
    mock_uploader = MagicMock()
    mock_uploader.__enter__ = MagicMock(return_value=mock_uploader)
    mock_uploader.__exit__ = MagicMock(return_value=False)
    mock_uploader.upload_file = MagicMock(return_value=False)

    with (
        patch("src.api.routers.S3ImageUploader", return_value=mock_uploader),
        patch("src.main.DEBUG", False),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.post(
                "/api/upload/test_file.jpg",
                files={"file": ("test.jpg", b"fake image data", "image/jpeg")},
            )

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


@pytest.mark.unit
async def test_http_exception_handler_4xx_preserves_detail():
    with patch("src.api.routers.DEBUG", False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get("/api/download/some_file.jpg")

    assert response.status_code == 403
    assert "not allowed" in response.json()["detail"]


@pytest.mark.unit
async def test_process_ocr_unsupported_engine():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.post(
            "/api/process_ocr/",
            params={"file_name": "test.jpg", "ocr_engine": "unknown_engine"},
            json={"user_email": "user@example.com"},
        )

    assert response.status_code == 404
    assert "Unsupported OCR engine" in response.json()["detail"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "file_name",
    [
        "file name.jpg",
        "file!@#.jpg",
        "a" * 256,
    ],
)
async def test_upload_rejects_invalid_file_name(file_name: str):
    # Path traversal cases (../, /absolute) are normalized by the HTTP layer before reaching FastAPI.
    # Null bytes are rejected by httpx itself. Those vectors are covered via query-param tests below.
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.post(
            f"/api/upload/{file_name}",
            files={"file": ("test.jpg", b"fake image data", "image/jpeg")},
        )
    assert response.status_code == 422


@pytest.mark.unit
@pytest.mark.parametrize(
    "file_name",
    [
        "../etc/passwd",
        "/absolute/path.jpg",
        "file name.jpg",
        "a" * 256,
    ],
)
async def test_process_ocr_rejects_invalid_file_name(file_name: str):
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.post(
            "/api/process_ocr/",
            params={"file_name": file_name},
            json={"user_email": "user@example.com"},
        )
    assert response.status_code == 422


@pytest.mark.unit
async def test_process_ocr_success():
    mock_engine = MagicMock()
    mock_engine.ocr_file = MagicMock(return_value={"text": ["Hello", "World"]})

    mock_runner = AsyncMock()
    mock_runner.__aenter__ = AsyncMock(return_value=mock_runner)
    mock_runner.upload_ocr_result = AsyncMock(return_value="inserted-id")

    mock_delete = MagicMock()

    with (
        patch.dict("src.api.routers.ocr_engines", {"pytesseract": mock_engine}),
        patch("src.api.routers.MongoConnectorRunner", return_value=mock_runner),
        patch("src.api.routers.delete_file", mock_delete),
        patch("src.api.routers.asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
    ):
        mock_to_thread.side_effect = [{"text": ["Hello", "World"]}, None]
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.post(
                "/api/process_ocr/",
                params={"file_name": "test.jpg"},
                json={"user_email": "user@example.com"},
            )

    assert response.status_code == 200
    assert response.json() == {"test.jpg": ["Hello", "World"]}
    mock_runner.upload_ocr_result.assert_called_once_with("test.jpg", ["Hello", "World"], "user@example.com")
    mock_to_thread.assert_any_await(mock_engine.ocr_file, "test.jpg")
    mock_to_thread.assert_any_await(mock_delete, "test.jpg")


@pytest.mark.unit
async def test_process_ocr_returns_success_when_delete_fails():
    mock_engine = MagicMock()

    mock_runner = AsyncMock()
    mock_runner.__aenter__ = AsyncMock(return_value=mock_runner)
    mock_runner.upload_ocr_result = AsyncMock(return_value="inserted-id")

    with (
        patch.dict("src.api.routers.ocr_engines", {"pytesseract": mock_engine}),
        patch("src.api.routers.MongoConnectorRunner", return_value=mock_runner),
        patch("src.api.routers.asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
    ):
        mock_to_thread.side_effect = [{"text": ["extracted"]}, Exception("S3 delete failed")]
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.post(
                "/api/process_ocr/",
                params={"file_name": "test.jpg"},
                json={"user_email": "user@example.com"},
            )

    assert response.status_code == 200
    assert response.json() == {"test.jpg": ["extracted"]}
