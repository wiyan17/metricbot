#!/usr/bin/env python3
"""
Simple Telegram bot to scrape Cortensor heatmap rank table.
Commands:
  /rank               - top 25 nodes
  /metric <node>      - show metrics for one node
Configuration: set TELEGRAM_TOKEN in .env
"""
import os
from dotenv import load_dotenv
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
from playwright.async_api import async_playwright

# Load token
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN missing")

# URL and columns
URL = "https://dashboard-devnet4.cortensor.network/stats/heatmap/rank/table"
COLUMNS = [
    "Miner", "Score", "Status", "Last Active",
    "Precommit Success %", "Precommit Counter",
    "Commit Success %", "Commit Counter", "Commit/Precommit %",
    "Prepare Success %", "Prepare Counter"
]

async def fetch_table():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL)
        await page.wait_for_selector("table tbody tr")
        rows = await page.query_selector_all("table tbody tr")
        data = []
        for r in rows:
            cells = await r.query_selector_all("td")
            texts = [(await c.inner_text()).strip() for c in cells]
            if len(texts) >= len(COLUMNS):
                data.append(texts[:len(COLUMNS)])
        await browser.close()
        return data

async def rank(update, context):
    """Send top 25 nodes"""
    data = await fetch_table()
    for i, row in enumerate(data[:25], 1):
        lines = [f"Rank {i}"]
        for name, val in zip(COLUMNS, row):
            lines.append(f"{name}: {val}")
        text = "\n".join(lines)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        await asyncio.sleep(1)

async def metric(update, context):
    """Send metrics for one node"""
    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /metric <node_address>")
        return
    node = context.args[0].lower()
    data = await fetch_table()
    for row in data:
        if row[0].lower() == node:
            lines = [f"Node: {row[0]}"] + [f"{n}: {v}" for n, v in zip(COLUMNS[1:], row[1:])]
            text = "\n".join(lines)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            return
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Node not found")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("rank", rank))
    app.add_handler(CommandHandler("metric", metric))
    print("Bot starting...")
    app.run_polling()
