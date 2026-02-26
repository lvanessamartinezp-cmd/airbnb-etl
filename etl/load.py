import csv
import logging
from pathlib import Path

import config


def _ensure_output_dir():
    path = Path(config.OUTPUT_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)


def initialize_output():
    """Create output file and write CSV header if it does not exist."""
    _ensure_output_dir()
    path = Path(config.OUTPUT_FILE)
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["url", "rating", "review_count"])
            writer.writeheader()
        logging.debug("Created output file: %s", config.OUTPUT_FILE)


def load_record(url: str, data: dict):
    """Append one transformed record to the output CSV."""
    _ensure_output_dir()
    row = {
        "url": url,
        "rating": data.get("rating") if data.get("rating") is not None else "",
        "review_count": data.get("review_count") if data.get("review_count") is not None else "",
    }
    with open(config.OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "rating", "review_count"])
        writer.writerow(row)
