from pathlib import Path
from dataclasses import dataclass


@dataclass
class FileInfo:
    file_path: Path
    class_name: str
