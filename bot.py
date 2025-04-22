import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Ambil konfigurasi dari environment variables atau pakai default user-provided
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8101652890:AAGkQGAopqTKlOOoU4fH7mTtDde3OgBuYtI")
CHAT_ID = os.getenv("CHAT_ID", "611044696")  # ID Telegram Anda
# NODE_IDS: daftar node ID dipisah koma, misalnya "0xabc,0xdef"
NODE_IDS = os.getenv("NODE_IDS", "0xdb9f33703aa0d90dfc56c96b2263bacf383db1c7").split(",")
METRICS = ["Precommit", "Commit", "Create", "Prepare"]
BASE_URL = "https://dashboard-devnet4.cortensor.network/stats/node/{node_id}?metric={metric}"


def fetch_latest_metric(node_id: str, metric: str):
    """
    GET <BASE_URL>?metric=<metric>, parse JSON, return nilai terakhir.
    """
    url = BASE_URL.format(node_id=node_id.strip(), metric=metric)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    js = resp.json()

    arr = js.get("data", [])
    if not arr:
        return None
    last = arr[-1]
    return last.get("value", last)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Bot monitoring node siap! Metrics akan dikirim setiap interval."
    )


async def job_monitor(context: ContextTypes.DEFAULT_TYPE):
    for node in NODE_IDS:
        lines = [f"📊 Metrics untuk node `{node.strip()}`:"]
        for m in METRICS:
            try:
                val = fetch_latest_metric(node, m)
            except Exception as e:
                val = f"Error: {e}"
            lines.append(f"• {m}: {val}")
        text = "\n".join(lines)
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode="Markdown"
        )


def main():
    # Inisialisasi bot dan job queue
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))

    # Schedule polling tiap 5 menit (300 detik)
    jq = app.job_queue
    jq.run_repeating(job_monitor, interval=300, first=10)

    app.run_polling()


if __name__ == "__main__":
    main()
