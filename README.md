# Jumia Price Monitor

A 24/7 Playwright-based price monitoring bot for Jumia category pages. It scrapes product listings, persists the latest price for each product in SQLite, detects new deals and price drops, and sends Discord webhook notifications.

## Features

- Browser automation with Playwright Chromium
- Stealth-oriented browser settings and human-like scrolling
- Automatic extraction and cleaning of Jumia product titles, prices, and URLs
- Persistent SQLite price history
- Detection of:
  - New products below the configured maximum price
  - Subsequent price drops below the configured maximum price
- Asynchronous Discord webhook alerts with retries
- Rotating file logs and console logs
- Randomized monitoring intervals
- Graceful shutdown on `SIGINT` and `SIGTERM`

## Architecture

The project follows separation of concerns:

| Module | Responsibility |
| --- | --- |
| `main.py` | Application entry point and component startup |
| `src/core/config.py` | Environment configuration and typed application settings |
| `src/core/logger.py` | Console and rotating file logging |
| `src/stealth/stealth_browser.py` | Playwright browser, browser context, and human-like behavior |
| `src/pipeline/scraper.py` | Jumia page navigation and product data extraction |
| `src/pipeline/detector.py` | SQLite state management and deal/price-drop detection |
| `src/pipeline/notifier.py` | Discord webhook payload creation and delivery |
| `src/pipeline/scheduler.py` | Monitoring cycles, jittered scheduling, and graceful shutdown |

For each cycle, the scheduler opens a browser page, scrapes product cards, compares the results with the SQLite state, and sends alerts for qualifying events.

## Project Structure

```text
Jumia/
├── main.py
├── .env
├── .gitignore
├── requirements.txt
├── jumia_prices.sqlite3
├── logs/
│   └── jumia_hunter.log
└── src/
    ├── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── config.py
    │   └── logger.py
    ├── stealth/
    │   ├── __init__.py
    │   └── stealth_browser.py
    └── pipeline/
        ├── __init__.py
        ├── scraper.py
        ├── detector.py
        ├── notifier.py
        └── scheduler.py
```

## Requirements

- Python 3.10 or newer
- Internet access
- A Jumia category or product-list URL
- A Discord webhook URL

## Setup

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
```

### 3. Configure the environment

Create a `.env` file in the project root. Do not commit it or share its contents.

```dotenv
JUMIA_URL=https://www.jumia.ma/smartphones/
MAX_PRICE=2500
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/<your-webhook-id>/<your-webhook-token>
CHECK_INTERVAL_SECONDS=600
```

| Variable | Description |
| --- | --- |
| `JUMIA_URL` | Jumia category or listing page to monitor |
| `MAX_PRICE` | Maximum price, in the site's local currency, that qualifies for an alert |
| `DISCORD_WEBHOOK_URL` | Discord webhook receiving deal notifications |
| `CHECK_INTERVAL_SECONDS` | Base interval between monitoring cycles |

The SQLite database defaults to `jumia_prices.sqlite3`. The default log location is `logs/jumia_hunter.log`.

## Running the Bot

```powershell
python main.py
```

Stop it with `Ctrl+C`. The scheduler stops after the active shutdown request and closes each browser cycle safely.

## How Price Detection Works

1. A product is inserted into SQLite when it is discovered for the first time.
2. A first-time product is notified only when its price is at or below `MAX_PRICE`.
3. A later lower price generates a price-drop event.
4. A later higher price updates SQLite but does not generate an alert.
5. Each product is identified by the Jumia data ID found on the listing card, with the product link used as a fallback.

## Logging and Runtime Files

- `logs/jumia_hunter.log` stores application logs using a 5 MB rotating file policy.
- `jumia_prices.sqlite3` stores product IDs, titles, prices, URLs, and update timestamps.
- `.env` contains credentials and must remain private.
- `.gitignore` excludes `.env`, SQLite databases, logs, virtual environments, and Python caches.

## Edge Cases and Recommended Improvements

The codebase should be hardened before long-term unattended production use:

- **Price parsing:** `clean_price()` removes commas and dots ambiguously. Localized values need explicit decimal/thousand-separator handling and should return `None` for invalid input rather than `0.0`.
- **Configuration validation:** Numeric environment values need bounded validation. Invalid, negative, or zero intervals and invalid URLs should produce clear startup errors.
- **Type safety:** Add a `logging.Logger` protocol/type annotation for module helpers and remove broad `Any`-style boundaries where possible.
- **Immutable models:** Mark scrape and event dataclasses as frozen once their data is no longer expected to mutate.
- **SQLite reliability:** Validate database records, use a typed path, and add transactions, migrations, indexes, and stale-record cleanup if the catalog grows.
- **Duplicate notifications:** Persist the latest observed price only after successful notification delivery, or introduce explicit notification state to recover cleanly after restarts.
- **Discord retries:** Use HTTP status handling for `429`, honor `Retry-After`, validate response bodies, and cap Discord embed description length.
- **Playwright resilience:** Selectors may change, and the scraper should fall back to alternate selectors and retry transient navigation failures.
- **Shutdown behavior:** Consolidate signal handling and use `asyncio.Event` for a race-free shutdown, especially during a cycle or notification delay.
- **Scheduler type safety:** Define async callback protocols and a typed shutdown event instead of using mutable boolean state.
- **Resource cleanup:** Keep browser startup, database connections, HTTP clients, and logger handlers on explicit lifecycles and close them deterministically.
- **Runtime compatibility:** Verify behavior across Windows and Linux because Playwright and signal handling differ by platform.

## Operational Notes

- Jumia markup, anti-bot protections, and network availability can change without notice.
- Keep request frequency reasonable and respect Jumia's terms of use and applicable local regulations.
- Restrict access to the log, SQLite database, environment file, and Discord webhook.
