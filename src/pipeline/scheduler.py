import asyncio
import random
import signal
from src.core.config import Config
from src.pipeline.detector import PriceDetector
from src.pipeline.notifier import send_discord_alert
from src.pipeline.scraper import scrape_jumia_products
from src.stealth.stealth_browser import get_stealth_page


class BotScheduler:
    def __init__(self, config: Config, logger):
        self.config = config
        self.logger = logger
        self.detector = PriceDetector(config.db_path, config.max_price)
        self.running = True

    def stop(self) -> None:
        self.logger.info("Shutdown signal received. Closing the bot safely (graceful shutdown).")
        self.running = False

    async def run_cycle(self) -> None:
        async with get_stealth_page(headless=True) as page:
            products = await scrape_jumia_products(page, self.config.target_url, self.logger)
            if not products:
                self.logger.warning("No products were fetched in this cycle.")
                return

            events = self.detector.analyze(products, self.logger)
            for event in events:
                await send_discord_alert(self.config.discord_webhook_url, event, self.logger)
                await asyncio.sleep(1.5)  # Avoid Discord rate limits

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self.stop)
            except NotImplementedError:
                # Windows support for Ctrl+C
                signal.signal(sig, lambda *_: self.stop())

        self.logger.info("🚀 Jumia deal hunter started successfully! (Press Ctrl+C to stop)")

        while self.running:
            try:
                await self.run_cycle()
            except Exception as e:
                self.logger.exception(f"Error in the current cycle (the bot will continue): {e}")

            if not self.running:
                break

            jitter = random.randint(-20, 45)
            sleep_time = max(30, self.config.check_interval + jitter)
            self.logger.info(f"💤 Waiting {sleep_time} seconds before the next scan...")

            for _ in range(sleep_time):
                if not self.running:
                    break
                await asyncio.sleep(1)
