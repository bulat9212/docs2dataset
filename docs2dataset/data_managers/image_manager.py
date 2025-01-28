import io
import logging
from pathlib import Path
from typing import Generator, Tuple

import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image

from docs2dataset.utils.file_info import FileInfo
from docs2dataset.utils.logging_utils import setup_logger

# Avoid DecompressionBombError in Pillow
Image.MAX_IMAGE_PIXELS = None


class ImageManager:
    """
    Handles reading of PDFs, TIFFs, and standard image files.
    Applies optional resizing and external processing (e.g. custom pipeline).
    """

    def __init__(
            self,
            image_processor,
            save_processed_img: bool,
            output_path: Path,
            target_pages: list[int] | None,
            dpi: int,
            logging_level: int,
            megapixel: int,
            size_threshold_mb: int,
    ):
        self.logger = setup_logger(self.__class__.__name__, logging_level)
        self.image_processor = image_processor
        self.save_processed_img = save_processed_img
        self.output_path = output_path
        self.target_pages = target_pages
        self.dpi = dpi
        self.megapixel = megapixel
        self.size_threshold_mb = size_threshold_mb

    def process_image(self, file_info: FileInfo) -> Generator[Tuple[np.ndarray, Path | None, int], None, None]:
        """
        Generator that yields (processed_image, image_path, page_number).

        Args:
            file_info (FileInfo): Contains path and class name.

        Yields:
            (np.ndarray, Optional[Path], int): The processed image (as NumPy array),
                                              the path where it's saved (or None),
                                              and the page number.
        """
        self.logger.info(f"Processing file: {file_info.file_path}")
        file_ext = file_info.file_path.suffix.lower()

        if file_ext == ".pdf":
            yield from self._process_pdf(file_info)
        elif file_ext in [".tiff", ".tif"]:
            yield from self._process_tiff(file_info)
        else:
            yield from self._process_single_image(file_info)

    def _process_single_image(self, file_info: FileInfo) -> Generator[Tuple[np.ndarray, Path | None, int], None, None]:
        self.logger.debug(f"Opening single image: {file_info.file_path}")
        with Image.open(file_info.file_path) as pil_img:
            # Convert to BGR for OpenCV usage
            image_np = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        processed_image = self._resize_image_if_needed(image_np)
        if self.image_processor:
            processed_image = self.image_processor.run(processed_image)

        image_path = self._save_image(processed_image, file_info, page_num=0) if self.save_processed_img else None
        yield processed_image, image_path, 0

    def _process_pdf(self, file_info: FileInfo) -> Generator[Tuple[np.ndarray, Path | None, int], None, None]:
        self.logger.debug(f"Opening PDF: {file_info.file_path}")
        doc = fitz.open(file_info.file_path)
        num_pages = len(doc)

        pages_to_process = self.target_pages if self.target_pages is not None else range(num_pages)
        # Convert negative page indices
        valid_pages = set(
            (num_pages + p) if p < 0 else p
            for p in pages_to_process
            if -num_pages <= p < num_pages
        )

        for page_num in sorted(valid_pages):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=self.dpi)
            pil_img = Image.open(io.BytesIO(pix.tobytes()))
            image_np = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

            processed_image = self._resize_image_if_needed(image_np)
            if self.image_processor:
                processed_image = self.image_processor.run(processed_image)

            image_path = self._save_image(processed_image, file_info,
                                          page_num=page_num) if self.save_processed_img else None
            yield processed_image, image_path, page_num

    def _process_tiff(self, file_info: FileInfo) -> Generator[Tuple[np.ndarray, Path | None, int], None, None]:
        self.logger.debug(f"Opening TIFF: {file_info.file_path}")
        with Image.open(file_info.file_path) as tiff:
            frames = []
            index = 0
            # Count frames in the TIFF
            while True:
                try:
                    tiff.seek(index)
                    frames.append(index)
                    index += 1
                except EOFError:
                    break

            pages_to_process = self.target_pages if self.target_pages is not None else frames
            # Convert -1, etc.
            pages_to_process = [
                (len(frames) + p) if p < 0 else p
                for p in pages_to_process
                if -len(frames) <= p < len(frames)
            ]

            for page_num in sorted(set(pages_to_process)):
                tiff.seek(page_num)
                pil_img = tiff.convert("RGB")
                image_np = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

                processed_image = self._resize_image_if_needed(image_np)
                if self.image_processor:
                    processed_image = self.image_processor.run(processed_image)

                image_path = self._save_image(processed_image, file_info,
                                              page_num=page_num) if self.save_processed_img else None
                yield processed_image, image_path, page_num

    def _resize_image_if_needed(self, image_np: np.ndarray) -> np.ndarray:
        """Downscale image to meet the self.megapixel constraint, if necessary."""
        height, width = image_np.shape[:2]
        max_pixels = self.megapixel * 1_000_000
        curr_pixels = width * height

        if curr_pixels > max_pixels:
            ratio = (max_pixels / float(curr_pixels)) ** 0.5
            new_size = (int(width * ratio), int(height * ratio))
            image_np = cv2.resize(image_np, new_size, interpolation=cv2.INTER_LANCZOS4)
            self.logger.debug(
                f"Resized from ~{curr_pixels / 1_000_000:.2f} MP to {self.megapixel} MP limit"
            )
        return image_np

    def _save_image(self, image_np: np.ndarray, file_info: FileInfo, page_num: int | None) -> Path:
        """
        Save the processed image to disk with optional compression if it exceeds size_threshold_mb.
        Returns the path to the saved image.
        """
        class_name = file_info.class_name
        class_output_dir = self.output_path / class_name
        class_output_dir.mkdir(parents=True, exist_ok=True)

        # Construct filename
        suffix = f"_page{page_num}" if page_num is not None else ""
        filename = f"{class_name}__{file_info.file_path.stem}{suffix}.jpg"
        output_file_path = class_output_dir / filename

        # Encode to JPEG buffer
        success, buffer = cv2.imencode(".jpg", image_np)
        if not success:
            self.logger.error("Failed to encode image to .jpg format.")
            return output_file_path

        file_size_mb = len(buffer) / (1024 * 1024)
        if file_size_mb > self.size_threshold_mb:
            # Attempt progressive compression
            for quality in range(70, 40, -10):
                success, buffer_test = cv2.imencode(".jpg", image_np, [cv2.IMWRITE_JPEG_QUALITY, quality])
                if success and (len(buffer_test) / (1024 * 1024)) <= self.size_threshold_mb:
                    buffer = buffer_test
                    self.logger.info(
                        f"Compressed image to {quality} quality to fit under {self.size_threshold_mb} MB."
                    )
                    break
            else:
                self.logger.warning(
                    f"Could not compress below {self.size_threshold_mb} MB even at ~40% quality."
                )

        with open(output_file_path, "wb") as f:
            f.write(buffer)

        self.logger.debug(f"Saved processed image to {output_file_path}")
        return output_file_path
