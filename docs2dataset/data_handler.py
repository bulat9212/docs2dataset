# File: data_handler.py
import pandas as pd
from multiprocessing import Pool
from .utils.logging_utils import setup_logger
from .utils.image_manager import ImageManager
from .utils.file_path_manager import FilePathManager
from .utils.file_info import FileInfo
from pathlib import Path

# todo
# write bad images to separate log file of file csv
# add datailed info about image size to the final csv
# adjust logging for multiprocessing, create log file, check that log was setuped once,add more log messages,debug logs
# typehints, refactor
# revise project structure
# add params by default
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
    def __init__(self, input_path, output_path, max_docs_per_class, batch_size_per_worker, num_workers, dpi,
                 save_processed_img, csv_name, target_pages, ocr_lang,
                 image_processor, ocr_engine, logging_level='INFO', do_ocr=True, smart_shuffle=False, megapixel=3, size_threshold_mb=5):
        self.output_path = Path(output_path)
        self.batch_size_per_worker = batch_size_per_worker
        self.num_workers = num_workers
        self.dpi = dpi
        self.csv_name = csv_name
        self.target_pages = target_pages
        self.ocr_lang = ocr_lang
        self.ocr_engine = ocr_engine
        self.logger = setup_logger('DataHandler', logging_level)
        self.do_ocr = do_ocr
        self.file_path_manager = FilePathManager(input_path, max_docs_per_class, batch_size_per_worker, smart_shuffle=smart_shuffle)
        self.image_manager = ImageManager(image_processor=image_processor,
                                          save_processed_img=save_processed_img, output_path=self.output_path / 'image_data',
                                          target_pages=self.target_pages, megapixel=megapixel, size_threshold_mb=size_threshold_mb)

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
                    self.logger.info(f"Start extracting text from {image_path}")
                    text = self.ocr_engine.extract_text(processed_image, pages=[page])
                    self.logger.debug(f"End extracting text from {image_path}")
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
