import asyncio
import random
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Page


@asynccontextmanager
async def get_stealth_page(headless: bool = True):
    """Creates a stealth Playwright browser context and yields a Page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="fr-MA",
            timezone_id="Africa/Casablanca",
        )

        # Hide automation fingerprints
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        page = await context.new_page()
        try:
            yield page
        finally:
            await context.close()
            await browser.close()


async def human_scroll(page: Page, steps: int = 4) -> None:
    """Simulates human-like gradual scrolling to trigger lazy-loaded products."""
    for _ in range(steps):
        scroll_amount = random.randint(400, 800)
        await page.mouse.wheel(0, scroll_amount)
        await asyncio.sleep(random.uniform(0.6, 1.4))