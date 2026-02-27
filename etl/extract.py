import logging
import config
from playwright.sync_api import sync_playwright
from tenacity import retry, stop_after_attempt, wait_fixed


def _review_item_locator(page):
    return page.locator("div[data-review-id]")


@retry(
    stop=stop_after_attempt(config.MAX_RETRIES),
    wait=wait_fixed(config.RETRY_WAIT_SECONDS),
)
def fetch_listing_html(url):
    logging.info(f"Extracting listing: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=config.USER_AGENT,
            viewport={
                "width": config.VIEWPORT_WIDTH,
                "height": config.VIEWPORT_HEIGHT,
            },
            locale=config.LOCALE,
        )
        page = context.new_page()

        page.goto(
            url,
            timeout=config.REQUEST_TIMEOUT,
            wait_until="domcontentloaded",
        )
        page.wait_for_load_state("load")
        page.wait_for_timeout(config.PAGE_WAIT_MS)

        html = page.content()
        browser.close()
        return html


@retry(
    stop=stop_after_attempt(config.MAX_RETRIES),
    wait=wait_fixed(config.RETRY_WAIT_SECONDS),
)
def fetch_reviews_html(listing_url):
    base = listing_url.strip().rstrip("/")
    reviews_url = f"{base}/reviews"
    logging.info(f"Extracting reviews page: {reviews_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=config.USER_AGENT,
            viewport={
                "width": config.VIEWPORT_WIDTH,
                "height": config.VIEWPORT_HEIGHT,
            },
            locale=config.LOCALE,
        )
        page = context.new_page()

        page.goto(
            reviews_url,
            timeout=config.REQUEST_TIMEOUT,
            wait_until="domcontentloaded",
        )
        page.wait_for_load_state("load")
        page.wait_for_timeout(config.PAGE_WAIT_MS)
        sort_trigger = (
            page.get_by_role("button", name="Las más relevantes")
            .or_(page.locator("[role='button']").filter(has_text="relevantes"))
            .first
        )
        sort_trigger.wait_for(state="visible", timeout=10000)
        sort_trigger.click()
        page.wait_for_timeout(500)

        option = page.get_by_role("option", name="Las más recientes").first
        option.wait_for(state="visible", timeout=5000)
        option.click()

        review_items = _review_item_locator(page)
        try:
            review_items.first.wait_for(state="visible", timeout=15000)
            page.wait_for_timeout(1000)
        except Exception:
            pass
        count = review_items.count()
        if count == 0:
            logging.warning("No se encontraron bloques de reseña en la página")
            html = ""
        else:
            take = min(config.REVIEWS_TOP_N, count)
            html_parts = []
            for i in range(take):
                html_parts.append(review_items.nth(i).evaluate("el => el.outerHTML"))
            html = "<div data-reviews=\"first-5\">" + "".join(html_parts) + "</div>"
        browser.close()
        return html
