from typing import List

import numpy as np

from .image_processor_interface import ImageProcessorInterface


class ImageProcessingPipeline:
    def __init__(self, processors: List[ImageProcessorInterface]):
        self._processors = processors

    @classmethod
    def from_config(cls, config: List[dict]) -> 'ImageProcessingPipeline':

        processors: List[ImageProcessorInterface] = [
            ImageProcessorInterface.create_instance(
                instance_name=processor['instance_name'],
                params=processor['params']
            )
            for processor in config
        ]

        return cls(processors=processors)

    def run(self, image: np.ndarray) -> np.ndarray:
        for processor in self._processors:
            image = processor.process(image=image)
        return image
