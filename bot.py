import os
import requests
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== Konfigurasi =====
TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_TOKEN",
    "8101652890:AAGkQGAopqTKlOOoU4fH7mTtDde3OgBuYtI"
)
logging.basicConfig(level=logging.INFO)


def fetch_all_metrics(node_id: str):
    """
    Ambil semua metrik sekaligus dari endpoint node.
    """
    url = f"https://dashboard-devnet4.cortensor.network/stats/node/{node_id.strip()}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    js = resp.json()

    result = {}
    for item in js.get("data", []):
        metric_name = item.get("metric")
        values = item.get("values", [])
        if values:
            result[metric_name] = values[-1].get("value", "N/A")
        else:
            result[metric_name] = "N/A"
    return result


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Selamat datang! Gunakan perintah `/metrics <node_id>` untuk mengambil metric node.\n"
        "Contoh: `/metrics 0x9344ed8328cf501f7a8d87231a2cb4ebd1207f2e`",
        parse_mode="Markdown"
    )


async def cmd_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ Harap sertakan Node ID.\nContoh: `/metrics 0xabc...`",
            parse_mode="Markdown"
        )
        return

    for node in args:
        try:
            metrics = fetch_all_metrics(node)
            lines = [f"📊 Metrics untuk node `{node.strip()}`:"]
            for m, val in metrics.items():
                lines.append(f"• {m}: {val}")
            await update.message.reply_text(
                "\n".join(lines),
                parse_mode="Markdown"
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Gagal ambil data dari node `{node}`:\n`{e}`",
                parse_mode="Markdown"
            )


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("metrics", cmd_metrics))
    app.run_polling()