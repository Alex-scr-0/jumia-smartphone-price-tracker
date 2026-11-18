import re
from dataclasses import dataclass
from typing import List
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from src.stealth.stealth_browser import human_scroll


@dataclass
class Product:
    product_id: str
    title: str
    price: float
    url: str


def clean_price(raw_price: str) -> float:
    """Converts '1,899.00 Dhs' or '1 899 Dhs' into float 1899.0."""
    cleaned = re.sub(r"[^\d.,]", "", raw_price).replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


async def scrape_jumia_products(page: Page, url: str, logger) -> List[Product]:
    """Navigates to Jumia category page and extracts cleaned product items."""
    products: List[Product] = []

    try:
        logger.info(f"Opening page: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)

        # Close the Jumia newsletter popup if it appears
        close_btn = page.locator("button[aria-label='newsletter_popup_close-cta']")
        if await close_btn.count() > 0:
            await close_btn.first.click()

        await page.wait_for_selector("article.prd", timeout=15000)
        await human_scroll(page, steps=4)

        cards = await page.locator("article.prd").all()
        logger.info(f"Found {len(cards)} product cards on the page.")

        for card in cards:
            link_el = card.locator("a.core")
            name_el = card.locator(".name")
            price_el = card.locator(".prc")

            if await link_el.count() == 0 or await name_el.count() == 0 or await price_el.count() == 0:
                continue

            href = await link_el.first.get_attribute("href") or ""
            sku = await link_el.first.get_attribute("data-id") or href
            title = (await name_el.first.inner_text()).strip()
            raw_price = (await price_el.first.inner_text()).strip()
            price = clean_price(raw_price)

            if title and price > 0 and href:
                full_url = f"https://www.jumia.ma{href}" if href.startswith("/") else href
                products.append(
                    Product(
                        product_id=sku,
                        title=title,
                        price=price,
                        url=full_url,
                    )
                )

    except PlaywrightTimeoutError:
        logger.error("Timed out while loading the Jumia page.")
    except Exception as e:
        logger.exception(f"Unexpected error while scraping data: {e}")

    return products