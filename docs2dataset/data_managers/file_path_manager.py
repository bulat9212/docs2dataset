import logging
from math import ceil
from pathlib import Path
from random import shuffle
from typing import Generator, List

from docs2dataset.utils.file_info import FileInfo
from docs2dataset.utils.file_utils import is_image_file
from docs2dataset.utils.logging_utils import setup_logger


class FilePathManager:
    """
    Scans directories under a root input_path, grouping files by class (directory name).
    Provides an iterator of batches of files for parallel processing.
    """

    def __init__(
        self,
        input_path: Path,
        max_docs_per_class: int,
        batch_size_per_worker: int,
        smart_shuffle: bool,
        logging_level: int = logging.INFO
    ):
        self.input_path = Path(input_path)
        self.max_docs_per_class = max_docs_per_class
        self.batch_size_per_worker = batch_size_per_worker
        self.smart_shuffle = smart_shuffle
        self.logger = setup_logger(self.__class__.__name__, logging_level)

    def file_batches(self) -> Generator[List[FileInfo], None, None]:
        """
        Yields:
            Generator[List[FileInfo], None, None]: Batches of FileInfo objects to process.
        """
        self.logger.info("Generating file batches...")

        for class_dir in self.input_path.iterdir():
            if class_dir.is_dir():
                all_files = [
                    FileInfo(file_path=f, class_name=class_dir.name)
                    for f in class_dir.rglob("*")
                    if f.is_file() and is_image_file(f)
                ]

                self.logger.info(f"Found {len(all_files)} files in class directory '{class_dir.name}'")

                # Decide how to limit/shuffle
                if self.smart_shuffle and self.max_docs_per_class:
                    all_files = self._smart_shuffle_files(class_dir)
                elif self.max_docs_per_class is not None and self.max_docs_per_class > 0:
                    shuffle(all_files)
                    all_files = all_files[: self.max_docs_per_class]
                else:
                    shuffle(all_files)

                # Yield in slices
                for i in range(0, len(all_files), self.batch_size_per_worker):
                    batch = all_files[i : i + self.batch_size_per_worker]
                    self.logger.debug(f"Yielding a batch of {len(batch)} file(s) for class '{class_dir.name}'")
                    yield batch

    def _smart_shuffle_files(self, class_dir: Path) -> List[FileInfo]:
        """
        Distributes picks from root + subdirectories so each subdirectory is
        proportionally sampled until max_docs_per_class is reached.

        Args:
            class_dir (Path): Directory for a specific "class."

        Returns:
            List[FileInfo]: Shuffled set of file info objects, up to max_docs_per_class.
        """
        self.logger.info("Performing smart shuffle...")
        subdir_dict = {"root": []}
        base_path = Path(class_dir)

        # Collect files under root and subdirs
        for item in base_path.iterdir():
            if item.is_file() and is_image_file(item):
                subdir_dict["root"].append(FileInfo(file_path=item.resolve(), class_name=class_dir.name))
            elif item.is_dir():
                subdir_dict[item.name] = []
                for file in item.rglob("*"):
                    if file.is_file() and is_image_file(file):
                        subdir_dict[item.name].append(FileInfo(file_path=file.resolve(), class_name=class_dir.name))

        final_batch = []
        docs_needed = self.max_docs_per_class

        while docs_needed > 0 and subdir_dict:
            num_take_each = ceil(docs_needed / len(subdir_dict))
            # For each subdir, take up to num_take_each
            for subdir in list(subdir_dict.keys()):
                available_files = subdir_dict[subdir]
                to_take = min(num_take_each, len(available_files))
                final_batch.extend(available_files[:to_take])
                subdir_dict[subdir] = available_files[to_take:]

                if not subdir_dict[subdir]:
                    del subdir_dict[subdir]

            docs_needed = self.max_docs_per_class - len(final_batch)

            if len(final_batch) >= self.max_docs_per_class:
                break

        shuffle(final_batch)
        return final_batch[: self.max_docs_per_class]
