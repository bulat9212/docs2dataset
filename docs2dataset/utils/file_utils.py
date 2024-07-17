# File: utils/file_utils.py
from pathlib import Path


def is_image_file(file_path):
    return file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif', '.pdf']
