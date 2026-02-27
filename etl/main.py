import logging
import config
from concurrent.futures import ProcessPoolExecutor, as_completed
from extract import fetch_listing_html, fetch_reviews_html
from transform import transform
from load import initialize_output, load_record
from pathlib import Path


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def _ensure_reviews(reviews_html, listing_html, url_done):
    data = transform(listing_html, reviews_html)
    review_count = data.get("review_count") or 0
    reviews = data.get("reviews") or []
    attempts = 0
    while review_count >= 1 and not reviews and attempts < config.REVIEWS_EMPTY_MAX_RETRIES:
        attempts += 1
        logging.info(
            "Reintento %s/%s reseñas para %s",
            attempts, config.REVIEWS_EMPTY_MAX_RETRIES, url_done,
        )
        try:
            reviews_html = fetch_reviews_html(url_done)
            data = transform(listing_html, reviews_html)
            reviews = data.get("reviews") or []
        except Exception as e:
            logging.warning("Reintento reseñas falló: %s", e)
    return data


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
        return (url, None, None, str(cause))
    try:
        reviews_html = fetch_reviews_html(url)
    except Exception as e:
        cause = e
        if hasattr(e, "last_attempt") and e.last_attempt.failed:
            try:
                cause = e.last_attempt.exception()
            except Exception:
                pass
        return (url, None, None, str(cause))
    return (url, listing_html, reviews_html, None)


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

    initialize_output()

    ok = 0
    fail = 0
    with ProcessPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        futures = {executor.submit(_process_one, url): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            url_done, listing_html, reviews_html, err = future.result()
            if err is not None:
                logging.error(f"Failed processing {url}: {err}")
                fail += 1
                continue
            try:
                data = _ensure_reviews(reviews_html, listing_html, url_done)
                rating = data.get("rating")
                review_count = data.get("review_count")
                highlight = data.get("highlight")
                opportunity = data.get("opportunity")
                if rating is None or rating == "":
                    logging.warning("Omitido %s: rating vacío", url_done)
                elif review_count is None or review_count == "":
                    logging.warning("Omitido %s: review_count vacío", url_done)
                elif not highlight:
                    logging.warning("Omitido %s: highlight vacío", url_done)
                elif not opportunity:
                    logging.warning("Omitido %s: opportunity vacío", url_done)
                else:
                    load_record(url_done, data)
                    n_reviews = len(data.get("reviews") or [])
                    logging.info(
                        "Processed: %s (rating=%s, review_count=%s, reviews=%s)",
                        url_done, data.get("rating"), data.get("review_count"), n_reviews,
                    )
                    ok += 1
            except Exception as e:
                logging.error(f"Failed transform/load for {url}: {e}")
                fail += 1

    logging.info(f"Done. OK: {ok}, Failed: {fail}")


if __name__ == "__main__":
    run_pipeline(config.LISTINGS_FILE)