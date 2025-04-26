import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = "8101652890:AAGkQGAopqTKlOOoU4fH7mTtDde3OgBuYtI"
USER_ID = 611044696  # Ganti dengan ID kamu

API_BASE_URL = "https://lb-be-4.cortensor.network/reputation"

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Selamat datang! Gunakan perintah /metrics <node_id> untuk ambil metrik. Contoh:\n"
        "`/metrics 0xb618b27B55372AE8d304E4A10fa82E506c771c1A`",
        parse_mode="Markdown"
    )

async def cmd_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Format salah! Contoh: /metrics <node_id>")
        return

    node_id = context.args[0]
    metrics = ["create", "commit", "prepare", "precommit"]
    results = []

    for metric in metrics:
        url = f"{API_BASE_URL}/{node_id}/{metric}"
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            results.append(f"*{metric.title()}*: `{data}`")
        except Exception as e:
            results.append(f"*{metric.title()}*: Error ambil data ({e})")

    response = "\n".join(results)
    await update.message.reply_text(response, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("metrics", cmd_metrics))
    app.run_polling()

if __name__ == "__main__":
    main()