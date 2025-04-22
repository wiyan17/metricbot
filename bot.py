import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ====== Konfigurasi BOT ======
TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_TOKEN",
    "8101652890:AAGkQGAopqTKlOOoU4fH7mTtDde3OgBuYtI"
)
CHAT_ID = os.getenv("CHAT_ID", "611044696")
METRICS = ["Precommit", "Commit", "Create", "Prepare"]
BASE_URL = (
    "https://dashboard-devnet4.cortensor.network/stats/node/{node_id}?metric={metric}"
)

def fetch_latest_metric(node_id: str, metric: str):
    """
    Ambil data JSON metric dari endpoint dan kembalikan nilai terbaru.
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
    """
    Sambutan dan instruksi penggunaan.
    """
    await update.message.reply_text(
        "👋 Selamat datang! Gunakan perintah `/metrics <node_id>` untuk mengambil metric node.\n"
        "Contoh: `/metrics 0xdb9f33703aa0d90dfc56c96b2263bacf383db1c7`",
        parse_mode="Markdown"
    )

async def cmd_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /metrics <node_id1> <node_id2> ...
    """
    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ Harap sertakan minimal satu Node ID.\n"
            "Contoh: `/metrics 0xdb9f... 0xabc...`",
            parse_mode="Markdown"
        )
        return

    for node in args:
        lines = [f"📊 Metrics untuk node `{node.strip()}`:"]
        for m in METRICS:
            try:
                val = fetch_latest_metric(node, m)
            except Exception as e:
                val = f"Error: {e}"
            lines.append(f"• {m}: {val}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="\n".join(lines),
            parse_mode="Markdown"
        )

if __name__ == "__main__":
    # Inisialisasi dan jalankan bot
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("metrics", cmd_metrics))
    app.run_polling()