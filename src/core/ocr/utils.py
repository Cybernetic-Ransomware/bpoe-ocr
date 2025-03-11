import cv2
import numpy as np
import pytesseract

from scipy import ndimage

from src.config import MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY
from src.core.filestorage.utils import S3ImageReader
from src.core.ocr.exceptions import FileNotFoundInBucket


class PytesseractReader:
    def __init__(self):
        self.reader = S3ImageReader(MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY)

    @staticmethod
    def rotate_image_cv2(image: np.ndarray, angle: float) -> np.ndarray:
        (h, w) = image.shape[:2]
        center = (w/2, h/2)

        rotation_matrix = cv2.getRotationMatrix2D(center, -angle, 1.0)
        rotated_image = cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

        return rotated_image

    @staticmethod
    def rotate_image_scipy(image: np.ndarray, angle: float) -> np.ndarray:
        rotated_image = ndimage.rotate(image, angle=angle, reshape=True)

        return rotated_image


    def ocr_rotated_by_cv2(self, image) -> dict[str, list]:
        osd_data = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
        rotation_angle = osd_data.get("rotate", 0)

        image_rotated = image
        if rotation_angle:
            image_rotated = self.rotate_image_cv2(image, rotation_angle) if rotation_angle else image

        result = pytesseract.image_to_data(image_rotated, config=r'--psm 4', output_type=pytesseract.Output.DICT)
        return result

    def ocr_rotated_by_scipy(self, image) -> dict[str, list]:
        osd_data = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
        rotation_angle = osd_data.get("rotate", 0)

        image_rotated = image
        if rotation_angle:
            image_rotated = self.rotate_image_scipy(image, rotation_angle) if rotation_angle else image

        result = pytesseract.image_to_data(image_rotated, config=r'--psm 4', output_type=pytesseract.Output.DICT)
        return result

    def ocr_file(self, file_name: str) -> dict[str, list]:
        with self.reader as bucket_connector:
            if file_name not in bucket_connector:
                raise FileNotFoundInBucket(message=f'File: {file_name}')
            file_blop = bucket_connector.get_image_as_numpy(file_name=file_name)

        ocr_text = dict()
        if file_blop:
            ocr_text = self.ocr_rotated_by_cv2(file_blop)

        return ocr_text

