from pathlib import Path
from random import shuffle
from math import ceil
from .file_info import FileInfo
from .file_utils import is_image_file
from .logging_utils import setup_logger
import logging


class FilePathManager:
    def __init__(self, input_path, max_docs_per_class=None, batch_size_per_worker=1, smart_shuffle=False,
                 logging_level=logging.INFO):
        self.input_path = Path(input_path)
        self.max_docs_per_class = max_docs_per_class
        self.batch_size_per_worker = batch_size_per_worker
        self.smart_shuffle = smart_shuffle
        self.logger = setup_logger(self.__class__.__name__, logging_level)

    def file_batches(self):
        """Generator that yields batches of FileInfo objects grouped by their class directory."""
        self.logger.info("Generating file batches...")
        for class_dir in self.input_path.iterdir():
            if class_dir.is_dir():
                all_files = [FileInfo(file_path=f, class_name=class_dir.name) for f in class_dir.rglob('*') if
                             f.is_file() and is_image_file(f)]
                self.logger.info(f"Found {len(all_files)} files in class directory {class_dir.name}")
                if self.smart_shuffle and self.max_docs_per_class:
                    all_files = self.smart_shuffle_files(class_dir)
                elif self.max_docs_per_class:
                    all_files = self.shuffle_and_limit(all_files)
                else:
                    shuffle(all_files)

                # Yield batches of files
                for i in range(0, len(all_files), self.batch_size_per_worker):
                    batch = all_files[i:i + self.batch_size_per_worker]
                    self.logger.info(f"Yielding batch of {len(batch)} files")
                    yield batch

    def smart_shuffle_files(self, class_dir: Path,):
        """Smart shuffle that gathers documents from nested subdirectories according to the specified rules."""
        self.logger.info("Performing smart shuffle")

        subdir_dict = {'root': []}
        base_path = Path(class_dir)

        for item in base_path.iterdir():
            if item.is_file() and is_image_file(item):
                subdir_dict['root'].append(FileInfo(file_path=item.resolve(), class_name=class_dir.name))
            elif item.is_dir():
                subdir_dict[item.name] = []
                for file in item.rglob('*'):
                    if file.is_file() and is_image_file(file):
                        subdir_dict[item.name].append(FileInfo(file_path=file.resolve(), class_name=class_dir.name))

        # Initialize the final batch and the remaining number of documents to gather
        final_batch = []
        docs_remain_to_gather = self.max_docs_per_class

        while docs_remain_to_gather > 0 and subdir_dict:
            num_take_from_each_subdir = ceil(docs_remain_to_gather / len(subdir_dict))

            for subdir in list(subdir_dict.keys()):  # Use list to allow modification during iteration
                subdir_files = subdir_dict[subdir]
                take_count = min(num_take_from_each_subdir, len(subdir_files))

                final_batch.extend(subdir_files[:take_count])
                subdir_dict[subdir] = subdir_files[take_count:]

                # Remove the subdir if no files remain
                if not subdir_dict[subdir]:
                    del subdir_dict[subdir]

            docs_remain_to_gather = self.max_docs_per_class - len(final_batch)

            # If we already have enough documents, stop gathering
            if len(final_batch) >= self.max_docs_per_class:
                break

        # Shuffle the final batch and trim to the desired number of documents
        shuffle(final_batch)
        return final_batch[:self.max_docs_per_class]

    def shuffle_and_limit(self, files):
        shuffle(files)
        limited_files = files[:self.max_docs_per_class]
        self.logger.info(f"Limited files to {len(limited_files)}")
        return limited_files
