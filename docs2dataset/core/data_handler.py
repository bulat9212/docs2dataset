import logging
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

from docs2dataset.data_managers.image_manager import ImageManager
from docs2dataset.data_managers.file_path_manager import FilePathManager
from docs2dataset.ocr.implementations.pytesseract_ocr import PytesseractOCR
from docs2dataset.utils.file_info import FileInfo
from docs2dataset.utils.file_utils import create_directory
from docs2dataset.utils.logging_utils import setup_logger
from docs2dataset.utils.params_utils import save_run_params


class DataHandler:
    """
    Orchestrates the creation of a dataset by:
    1. Gathering file paths (pdf/images).
    2. Processing images and performing OCR.
    3. Saving results to a CSV file.

    Attributes:
        input_path (Path): Path to the root input directory containing class-subdirectories.
        output_path (Path): Path where all processed data and CSV are saved.
        max_docs_per_class (int): Maximum number of documents per class.
        csv_name (str): Name of the CSV file to be created.
        num_workers (int): Number of parallel processes for OCR.
        dpi (int): Resolution for rendering PDF pages.
        save_processed_img (bool): Whether to save processed images.
        target_pages (list[int]): Which pages to extract from multi-page documents. If None, extract all.
        ocr_lang (str): Language for OCR.
        ocr_engine (str or OCRInterface): The OCR engine. Defaults to "Tesseract".
        batch_size_per_worker (int): Number of documents each worker processes at a time.
        logging_level (str): Logging level ("INFO", "DEBUG", etc.).
        do_ocr (bool): Whether to perform OCR or skip it.
        smart_shuffle (bool): If True, distribute documents from subdirectories evenly.
        megapixel (int): Maximum resolution in megapixels to which images are scaled down if they exceed it.
        size_threshold_mb (int): Maximum file size in MB for saved images. If exceeded, compression is applied.
        image_processor (ImageProcessorInterface): Custom image preprocessing pipeline.
    """

    def __init__(
            self,
            input_path: str,
            output_path: str,
            max_docs_per_class: int,
            csv_name: str = "data.csv",
            num_workers: int = 1,
            dpi: int = 300,
            save_processed_img: bool = False,
            target_pages: list[int] | None = None,
            ocr_lang: str = "rus",
            ocr_engine: str = "Tesseract",
            batch_size_per_worker: int = 10,
            logging_level: str = "INFO",
            do_ocr: bool = True,
            smart_shuffle: bool = False,
            megapixel: int = 3,
            size_threshold_mb: int = 5,
            image_processor=None
    ):
        # Setup logging
        self.logging_level = getattr(logging, logging_level.upper(), logging.INFO)
        self.logger = setup_logger("DataHandler", self.logging_level)

        # Main handler args
        self.input_path = Path(input_path)
        self.output_path = create_directory(Path(output_path))
        self.max_docs_per_class = max_docs_per_class
        self.csv_name = csv_name
        self.num_workers = num_workers
        self.do_ocr = do_ocr

        # OCR engine setup
        self.ocr_lang = ocr_lang
        if ocr_engine == "Tesseract":
            self.ocr_engine = PytesseractOCR(ocr_lang)
        else:
            # Assume an OCRInterface-compatible engine was passed
            self.ocr_engine = ocr_engine

        # FilePathManager
        self.batch_size_per_worker = batch_size_per_worker
        self.smart_shuffle = smart_shuffle
        self.file_path_manager = FilePathManager(
            input_path=self.input_path,
            max_docs_per_class=self.max_docs_per_class,
            batch_size_per_worker=self.batch_size_per_worker,
            smart_shuffle=self.smart_shuffle,
            logging_level=self.logging_level
        )

        # ImageManager
        self.save_processed_img = save_processed_img
        self.size_threshold_mb = size_threshold_mb
        self.target_pages = target_pages
        self.megapixel = megapixel
        self.dpi = dpi
        self.image_manager = ImageManager(
            image_processor=image_processor,
            save_processed_img=self.save_processed_img,
            megapixel=self.megapixel,
            output_path=self.output_path / "image_data",
            target_pages=self.target_pages,
            dpi=self.dpi,
            size_threshold_mb=self.size_threshold_mb,
            logging_level=self.logging_level
        )

    def create_dataset(self) -> pd.DataFrame:
        """
        Walk through all documents, process each with optional OCR, and produce a single CSV file.

        Returns:
            pd.DataFrame: A DataFrame containing all OCR and metadata results.
        """
        results = []

        # For each batch of files, process them (optionally in parallel)
        for file_batch in self.file_path_manager.file_batches():
            # Tesseract OCR can conflict if used with multiple processes, but let's attempt anyway
            if self.num_workers > 1 and getattr(self.ocr_engine, "engine_name", "") == "Tesseract":
                with Pool(self.num_workers) as pool:
                    class_results = pool.map(self.process_file, file_batch)
                results.extend(class_results)
            else:
                class_results = [self.process_file(file_info) for file_info in file_batch]
                results.extend(class_results)

        # Combine all results into a single DataFrame
        dataset = pd.concat(results, ignore_index=True)
        dataset.to_csv(self.output_path / self.csv_name, index=False)

        # Save parameters used to generate this dataset for reproducibility
        save_run_params(self)
        self.logger.info("Dataset creation complete.")
        return dataset

    def process_file(self, file_info: FileInfo) -> pd.DataFrame:
        """
        Process a single file (PDF/image). Extract text if OCR is enabled.

        Args:
            file_info (FileInfo): Information about the file to be processed.

        Returns:
            pd.DataFrame: DataFrame containing text results (per-page) and metadata.
        """
        ocr_results = []

        for processed_image, image_path, page in self.image_manager.process_image(file_info):
            text = ""
            if self.do_ocr:
                try:
                    self.logger.debug(f"OCR Start -> {file_info.file_path}, page {page}")
                    text = self.ocr_engine.recognize(image=processed_image)
                    self.logger.debug(f"OCR End -> {file_info.file_path}, page {page}")
                except Exception as e:
                    self.logger.error(f"OCR error on file {file_info.file_path}: {e}")
                    text = ""

            ocr_results.append({
                "SourceFilename": file_info.file_path.name,
                "Page": page,
                "Text": text,
                "Class": file_info.class_name,
                "PreprocessedFilename": str(image_path) if self.save_processed_img and image_path else ""
            })

        return pd.DataFrame(ocr_results)
