from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from src.core.filestorage.exceptions import MinIOConnectorError
from src.core.ocr.utils import PytesseractReader


def _mock_reader(image=None, error=None):
    reader = MagicMock()
    reader.__enter__ = MagicMock(return_value=reader)
    reader.__exit__ = MagicMock(return_value=False)
    if error:
        reader.get_image_as_pil = MagicMock(side_effect=error)
    else:
        reader.get_image_as_pil = MagicMock(return_value=image)
    return reader


@pytest.mark.unit
def test_ocr_file_returns_dict():
    fake_image = Image.new("RGB", (100, 100))
    mock_reader = _mock_reader(image=fake_image)

    with (
        patch("src.core.ocr.utils.S3ImageReader", return_value=mock_reader),
        patch("src.core.ocr.utils.pytesseract.image_to_osd", return_value={"rotate": 0}),
        patch("src.core.ocr.utils.pytesseract.image_to_data", return_value={"text": ["Hello", "World"]}),
    ):
        result = PytesseractReader().ocr_file("test.jpg")

    assert result == {"text": ["Hello", "World"]}


@pytest.mark.unit
def test_ocr_file_propagates_storage_error():
    mock_reader = _mock_reader(error=MinIOConnectorError(code=404, message="File not found"))

    with (
        patch("src.core.ocr.utils.S3ImageReader", return_value=mock_reader),
        pytest.raises(MinIOConnectorError) as exc_info,
    ):
        PytesseractReader().ocr_file("missing.jpg")

    assert exc_info.value.status_code == 404