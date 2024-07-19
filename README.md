
# docs2dataset

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
## Development Setup

Set up development environment:

```bash
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Installation Guide

Install the project using `pip` directly from the GitHub repository:

```bash
pip install git+https://github.com/bulat9212/docs2dataset.git
```

Or clone the repository and install it in editable mode:

```bash
git clone git@github.com:bulat9212/docs2dataset.git
pip install -e docs2dataset
```

## Usage Example

```python
from docs2dataset import DataHandler
from docs2dataset.preprocessing import ImageProcessorInterface


custom_processor: ImageProcessorInterface = your_custom_processor_implementation

dataset_creator = DataHandler(
    # required
    input_path='path_to_docs_dir',
    output_path='dataset',
    max_docs_per_class=10,
    # optional
    image_processor=custom_processor,
    target_pages=[0, 1, -1], # will process all pages by default 
    save_processed_img=True, # False by default
    do_ocr=True              # True by default
)

dataset = dataset_creator.create_dataset()

# |-path_do_docs_dir
#   |-Class_A
#     |-sub_class_a
#       |-doc_example1.pdf
#     |-doc_example2.tif
#   |-Class_C
#     |-doc_example3.jpg
#     |-doc_example4.png
# ...

# As the result handler will create text_data.csv inside output_path, 
# And image_data dir with subdirs contain images for each class if save_processed_img=True (default False).

# |-output_path
#   |-text_data.csv
#   |-app.log
#   |-image_data
#     |-Class_A
#       |-doc_example1_page[0].jpg
#       |-doc_example1_page[1].jpg
#       |-doc_example1_page[5].jpg
#       |-doc_example2_page[0].jpg
#     |-Class_C
#       |-doc_example3_page[0].jpg
#       |-doc_example4_page[0].jpg

```

### Example Output CSV


| SourceFilename   | Page | Text                | Class   | PreprocessedFilename     |
|------------------|------|---------------------|---------|--------------------------|
| doc_example1.pdf | 0    | ocr recognized text | Class_A | doc_example1_page[0].jpg |
| ...              | ...  | ...                 | ...     | ...                      |
| doc_example4.pdf | 0    | ocr recognized text | Class_C | doc_example4_page[0].jpg |


## TODO

- [ ] Write bad images to a separate log file or CSV file
- [ ] Add column with detailed info about image size to the final CSV
- [ ] Adjust logging for multiprocessing, create a log file, ensure the log is set up once after creating more DataHandler instances, add more log messages. Increment log file name if it already exists.
- [ ] Add type hints and refactor the code
- [ ] Revise the project structure
- [ ] Add timings logging and log the mean image processing time
- [ ] Refactor requirements.txt and setup.py
- [ ] Add Tesseract process importance parameter
- [ ] Properly filter 0 confidence tokens
- [ ] Avoid `.dirs`
- [ ] Add tests
- [ ] Handle `-2`, `-3`, ... pages, not only `-1`
- [ ] Fix onnx pickle issue when trying to use onnx image processor in multiprocessing   
- [ ] Refactor and rename `smart_shuffle`
- [ ] Save the used data handler config file to the output directory
- [ ] Add proper handling of `DecompositionBombWarning`
- [ ] Rewrite `ImageManager` to use the factory pattern with interface and implementations of pdf, tiff, standard-image handlers
- [ ] Replace `PyMuPDF` with `pdf2img`