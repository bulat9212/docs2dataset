# File: tests/test_data_handler.py
from docs2dataset.data_handler import DataHandler
from docs2dataset.ocr.implementations.pytesseract_ocr import PytesseractOCR

import unittest


class TestDataHandler(unittest.TestCase):
    def test_create_dataset(self):

        docs_dir = 'path/to/docs'

        dataset_creator = DataHandler(
            input_path=docs_dir,
            output_path='big_cv_dataset',
            ocr_engine=PytesseractOCR(lang='rus'),
            max_docs_per_class=2000,
            batch_size_per_worker=10,
            num_workers=1,
            dpi=300,
            save_processed_img=True,
            csv_name='big_cv_dataset.csv',
            # target_pages=[*range(10), -1],
            target_pages=[0, 1, 2, 3, 4, -1],
            ocr_lang=['rus'],
            logging_level='INFO',
            megapixel=3,
            size_threshold_mb=5,
            smart_shuffle=True,
            do_ocr=False,
        )

        dataset = dataset_creator.create_dataset()
        self.assertIsNotNone(dataset)


if __name__ == '__main__':
    unittest.main()
