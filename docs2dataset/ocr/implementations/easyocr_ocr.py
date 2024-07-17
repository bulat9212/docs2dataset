# # File: ocr/implementations/easyocr_ocr.py
# import easyocr
# from ..ocr_interface import OCRAbstract
#
# class EasyOCROCR(OCRAbstract):
#     def __init__(self, lang=['ru']):
#         self.reader = easyocr.Reader(lang)
#
#     def extract_text(self, image, pages=None):
#         result = self.reader.readtext(image)
#         return ' '.join([res[1] for res in result if res[2] > 0.1])
#
#     @property
#     def engine_name(self):
#         return 'EasyOCR'
