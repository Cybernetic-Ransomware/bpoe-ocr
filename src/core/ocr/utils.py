import cv2
import numpy as np
import pytesseract

from scipy import ndimage

from src.config import MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY
from src.core.filestorage.utils import S3ImageReader


class OCRReader:
    def __init__(self):
        self.reader = S3ImageReader(MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY)
        self.files_queue = []

    def read_queue_in_bucket(self) -> None:
        list_of_files = self.reader.list_images()

        if not list_of_files:
            return None

        for file in list_of_files:
            if file not in self.files_queue:
                self.files_queue.append(file)


    @staticmethod
    def rotate_image_cv2(image: np.ndarray, angle: float) -> np.ndarray:
        (h, w) = image.shape[:2]
        center = (w/2, h/2)

        rotation_matrix = cv2.getRotationMatrix2D(center, -angle, 1.0)
        rotated_image = cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

        return rotated_image

    @staticmethod
    def rotate_image_scipy(image: np.ndarray, angle: float) -> np.ndarray:
        rotated_image = ndimage.rotate(image, angle=angle, reshape=False)

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
