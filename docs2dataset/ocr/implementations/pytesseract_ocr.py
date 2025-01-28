import pytesseract
import numpy as np

from docs2dataset.ocr.ocr_interface import OCRInterface


class PytesseractOCR(OCRInterface):
    """
    Pytesseract-based implementation of OCRInterface.
    """

    def __init__(self, lang: str = "rus"):
        """
        Args:
            lang (str): Language parameter for Tesseract.
        """
        self._lang = lang

    def recognize(self, image: np.ndarray) -> str:
        """
        Perform OCR using pytesseract on a single image.
        """
        ocr_data = pytesseract.image_to_data(
            image,
            lang=self._lang,
            output_type=pytesseract.Output.DICT,
            timeout=30
        )

        words = []
        for i, text_val in enumerate(ocr_data["text"]):
            conf = float(ocr_data["conf"][i])
            if conf > 0 and text_val.strip():
                words.append(text_val.strip())

        return " ".join(words)

    @property
    def engine_name(self) -> str:
        """Name of the OCR engine."""
        return "Tesseract"
