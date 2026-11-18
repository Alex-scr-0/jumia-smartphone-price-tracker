import asyncio
from src.core.config import load_config
from src.core.logger import setup_logger
from src.pipeline.scheduler import BotScheduler


async def main() -> None:
    logger = setup_logger()
    try:
        config = load_config()
    except Exception as e:
        logger.critical(f"Failed to load configuration: {e}")
        return

    scheduler = BotScheduler(config, logger)
    await scheduler.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass