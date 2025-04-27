#!/usr/bin/env python3
"""
Cortensor Metrics Telegram Bot with Logging

Commands:
  /rank               Show top 25 nodes
  /metric <node>      Show metrics for a specific node

Uses Playwright to scrape the Cortensor heatmap rank table.
Configuration:
  - Create a .env file with TELEGRAM_TOKEN=<your_bot_token>

Dependencies:
  pip install python-telegram-bot python-dotenv playwright
  playwright install chromium
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Setup logging
env_log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=getattr(logging, env_log_level.upper(), logging.INFO)
)
logger = logging.getLogger(__name__)

# Load bot token
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_TOKEN not set in .env")
    raise RuntimeError("TELEGRAM_TOKEN not set in .env")

# Constants
TABLE_URL = "https://dashboard-devnet4.cortensor.network/stats/heatmap/rank/table"
COLUMNS = [
    "Miner", "Score", "Status", "Last Active",
    "Precommit Success %", "Precommit Counter",
    "Commit Success %", "Commit Counter", "Commit/Precommit %",
    "Prepare Success %", "Prepare Counter"
]
MAX_ROWS = 25
DELAY = 1.0  # seconds between messages

async def fetch_table() -> list[list[str]]:
    """
    Scrape the rank table rows, attempt to scroll to load more.
    Return list of rows as list of cell texts.
    """
    logger.info("Starting table fetch from %s", TABLE_URL)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(TABLE_URL, timeout=60000)
            await page.wait_for_selector("table tbody tr", timeout=60000)
            # attempt to scroll to bottom to load more rows
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            # collect rows
            row_elems = await page.query_selector_all("table tbody tr")
            data = []
            for row in row_elems:
                cells = await row.query_selector_all("td")
                texts = [ (await cell.inner_text()).strip() for cell in cells ]
                if len(texts) >= len(COLUMNS):
                    data.append(texts[:len(COLUMNS)])
            logger.info("Fetched %d rows", len(data))
        except PlaywrightTimeoutError as e:
            logger.error("Timeout loading table: %s", e)
            data = []
        except Exception as e:
            logger.exception("Error during fetch_table: %s", e)
            data = []
        finally:
            await browser.close()
    return data

async def rank_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info("/rank command invoked by user %s", update.effective_user.id)
    await context.bot.send_message(chat_id, "Fetching top 25 nodes, please wait...")
    table = await fetch_table()
    if not table:
        logger.warning("No data returned for /rank")
        await context.bot.send_message(chat_id, "No data available.")
        return
    if len(table) < MAX_ROWS:
        logger.warning("Only %d rows fetched, expected %d", len(table), MAX_ROWS)
    for idx, row in enumerate(table[:MAX_ROWS], start=1):
        msg_lines = [f"Rank {idx}"]
        for col, val in zip(COLUMNS, row):
            msg_lines.append(f"{col}: {val}")
        text = "\n".join(msg_lines)
        await context.bot.send_message(chat_id, text)
        await asyncio.sleep(DELAY)
    logger.info("Completed sending /rank responses")

async def metric_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info("/metric invoked by user %s args=%s", update.effective_user.id, context.args)
    if not context.args:
        await context.bot.send_message(chat_id, "Usage: /metric <node_address>")
        return
    target = context.args[0].lower()
    table = await fetch_table()
    if not table:
        await context.bot.send_message(chat_id, "No data available.")
        return
    for row in table:
        if row[0].lower() == target:
            msg_lines = [f"Node: {row[0]}"]
            for col, val in zip(COLUMNS[1:], row[1:]):
                msg_lines.append(f"{col}: {val}")
            await context.bot.send_message(chat_id, "\n".join(msg_lines))
            logger.info("Sent metrics for node %s", target)
            return
    logger.warning("Node %s not found", target)
    await context.bot.send_message(chat_id, "Node not found.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("rank", rank_cmd))
    app.add_handler(CommandHandler("metric", metric_cmd))
    logger.info("Bot is starting...")
    app.run_polling()
