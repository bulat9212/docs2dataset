# File: utils/file_utils.py
from pathlib import Path


def create_directory(base_path):
    base_path = Path(base_path)
    if not base_path.exists():
        base_path.mkdir(parents=True)
        return base_path

    index = 1
    while True:
        incremented_path = base_path.parent / f"{base_path.name}_{index}"
        if not incremented_path.exists():
            incremented_path.mkdir(parents=True)
            return incremented_path
        index += 1


def is_image_file(file_path):
    return file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif', '.pdf']
