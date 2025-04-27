#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram bot using Playwright to scrape Cortensor heatmap rank table.

Commands:
/start     \- show help
/rank      \- fetch top 25 nodes
/metric    \- lookup a single node; optionally specify a metric:
             /metric <node_address> <metric_name>

Configuration via .env (TELEGRAM_TOKEN).
"""
import os
import re
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright

# Load environment variables
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
MAX_RANK = 25
SEND_INTERVAL = 1.0  # seconds between messages

# MarkdownV2 escape helper
def escape_md(text: str) -> str:
    if text is None:
        return ""
    text = str(text)
    return re.sub(r'([_\*\[\]\(\)~`>\#+\-=\|\{\}\.\!])', r'\\\1', text)

async def scrape_table() -> list[list[str]]:
    """
    Scrapes the entire rank table and returns rows of cell texts.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(TABLE_URL, timeout=60000)
        await page.wait_for_selector("table tbody tr", timeout=60000)
        row_elems = await page.query_selector_all("table tbody tr")
        data = []
        for row in row_elems:
            cells = await row.query_selector_all("td")
            texts = [ (await cell.inner_text()).strip() for cell in cells ]
            if len(texts) >= len(COLUMNS):
                data.append(texts[:len(COLUMNS)])
        await browser.close()
        return data

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help text"""
    text = (
        "👋 *Cortensor Metrics Bot*\n"
        "/rank \- top 25 nodes\n"
        "/metric <node_address> [metric_name] \- single node lookup\n"
        "Example: /metric 0x123... 'Precommit Success %'"
    )
    await update.message.reply_text(text, parse_mode="MarkdownV2")

async def cmd_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send top 25 node metrics one by one"""
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "⏳ Fetching top 25 nodes...", parse_mode=None)
    try:
        table = await scrape_table()
    except Exception as e:
        return await context.bot.send_message(chat_id, f"❌ Scrape error: {e}")

    for i, row in enumerate(table[:MAX_RANK], start=1):
        lines = [f"📊 *Rank {i}*"]
        for col_name, cell in zip(COLUMNS, row):
            lines.append(f"*{escape_md(col_name)}*: `{escape_md(cell)}`")
        await context.bot.send_message(chat_id, "\n".join(lines), parse_mode="MarkdownV2")
        await asyncio.sleep(SEND_INTERVAL)

async def cmd_metric(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lookup a single node; optional metric name"""
    chat_id = update.effective_chat.id
    args = context.args
    if len(args) < 1:
        return await context.bot.send_message(chat_id, "⚠️ Usage: /metric <node_address> [metric_name]")

    node = args[0].strip().lower()
    metric_name = " ".join(args[1:]).strip() if len(args) > 1 else None

    try:
        table = await scrape_table()
    except Exception as e:
        return await context.bot.send_message(chat_id, f"❌ Scrape error: {e}")

    for row in table:
        if row[0].strip().lower() == node:
            if metric_name:
                try:
                    idx = next(i for i, col in enumerate(COLUMNS) if col.lower() == metric_name.lower())
                except StopIteration:
                    available = ", ".join(COLUMNS)
                    return await context.bot.send_message(
                        chat_id,
                        f"❓ Unknown metric '{escape_md(metric_name)}'. Available: {escape_md(available)}",
                    )
                value = row[idx]
                return await context.bot.send_message(
                    chat_id,
                    f"📊 *{escape_md(COLUMNS[idx])}* for node `{escape_md(node)}`: `{escape_md(value)}`",
                    parse_mode="MarkdownV2"
                )
            else:
                lines = [f"📊 *Node*: `{escape_md(node)}`"]
                for col_name, cell in zip(COLUMNS, row):
                    lines.append(f"*{escape_md(col_name)}*: `{escape_md(cell)}`")
                return await context.bot.send_message(chat_id, "\n".join(lines), parse_mode="MarkdownV2")

    await context.bot.send_message(chat_id, "❓ Node not found.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("rank", cmd_rank))
    app.add_handler(CommandHandler("metric", cmd_metric))
    print("Bot is starting…")
    app.run_polling()
