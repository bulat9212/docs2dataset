from docs2dataset.core.data_handler import DataHandler

import unittest


class TestDataHandler(unittest.TestCase):
    def test_create_dataset(self):

        docs_dir = 'path/to/docs'

        dataset_creator = DataHandler(
            input_path=docs_dir,
            output_path='big_cv_dataset',
            max_docs_per_class=2000,
        )

        dataset = dataset_creator.create_dataset()
        self.assertIsNotNone(dataset)


if __name__ == '__main__':
    unittest.main()
