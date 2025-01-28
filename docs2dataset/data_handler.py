# File: data_handler.py
from multiprocessing import Pool
from pathlib import Path
import logging

import pandas as pd

from .utils.logging_utils import setup_logger
from .utils.image_manager import ImageManager
from .utils.file_path_manager import FilePathManager
from .utils.file_info import FileInfo
from .utils.file_utils import create_directory
from .ocr.implementations.pytesseract_ocr import PytesseractOCR
from .utils import save_run_params

class DataHandler:
    def __init__(
            self, input_path: str, output_path: str, max_docs_per_class: int,
            csv_name: str ='data.csv', num_workers=1, dpi=300, save_processed_img=False, target_pages=None, ocr_lang='rus',
            ocr_engine='Tesseract', batch_size_per_worker=10, logging_level='INFO', do_ocr=True,
            smart_shuffle=False, megapixel=3, size_threshold_mb=5, image_processor=None
    ):
        # Setup logging
        self.logging_level = getattr(logging, logging_level.upper(), logging.INFO)
        self.logger = setup_logger('DataHandler', self.logging_level)

        # Main handler args
        self.output_path = create_directory(Path(output_path))
        self.num_workers = num_workers
        self.csv_name = csv_name
        self.do_ocr = do_ocr

        # Ocr Engine and Initialization
        self.ocr_lang = ocr_lang
        self.ocr_engine = PytesseractOCR(ocr_lang) if ocr_engine == 'Tesseract' else ocr_engine

        # FilePathManager args and Initialization
        self.batch_size_per_worker = batch_size_per_worker
        self.max_docs_per_class = max_docs_per_class
        self.smart_shuffle = smart_shuffle
        self.input_path = Path(input_path)
        self.file_path_manager = FilePathManager(
            input_path=self.input_path, max_docs_per_class=self.max_docs_per_class, smart_shuffle=self.smart_shuffle,
            logging_level=self.logging_level, batch_size_per_worker=self.batch_size_per_worker
        )

        # ImageManager args and Initialization
        self.save_processed_img = save_processed_img
        self.size_threshold_mb = size_threshold_mb
        self.target_pages = target_pages
        self.megapixel = megapixel
        self.dpi = dpi
        self.image_manager = ImageManager(
            image_processor=image_processor, save_processed_img=self.save_processed_img, megapixel=self.megapixel,
            output_path=self.output_path / 'image_data', target_pages=self.target_pages, dpi=self.dpi,
            size_threshold_mb=self.size_threshold_mb, logging_level=self.logging_level
        )

    def create_dataset(self):
        results = []
        for file_batch in self.file_path_manager.file_batches():
            if self.num_workers > 1 and self.ocr_engine.engine_name == 'Tesseract':
                with Pool(self.num_workers) as pool:
                    class_results = pool.map(self.process_file, file_batch)
                results.extend(class_results)
            else:
                class_results = [self.process_file(file_info) for file_info in file_batch]
                results.extend(class_results)

        dataset = pd.concat(results, ignore_index=True)
        dataset.to_csv(self.output_path / self.csv_name, index=False)
        save_run_params(self)
        self.logger.info("Dataset creation complete.")
        return dataset

    def process_file(self, file_info: FileInfo):
        ocr_results = []
        for processed_image, image_path, page in self.image_manager.process_image(file_info):
            if self.do_ocr:
                try:
                    self.logger.debug(f"Start extracting text from {page} page of {file_info.file_path}")
                    text = self.ocr_engine.recognize(processed_image, pages=[page])
                    self.logger.debug(f"End extracting text {page} page of {file_info.file_path}")
                except Exception as e:
                    self.logger.error(f"Error occurred while doing OCR on {file_info.file_path}: {e}")
                    text = ''
                ocr_results.append({
                    'SourceFilename': file_info.file_path.name,
                    'Page': page,
                    'Text': text,
                    'Class': file_info.class_name,
                    'PreprocessedFilename': image_path if self.image_manager.save_processed_img else ''
                })
            else:
                ocr_results.append({
                    'SourceFilename': file_info.file_path.name,
                    'Page': page,
                    'Text': '',
                    'Class': file_info.class_name,
                    'PreprocessedFilename': image_path if self.image_manager.save_processed_img else ''
                })
        return pd.DataFrame(ocr_results)
