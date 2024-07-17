# File: docs2dataset/preprocessing/processors/angle_align.py
from docs2dataset.preprocessing.image_processor_interface import ImageProcessorInterface


class AngleAlign(ImageProcessorInterface):
    def __init__(self, params=None):
        self.params = params if params is not None else {}

    def process(self, image):
        return image
