# File: data_handler.py
from multiprocessing import Pool
from pathlib import Path
import logging

import pandas as pd

from .utils.logging_utils import setup_logger
from .utils.image_manager import ImageManager
from .utils.file_path_manager import FilePathManager
from .utils.file_info import FileInfo
from .ocr.implementations.pytesseract_ocr import PytesseractOCR


# todo
# write bad images to separate log file of file csv
# add datailed info about image size to the final csv
# adjust logging for multiprocessing, create log file, check that log was setuped once,add more log messages,debug logs
# typehints, refactor
# revise project structure
# add timings logging, log mean img processing time
# add requirements
# add tesseract htop importance parameter
# properly filter 0 confidence tokens
# avoid .dirs
# add tests
# handle also -2 -3 pages not only -1
# angle align multiprocessing issue
# refactor smart_shuffle
# save used data handler config file to the output dir
# add proper handling of DecompositionBombWarning


class DataHandler:
    def __init__(
            self, input_path, output_path, max_docs_per_class,
            csv_name='data.csv', num_workers=1, dpi=300, save_processed_img=False, target_pages=None, ocr_lang='rus',
            ocr_engine='Tesseract', batch_size_per_worker=10, logging_level='INFO', do_ocr=True,
            smart_shuffle=False, megapixel=3, size_threshold_mb=5, image_processor=None
    ):
        self.logging_level = getattr(logging, logging_level.upper(), logging.INFO)
        self.output_path = Path(output_path)
        self.batch_size_per_worker = batch_size_per_worker
        self.num_workers = num_workers
        self.dpi = dpi
        self.csv_name = csv_name
        self.ocr_engine = PytesseractOCR(ocr_lang) if ocr_engine == 'Tesseract' else None
        self.logger = setup_logger('DataHandler', self.logging_level)
        self.do_ocr = do_ocr
        self.file_path_manager = FilePathManager(
            input_path=input_path, max_docs_per_class=max_docs_per_class, batch_size_per_worker=batch_size_per_worker,
            smart_shuffle=smart_shuffle, logging_level=self.logging_level
        )
        self.image_manager = ImageManager(
            image_processor=image_processor,save_processed_img=save_processed_img,
            output_path=self.output_path / 'image_data', target_pages=target_pages, megapixel=megapixel,
            size_threshold_mb=size_threshold_mb, logging_level=self.logging_level, dpi=dpi
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
        self.logger.info("Dataset creation complete.")
        return dataset

    def process_file(self, file_info: FileInfo):
        ocr_results = []
        for processed_image, image_path, page in self.image_manager.process_image(file_info):
            if self.do_ocr:
                try:
                    self.logger.debug(f"Start extracting text from {page} page of {file_info.file_path}")
                    text = self.ocr_engine.extract_text(processed_image, pages=[page])
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
