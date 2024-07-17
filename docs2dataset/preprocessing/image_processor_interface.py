# File: preprocessing/image_processor_interface.py
from abc import ABC, abstractmethod


class ImageProcessorInterface(ABC):
    @abstractmethod
    def process(self, image):
        pass
