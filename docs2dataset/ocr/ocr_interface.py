# File: ocr/ocr_interface.py
from abc import ABC, abstractmethod


class OCRAbstract(ABC):
    @abstractmethod
    def recognize(self, image, pages=None):
        pass

    @property
    @abstractmethod
    def engine_name(self):
        pass
