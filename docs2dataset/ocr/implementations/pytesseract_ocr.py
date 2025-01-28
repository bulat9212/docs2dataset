from typing import Iterable

import numpy as np
import pytesseract

from ..ocr_interface import OCRInterface


class PytesseractOCR(OCRInterface):
    def __init__(self, lang: str ='rus'):
        self.lang = lang

    def recognize(self, image: Iterable[np.ndarray]) -> Iterable[str]:
        ocr_data = pytesseract.image_to_data(
            image,
            lang=self.lang,
            output_type=pytesseract.Output.DICT,
            timeout=30
        )

        text_items = []
        fields = ['left', 'top', 'width', 'height', 'text', 'conf']
        for x, y, w, h, text, confidence in zip(*[ocr_data[field] for field in fields]):
            confidence = float(confidence)
            if confidence < 0:
                continue
            if text.strip() != '':
                text_items.append(text)

        return " ".join(text_items)

    @property
    def engine_name(self):
        return 'Tesseract'
