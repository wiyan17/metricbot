# monitor_bot.py
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 2) Konfigurasi lewat environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")    # token dari BotFather
CHAT_ID         = os.getenv("CHAT_ID")          # chat_id target (bisa grup atau personal)
NODE_ID         = os.getenv(
    "NODE_ID",
    "0xdb9f33703aa0d90dfc56c96b2263bacf383db1c7"
)
METRICS = ["Precommit", "Commit", "Create", "Prepare"]
BASE_URL = "https://dashboard-devnet4.cortensor.network/stats/node/{node_id}?metric={metric}"

def fetch_latest_metric(node_id: str, metric: str):
    """
    GET <BASE_URL>?metric=<metric>, 
    parse JSON, return nilai terakhir (assume data['data'] is list of points).
    """
    url = BASE_URL.format(node_id=node_id, metric=metric)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    js = resp.json()

    # contoh struktur: {"data": [{"timestamp":..., "value": ...}, ...]}
    arr = js.get("data", [])
    if not arr:
        return None
    last = arr[-1]
    # bisa perlu disesuaikan jika struktur berbeda
    return last.get("value") or last

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot monitoring node siap berjalan! Anda akan menerima metric setiap 5 menit.")

async def job_monitor(context: ContextTypes.DEFAULT_TYPE):
    lines = [f"📊 Metrics untuk node `{NODE_ID}`:"]
    for m in METRICS:
        try:
            val = fetch_latest_metric(NODE_ID, m)
        except Exception as e:
            val = f"Error: {e}"
        lines.append(f"• {m}: {val}")
    text = "\n".join(lines)
    await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")

def main():
    # 3) Bangun aplikasi dan daftarkan handler
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))

    # 4) Schedule polling tiap 300 detik (5 menit), mulai 10 detik setelah run
    jq = app.job_queue
    jq.run_repeating(job_monitor, interval=300, first=10)

    app.run_polling()

if __name__ == "__main__":
    main()
