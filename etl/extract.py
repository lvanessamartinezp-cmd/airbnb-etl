import logging
import config
from playwright.sync_api import sync_playwright
from tenacity import retry, stop_after_attempt, wait_fixed


@retry(stop=stop_after_attempt(config.MAX_RETRIES), wait=wait_fixed(config.RETRY_WAIT_SECONDS))
def fetch_listing_html(url):
    logging.info(f"Extracting URL: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=config.USER_AGENT,
            viewport={"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT},
            locale=config.LOCALE,
        )
        page = context.new_page()
        page.goto(url, timeout=config.REQUEST_TIMEOUT, wait_until="domcontentloaded")
        page.wait_for_load_state("load")
        page.wait_for_timeout(config.PAGE_WAIT_MS)

        html = page.content()
        browser.close()

        return html

