# File: setup.py
from setuptools import setup, find_packages

setup(
    name='docs2dataset',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'pillow',
        'pytesseract',
        'PyMuPDF',
        'numpy',
        'setuptools==70.0.0',
        'opencv-python',
        'pandas'
    ],
)