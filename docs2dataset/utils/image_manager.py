from PIL import Image
import fitz  # PyMuPDF
import cv2
import numpy as np
import io
from .logging_utils import setup_logger
import logging
from docs2dataset.utils.file_info import FileInfo

# to avoid DecompressionBombError
Image.MAX_IMAGE_PIXELS = None


class ImageManager:
    def __init__(self, image_processor=None, save_processed_img=True, output_path=None, target_pages=None,
                 dpi=300, logging_level=logging.INFO, megapixel=3, size_threshold_mb=5):
        self.logger = setup_logger(self.__class__.__name__, logging_level)
        self.image_processor = image_processor
        self.save_processed_img = save_processed_img
        self.output_path = output_path
        self.target_pages = target_pages if target_pages is not None else [0]  # Default to first page if None
        self.dpi = dpi
        self.megapixel = megapixel
        self.size_threshold_mb = size_threshold_mb

    def process_image(self, file: FileInfo):
        """Generator that yields processed images for the target pages."""
        self.logger.info(f"Processing image: {file.file_path}")
        file_ext = file.file_path.suffix.lower()

        if file_ext == '.pdf':
            yield from self._process_pdf(file)
        elif file_ext in ['.tiff', '.tif']:
            yield from self._process_tiff(file)
        else:
            yield from self._process_standard_image(file)

    def _process_standard_image(self, file: FileInfo):
        for page in self.target_pages:
            if page == 0:
                image = Image.open(file.file_path)  # Load the image with PIL
                self.logger.info(f"Opened image: {file.file_path}")

                # Convert the PIL Image to a NumPy array
                image_np = np.array(image)

                # Ensure image is in the correct format (BGR for OpenCV)
                if image.mode != 'RGB':
                    image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

                processed_image = self.correct_image(image_np, file)  # Process using the corrected image
                if self.save_processed_img:
                    processed_image = self.image_processor.run(processed_image)

                if self.save_processed_img:
                    image_path = self.save_image(processed_image, file, page)
                else:
                    image_path = None

                yield processed_image, image_path, page

    def _process_pdf(self, file: FileInfo):
        file_path = file.file_path
        self.logger.info(f"Opened PDF: {file_path}")
        document = fitz.open(file_path)
        num_pages = len(document)

        pages_to_process = list(set(p if p != -1 else num_pages - 1 for p in self.target_pages if p < num_pages))

        for page_num in sorted(pages_to_process):
            page = document.load_page(page_num)
            pix = page.get_pixmap(dpi=self.dpi)
            image = Image.open(io.BytesIO(pix.tobytes()))

            # Convert PIL Image to NumPy array
            image_np = np.array(image)
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

            processed_image = self.correct_image(image_np, file)
            processed_image = self.image_processor.run(processed_image)

            if self.save_processed_img:
                image_path = self.save_image(processed_image, file, page_num)
            else:
                image_path = None

            yield processed_image, image_path, page_num

    def _process_tiff(self, file: FileInfo):
        self.logger.info(f"Opened TIFF: {file.file_path}")
        tiff = Image.open(file.file_path)
        num_pages = 0
        while True:
            try:
                tiff.seek(num_pages)
                num_pages += 1
            except EOFError:
                break

        pages_to_process = list(set(p if p != -1 else num_pages - 1 for p in self.target_pages if p < num_pages))

        for page_num in sorted(pages_to_process):
            tiff.seek(page_num)
            image = tiff.convert("RGB")

            # Convert PIL Image to NumPy array
            image_np = np.array(image)
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

            processed_image = self.correct_image(image_np, file)
            processed_image = self.image_processor.run(processed_image)

            if self.save_processed_img:
                image_path = self.save_image(processed_image, file, page_num)
            else:
                image_path = None

            yield processed_image, image_path, page_num

    def correct_image(self, image, file: FileInfo):
        self.logger.info(f"Correcting image {file.file_path}")
        max_pixels = 1000000 * self.megapixel

        # Check if the image is a PIL Image or a NumPy array
        if isinstance(image, Image.Image):
            width, height = image.size
        elif isinstance(image, np.ndarray):
            height, width = image.shape[:2]
        else:
            raise TypeError("Unsupported image type")

        if width * height > max_pixels:
            ratio = (max_pixels / float(width * height)) ** 0.5
            new_size = (int(width * ratio), int(height * ratio))
            if isinstance(image, Image.Image):
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            elif isinstance(image, np.ndarray):
                image = cv2.resize(image, new_size, interpolation=cv2.INTER_LANCZOS4)
            self.logger.info(
                f"Resized source {(width * height) / 1000000} MP image to {new_size} to meet {self.megapixel} MP requirement")
        return image

    def save_image(self, image, file: FileInfo, page_num=None):
        """Save the processed image to the output path and return the new file path."""
        if self.output_path:
            class_dir = file.class_name
            class_output_path = self.output_path / class_dir
            class_output_path.mkdir(parents=True, exist_ok=True)

            if page_num is not None:
                output_file_name = f"{file.file_path.stem}_page[{page_num}].jpg"
            else:
                output_file_name = f"{file.file_path.stem}.jpg"

            output_file_path = class_output_path / output_file_name

            # Convert PIL image to OpenCV format if it's not already a numpy array
            if isinstance(image, Image.Image):
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Calculate future image size and apply compression if necessary
            success, buffer = cv2.imencode('.jpg', image)
            file_size = len(buffer)

            if file_size > self.size_threshold_mb * 1024 * 1024:
                for quality in range(90, 10, -10):
                    success, buffer = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                    if len(buffer) <= 5 * 1024 * 1024:
                        self.logger.info(f"Saved image with compression at quality {quality}")
                        break
                else:
                    self.logger.warning(f"Could not reduce image size below 5 MB even with maximum compression")
            else:
                self.logger.debug(f"Image size {file_size / (1024 * 1024)}is under 5 MB without compression")

            with open(output_file_path, 'wb') as f:
                f.write(buffer)
            self.logger.info(f"Saved processed image to: {output_file_path}")
            return output_file_path
        return None
