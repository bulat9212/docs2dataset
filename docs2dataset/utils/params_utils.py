import json
import logging
import os
from typing import Any

def save_run_params(obj: Any) -> None:
    """
    Inspect an object (e.g., DataHandler) and save relevant constructor parameters to JSON.

    The object is expected to have attributes that match the parameters we care about:
    e.g., input_path, output_path, csv_name, target_pages, ...

    Args:
        obj (Any): The pipeline or handler object with relevant attributes.
    """
    # We can decide which attributes to store.
    # For demonstration, let's store all public attributes that are basic types.
    pipeline_params = {
        "input_path": str(getattr(obj, "input_path", "")),
        "output_path": str(getattr(obj, "output_path", "")),
        "csv_name": getattr(obj, "csv_name", ""),
        "target_pages": getattr(obj, "target_pages", None),
        "dpi": getattr(obj, "dpi", ""),
        "ocr_lang": getattr(obj, "ocr_lang", ""),
        "do_ocr": getattr(obj, "do_ocr", ""),
        "save_processed_img": getattr(obj, "save_processed_img", ""),
        "megapixel": getattr(obj, "megapixel", ""),
        "size_threshold_mb": getattr(obj, "size_threshold_mb", ""),
        "num_workers": getattr(obj, "num_workers", ""),
        "batch_size_per_worker": getattr(obj, "batch_size_per_worker", ""),
        "smart_shuffle": getattr(obj, "smart_shuffle", ""),
        "logging_level": getattr(obj, "logging_level", ""),
        "ocr_engine": getattr(obj.ocr_engine, "engine_name", str(obj.ocr_engine)),
    }
    params_path = os.path.join(str(obj.output_path), "used_args.json")
    with open(params_path, "w", encoding="utf-8") as f:
        json.dump(pipeline_params, f, indent=4, ensure_ascii=False)
    logging.info(f"Pipeline parameters saved to {params_path}.")
