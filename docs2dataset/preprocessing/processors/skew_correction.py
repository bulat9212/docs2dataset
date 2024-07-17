# File: preprocessing/processors/skew_correction.py
from ..image_processor_interface import ImageProcessorInterface


class SkewCorrection(ImageProcessorInterface):
    def __init__(self, params=None):
        self.params = params if params is not None else {}

    def process(self, image):
        return image
