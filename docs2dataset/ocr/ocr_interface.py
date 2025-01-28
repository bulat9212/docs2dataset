from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, List

import numpy as np


@dataclass
class Box:
    x1: int  # Left
    y1: int  # Top
    x2: int  # Right
    y2: int  # Bottom


@dataclass
class TxtItem:
    bbox: Box
    text: str
    confidence: float  # MUST be in range 0...100


@dataclass
class OCROutput:
    text_items: List[TxtItem]


class OCRInterface(ABC):
    @abstractmethod
    def recognize(self, images: Iterable[np.ndarray]) -> List[OCROutput]:
        pass
