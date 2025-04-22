import os import requests from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

Ambil token dan chat ID dari environment or defaults

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8101652890:AAGkQGAopqTKlOOoU4fH7mTtDde3OgBuYtI") CHAT_ID = os.getenv("CHAT_ID", "611044696") METRICS = ["Precommit", "Commit", "Create", "Prepare"] BASE_URL = "https://dashboard-devnet4.cortensor.network/stats/node/{node_id}?metric={metric}"

def fetch_latest_metric(node_id: str, metric: str): """ GET <BASE_URL>?metric=<metric>, parse JSON, return nilai terakhir. """ url = BASE_URL.format(node_id=node_id.strip(), metric=metric) resp = requests.get(url, timeout=10) resp.raise_for_status() js = resp.json()

arr = js.get("data", [])
if not arr:
    return None
last = arr[-1]
return last.get("value", last)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "👋 Selamat datang! Gunakan perintah /metrics <node_id> untuk mengambil metric node. Contoh: /metrics 0x1234... , parse_mode="Markdown" )

async def cmd_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE): args = context.args if not args: await update.message.reply_text( "⚠️ Harap sertakan Node ID. Contoh: /metrics 0x1234...", parse_mode="Markdown" ) return

for node in args:
    lines = [f"📊 Metrics untuk node `{node.strip()}`:"]
    for m in METRICS:
        try:
            val = fetch_latest_metric(node, m)
        except Exception as e:
            val = f"Error: {e}"
        lines.append(f"• {m}: {val}")
    text = "\n".join(lines)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode="Markdown"
    )

async def main(): app = ApplicationBuilder().token(TELEGRAM_TOKEN).build() app.add_handler(CommandHandler("start", cmd_start)) app.add_handler(CommandHandler("metrics", cmd_metrics))

app.run_polling()

if name == "main": import asyncio asyncio.run(main())

