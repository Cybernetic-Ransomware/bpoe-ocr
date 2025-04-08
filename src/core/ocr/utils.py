import numpy as np
import pytesseract
from PIL import Image

from src.conf_logger import setup_logger
from src.config import MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY
from src.core.filestorage.utils import S3ImageReader
from src.core.ocr.exceptions import FileNotFoundInBucket

logger = setup_logger(__name__, "ocr")


class PytesseractReader:
    def __init__(self):
        self.reader = S3ImageReader(MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY)

    @staticmethod
    def rotate_image_pil(image: Image.Image, angle: int) -> Image.Image:
        return image.rotate(-angle, expand=True)

    def ocr_rotated_by_pillow(self, image: Image.Image, file_name: str = "unknown") -> Image.Image:
        try:
            osd_data = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
            rotation_angle = osd_data.get("rotate", 0)
        except Exception as e:
            logger.error(e)
            rotation_angle = 0
        response = self.rotate_image_pil(image, rotation_angle) if rotation_angle else image
        logger.debug(f"Image: {file_name}, of sizes: {image.size} "
                     f"{f'was rotated by {rotation_angle}' if rotation_angle else 'Was not rotated'}")
        return response

    def ocr_file(self, file_name: str) -> dict[str, list]:
        with self.reader as bucket_connector:
            file_blop = bucket_connector.get_image_as_pil(file_name=file_name)
            if not np.any(file_blop):
                raise FileNotFoundInBucket(message=f'File: {file_name}')

        rotated_image = self.ocr_rotated_by_pillow(file_blop, file_name=file_name)
        ocr_text = pytesseract.image_to_data(rotated_image, config=r'--psm 4', output_type=pytesseract.Output.DICT)

        return ocr_text
