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
        'setuptools',
        'opencv-python',
        'pandas'
    ],
)