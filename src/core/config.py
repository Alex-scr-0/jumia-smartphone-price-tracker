import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    target_url: str
    max_price: float
    discord_webhook_url: str
    check_interval: int
    db_path: str = "jumia_prices.sqlite3"


def load_config() -> Config:
    target_url = os.getenv("JUMIA_URL", "").strip()
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    if not target_url:
        raise ValueError("Error: JUMIA_URL is missing from the .env file")
    if not discord_webhook or "YOUR_WEBHOOK_HERE" in discord_webhook:
        raise ValueError("Error: Set a valid DISCORD_WEBHOOK_URL in the .env file")

    return Config(
        target_url=target_url,
        max_price=float(os.getenv("MAX_PRICE", "2500")),
        discord_webhook_url=discord_webhook,
        check_interval=int(os.getenv("CHECK_INTERVAL_SECONDS", "600")),
    )