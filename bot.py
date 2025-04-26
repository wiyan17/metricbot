import os import requests import logging from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

====== Konfigurasi BOT ======

TELEGRAM_TOKEN = os.getenv( "TELEGRAM_TOKEN", "8101652890:AAGkQGAopqTKlOOoU4fH7mTtDde3OgBuYtI" )

Enable logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

API Base URL untuk mengambil metric

API_BASE_URL = "https://lb-be-4.cortensor.network/reputation"

Daftar metric yang tersedia

METRICS = ["create", "commit", "prepare", "precommit"]

def escape_markdown_v2(text: str) -> str: """ Escape text so it can be safely used with MarkdownV2 formatting. """ if not isinstance(text, str): text = str(text) # karakter yang perlu di-escape di MarkdownV2 escape_chars = r'_*~`>#+-=|{}.!' return re.sub(f'([{escape_chars}])', r'\\1', text)

def fetch_metric(node_id: str, metric: str): """ Fetch a single metric for a node. Returns parsed JSON or raises error. """ url = f"{API_BASE_URL}/{node_id.strip()}/{metric}" resp = requests.get(url, timeout=10) resp.raise_for_status() # Bisa saja JSON langsung jumlah, atau object return resp.json()

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE): """ Sambutan dan instruksi penggunaan bot. """ text = ( "👋 Selamat datang!\n" "Gunakan perintah /metrics <node_id> untuk mengambil metric node.\n" "Contoh: /metrics 0xb618b27B55372AE8d304E4A10fa82E506c771c1A ) await update.message.reply_text(text, parse_mode="MarkdownV2")

async def cmd_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE): """ Handler untuk perintah /metrics <node_id> """ args = context.args if len(args) != 1: await update.message.reply_text( "⚠️ Gunakan: /metrics <node_id>", parse_mode="MarkdownV2" ) return

node_id = args[0].strip()
lines = [f"📊 *Metrics* untuk node `{escape_markdown_v2(node_id)}`:"]

for m in METRICS:
    try:
        data = fetch_metric(node_id, m)
        val = data if not isinstance(data, dict) else data.get('value', data)
        val_esc = escape_markdown_v2(val)
    except Exception as e:
        val_esc = escape_markdown_v2(f"Error: {e}")
    lines.append(f"• *{m.title()}*: `{val_esc}`")

text = "\n".join(lines)
await update.message.reply_text(text, parse_mode="MarkdownV2")

if name == "main": app = ApplicationBuilder().token(TELEGRAM_TOKEN).build() app.add_handler(CommandHandler("start", cmd_start)) app.add_handler(CommandHandler("metrics", cmd_metrics)) app.run_polling()

