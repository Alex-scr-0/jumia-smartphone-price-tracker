import sqlite3
from dataclasses import dataclass
from typing import List, Optional
from src.pipeline.scraper import Product


@dataclass
class DealEvent:
    event_type: str  # "NEW_DEAL" or "PRICE_DROP"
    product: Product
    old_price: Optional[float] = None


class PriceDetector:
    def __init__(self, db_path: str, max_price: float):
        self.db_path = db_path
        self.max_price = max_price
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    product_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    last_price REAL NOT NULL,
                    url TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def analyze(self, products: List[Product], logger) -> List[DealEvent]:
        events: List[DealEvent] = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for item in products:
                cursor.execute(
                    "SELECT last_price FROM products WHERE product_id = ?",
                    (item.product_id,),
                )
                row = cursor.fetchone()

                if row is None:
                    # First time seeing this product
                    cursor.execute(
                        "INSERT INTO products (product_id, title, last_price, url) VALUES (?, ?, ?, ?)",
                        (item.product_id, item.title, item.price, item.url),
                    )
                    if item.price <= self.max_price:
                        events.append(DealEvent(event_type="NEW_DEAL", product=item))
                else:
                    old_price = float(row[0])
                    if item.price < old_price:
                        # Price decreased
                        cursor.execute(
                            "UPDATE products SET last_price = ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?",
                            (item.price, item.product_id),
                        )
                        if item.price <= self.max_price:
                            events.append(
                                DealEvent(
                                    event_type="PRICE_DROP",
                                    product=item,
                                    old_price=old_price,
                                )
                            )
                    elif item.price > old_price:
                        # Update the price if it increased without sending a notification
                        cursor.execute(
                            "UPDATE products SET last_price = ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?",
                            (item.price, item.product_id),
                        )

        logger.info(f"Price analysis completed: detected {len(events)} notification-worthy opportunities.")
        return events