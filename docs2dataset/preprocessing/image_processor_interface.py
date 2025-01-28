from abc import ABC, abstractmethod


class ImageProcessorInterface(ABC):
    @abstractmethod
    def process(self, image):
        pass
