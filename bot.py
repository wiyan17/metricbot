import os import re import requests import logging from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

================= CONFIGURATION =================

TELEGRAM_TOKEN = os.getenv( "TELEGRAM_TOKEN", "8101652890:AAGkQGAopqTKlOOoU4fH7mTtDde3OgBuYtI" ) logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO ) API_BASE_URL = "https://lb-be-4.cortensor.network/reputation" METRICS = ["create", "commit", "prepare", "precommit"]

def escape_markdown_v2(text): """ Escape special characters for Telegram MarkdownV2. """ if not isinstance(text, str): text = str(text) escape_chars = r'_*~`>#+-=|{}.!' return re.sub(f'([{re.escape(escape_chars)}])', r'\\1', text)

def fetch_metric(node_id, metric): """ Fetch a single metric from the API and return parsed JSON. """ url = f"{API_BASE_URL}/{node_id}/{metric}" resp = requests.get(url, timeout=10) resp.raise_for_status() return resp.json()

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE): """ Send welcome message in English with usage instructions. """ welcome_message = ( "👋 Welcome! Use the /metrics <node_id> command to fetch node metrics.\n" "Example: /metrics 0xb618b27B55372AE8d304E4A10fa82E506c771c1A" ) await update.message.reply_text( welcome_message, parse_mode="MarkdownV2" )

async def cmd_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE): """ Handle /metrics <node_id>: fetch and display all metrics. """ args = context.args if len(args) != 1: await update.message.reply_text( "⚠️ Usage: /metrics <node_id>", parse_mode="MarkdownV2" ) return

node_id = args[0].strip()
header = f"📊 Metrics for node `{escape_markdown_v2(node_id)}`:"
lines = [header]

for metric in METRICS:
    try:
        data = fetch_metric(node_id, metric)
        # If API returns dict with 'value'
        val = data.get('value') if isinstance(data, dict) and 'value' in data else data
        val_escaped = escape_markdown_v2(val)
    except Exception as e:
        val_escaped = escape_markdown_v2(f"Error: {e}")
    lines.append(f"• *{metric.title()}*: `{val_escaped}`")

await update.message.reply_text(
    "\n".join(lines),
    parse_mode="MarkdownV2"
)

if name == "main": app = ApplicationBuilder().token(TELEGRAM_TOKEN).build() app.add_handler(CommandHandler("start", cmd_start)) app.add_handler(CommandHandler("metrics", cmd_metrics)) app.run_polling()

