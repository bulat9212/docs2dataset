import abc
from typing import Dict, Callable

import numpy as np


class ImageProcessorInterface(abc.ABC):

    _REGISTRY: Dict[str, Callable] = {}

    def __init_subclass__(cls, /, instance_name: str, **kwargs):
        super().__init_subclass__(**kwargs)
        if instance_name in cls._REGISTRY:
            raise ValueError(f'Subclass with {instance_name=} already exists in registry.')
        cls._REGISTRY[instance_name] = cls

    @classmethod
    def create_instance(cls, instance_name: str, params: dict = None):
        if instance_name not in cls._REGISTRY:
            raise ValueError(f'There is no subclass with {instance_name=} in registry.')
        return cls._REGISTRY[instance_name]() if params is None else cls._REGISTRY[instance_name](**params)

    @abc.abstractmethod
    def process(self, image: np.ndarray) -> np.ndarray:
        raise NotImplementedError('Method should be implemented in child class!')
