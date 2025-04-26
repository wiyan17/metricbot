import os
import re
import requests
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIGURATION =================
TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_TOKEN",
    "8101652890:AAGkQGAopqTKlOOoU4fH7mTtDde3OgBuYtI"
)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Base URL for reputation API
API_BASE_URL = "https://lb-be-4.cortensor.network/reputation"
# Metrics to request
METRICS = [
    "request",
    "create",
    "prepare",
    "precommit",
    "commit",
    "correctness",
    "ping",
    "global-ping"
]
# Fields to display per metric: (json_key, label)
FIELDS = [
    ("successRate", "Success rate"),
    ("point", "Point"),
    ("counter", "Counter")
]


def escape_markdown_v2(text):
    """
    Escape special characters for Telegram MarkdownV2.
    """
    if not isinstance(text, str):
        text = str(text)
    # characters to escape
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(rf"([{re.escape(escape_chars)}])", r"\\\1", text)


def fetch_metric(node_id, metric):
    """
    Fetch a single metric from the reputation API.
    Returns JSON dict or raw text or None on error.
    """
    url = f"{API_BASE_URL}/{node_id}/{metric}"
    logging.info(f"Requesting {url}")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error fetching {metric}: {e}")
        return None

    try:
        return resp.json()
    except ValueError:
        logging.warning(f"Non-JSON for {metric}: {resp.text[:100]}")
        return resp.text.strip() or None

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"Received /start from {update.effective_user.id}")
    message = (
        "👋 *Welcome!*\n"
        "Use `/metrics <node_id>` to fetch node metrics.\n"
        "Example: `/metrics 0xb618b27B55372AE8d304E4A10fa82E506c771c1A`"
    )
    await update.message.reply_text(message, parse_mode="MarkdownV2")

async def cmd_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"Received /metrics args={context.args}")
    args = context.args
    if len(args) != 1:
        await update.message.reply_text(
            "⚠️ Usage: `/metrics <node_id>`",
            parse_mode="MarkdownV2"
        )
        return

    node_id = args[0].strip()
    # Shorten node for header
    short = f"{node_id[:10]}...{node_id[-10:]}"
    lines = [f"📊 *Node metrics:* `{escape_markdown_v2(short)}`", ""]

    for metric in METRICS:
        # Display metric name
        display_name = metric.replace("-", " ").title()
        lines.append(f"*{display_name}:*")
        data = fetch_metric(node_id, metric)
        if not isinstance(data, dict):
            # No data or not dict
            for _, label in FIELDS:
                lines.append(f"{label}: N/A")
        else:
            for key, label in FIELDS:
                val = data.get(key)
                if val is None:
                    val_str = "N/A"
                else:
                    val_str = f"{val}" if key != "successRate" else f"{val}%"
                lines.append(f"{label}: {escape_markdown_v2(val_str)}")
        lines.append("")  # blank line

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")

if __name__ == "__main__":
    print("🚀 Bot is starting…")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("metrics", cmd_metrics))
    app.run_polling()
