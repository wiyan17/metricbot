#!/usr/bin/env python3
"""
Cortensor Metrics Telegram Bot

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
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright

# Load bot token
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
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
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(TABLE_URL, timeout=60000)
        await page.wait_for_selector("table tbody tr", timeout=60000)
        elements = await page.query_selector_all("table tbody tr")
        data = []
        for row in elements:
            cells = await row.query_selector_all("td")
            texts = [await c.inner_text() for c in cells]
            texts = [t.strip() for t in texts]
            if len(texts) >= len(COLUMNS):
                data.append(texts[:len(COLUMNS)])
        await browser.close()
        return data

async def rank_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "Fetching top 25 nodes, please wait...")
    try:
        table = await fetch_table()
    except Exception as e:
        await context.bot.send_message(chat_id, f"Error: {e}")
        return

    for idx, row in enumerate(table[:MAX_ROWS], start=1):
        msg_lines = [f"Rank {idx}"]
        for col, val in zip(COLUMNS, row):
            msg_lines.append(f"{col}: {val}")
        await context.bot.send_message(chat_id, "\n".join(msg_lines))
        await asyncio.sleep(DELAY)

async def metric_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        await context.bot.send_message(chat_id, "Usage: /metric <node_address>")
        return
    target = args[0].lower()
    try:
        table = await fetch_table()
    except Exception as e:
        await context.bot.send_message(chat_id, f"Error: {e}")
        return
    for row in table:
        if row[0].lower() == target:
            lines = [f"Node: {row[0]}"]
            for col, val in zip(COLUMNS[1:], row[1:]):
                lines.append(f"{col}: {val}")
            await context.bot.send_message(chat_id, "\n".join(lines))
            return
    await context.bot.send_message(chat_id, "Node not found.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("rank", rank_cmd))
    app.add_handler(CommandHandler("metric", metric_cmd))
    print("Bot is starting...")
    app.run_polling()
