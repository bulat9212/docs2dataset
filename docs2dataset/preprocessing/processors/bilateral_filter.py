# File: preprocessing/processors/bilateral_filter.py
from ..image_processor_interface import ImageProcessorInterface


class BilateralFilter(ImageProcessorInterface):
    def __init__(self, params=None):
        self.params = params if params is not None else {}

    def process(self, image):
        return image
