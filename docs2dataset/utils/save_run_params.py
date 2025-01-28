import os
import json
import logging


def save_run_params(self):
    """
    Save the TrainingPipeline's parameters to a JSON file for reproducibility.
    """
    pipeline_params = {
        "input_path": str(self.input_path),
        "output_path": str(self.output_path),
        "csv_name": self.csv_name,
        "target_pages": self.target_pages,
        "dpi": self.dpi,
        "ocr_lang": self.ocr_lang,
        "do_ocr": self.do_ocr,
        "save_processed_img": self.save_processed_img,
        "megapixel": self.megapixel,
        "size_threshold_mb": self.size_threshold_mb,
        "num_workers": self.num_workers,
        "batch_size_per_worker": self.batch_size_per_worker,
        "smart_shuffle": self.smart_shuffle,
        "logging_level": self.logging_level,
        "ocr_engine": self.ocr_engine.__class__.__name__,
    }
    params_path = os.path.join(self.output_path, 'used_args.json')
    with open(params_path, 'w', encoding='utf-8') as f:
        json.dump(pipeline_params, f, indent=4, ensure_ascii=False)
    logging.info(f"Pipeline parameters saved to {params_path}.")
