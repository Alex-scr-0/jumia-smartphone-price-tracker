import asyncio
import httpx
from src.pipeline.detector import DealEvent


async def send_discord_alert(webhook_url: str, event: DealEvent, logger, retries: int = 3) -> bool:
    p = event.product
    if event.event_type == "PRICE_DROP" and event.old_price:
        drop_pct = round(((event.old_price - p.price) / event.old_price) * 100, 1)
        title = f"🔥 Price drop (-{drop_pct}%)"
        desc = f"**{p.title}**\n💰 New price: **{p.price} DH** (was ~~{event.old_price} DH~~)\n🔗 [View product on Jumia]({p.url})"
        color = 3066993  # Green
    else:
        title = "🆕 New deal within budget"
        desc = f"**{p.title}**\n💰 Price: **{p.price} DH**\n🔗 [View product on Jumia]({p.url})"
        color = 3447003  # Blue

    payload = {
        "username": "Jumia Deal Hunter",
        "embeds": [{"title": title, "description": desc, "color": color}],
    }

    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(webhook_url, json=payload)
                if resp.status_code in (200, 204):
                    logger.info(f"Discord notification sent successfully: {p.title[:40]}...")
                    return True
                logger.warning(f"Unexpected Discord response ({resp.status_code}), attempt {attempt}/{retries}")
        except Exception as e:
            logger.warning(f"Failed to send Discord notification (attempt {attempt}/{retries}): {e}")

        await asyncio.sleep(2 * attempt)

    logger.error(f"Could not send notification after {retries} attempts: {p.title}")
    return False