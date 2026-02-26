import logging
import config
from concurrent.futures import ProcessPoolExecutor, as_completed
from extract import fetch_listing_html


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )


def _process_one(url):
    return url, fetch_listing_html(url)


def run_pipeline(input_file):
    setup_logger()

    with open(input_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    max_workers = config.MAX_WORKERS

    ok = 0
    fail = 0
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_process_one, url): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                url_done, html = future.result()
                logging.info(f"Processed successfully: {url_done}")
                ok += 1
            except Exception as e:
                cause = e
                if hasattr(e, "last_attempt") and e.last_attempt.failed:
                    cause = e.last_attempt.exception()
                logging.error(f"Failed processing {url}: {cause}")
                fail += 1

    logging.info(f"Done. OK: {ok}, Failed: {fail}")


if __name__ == "__main__":
    run_pipeline(config.LISTINGS_FILE)