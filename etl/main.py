import logging
from pathlib import Path

import config
from concurrent.futures import ProcessPoolExecutor, as_completed
from extract import fetch_listing_html
from transform import transform


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )


def _process_one(url):
    try:
        listing_html = fetch_listing_html(url)
    except Exception as e:
        cause = e
        if hasattr(e, "last_attempt") and e.last_attempt.failed:
            try:
                cause = e.last_attempt.exception()
            except Exception:
                pass
        return (url, None, str(cause))
    return (url, listing_html, None)


def run_pipeline(input_file):
    setup_logger()

    path = Path(input_file)
    if not path.exists():
        logging.error("Input file not found: %s", input_file)
        return

    with open(path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        logging.warning("No URLs in %s", input_file)
        return

    max_workers = config.MAX_WORKERS

    ok = 0
    fail = 0
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_process_one, url): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            url_done, listing_html, err = future.result()
            if err is not None:
                logging.error(f"Failed processing {url}: {err}")
                fail += 1
                continue
            try:
                data = transform(listing_html)
                logging.info(f"Processed successfully: {url_done} (rating=%s, review_count=%s)", data.get("rating"), data.get("review_count"))
                ok += 1
            except Exception as e:
                logging.error(f"Failed transform for {url}: {e}")
                fail += 1

    logging.info(f"Done. OK: {ok}, Failed: {fail}")


if __name__ == "__main__":
    run_pipeline(config.LISTINGS_FILE)