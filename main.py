
"""
Self‑contained Telegram bot that keeps track of users’ watch‑lists and
sends a (dummy) LONG / SHORT signal based on a very simple moving‑average
rule.  Designed for quick deployment to Render with python‑telegram‑bot 20.x

‼️  IMPORTANT
—————————
* Replace the dummy check_signal / get_ohlcv implementations with real
  market‑data logic once you are ready.
* Set the BOT_TOKEN environment variable in Render.
"""

import os
import asyncio
import logging
from collections import defaultdict
from datetime import datetime

import numpy as np
import pandas as pd
from telegram import Update
from telegram.ext import (
    Application, ApplicationBuilder,
    CommandHandler, ContextTypes
)

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")               # Telegram token from BotFather
MONITOR_SLEEP_SECONDS = int(os.getenv("MONITOR_SLEEP_SECONDS", "60"))

# -------------------------------------------------------------------------
# In‑memory user settings:
# {chat_id: {"coins": list[str], "interval": str, "last_signals": {symbol: str}}}
# -------------------------------------------------------------------------
user_settings: dict[int, dict] = defaultdict(
    lambda: {"coins": [], "interval": "15m", "last_signals": {}}
)

# -------------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("bot.log")]
)
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Dummy market‑data + signal logic
# -------------------------------------------------------------------------
def get_ohlcv(symbol: str, interval: str) -> pd.DataFrame | None:
    """
    ⚠️  DUMMY implementation!

    Replace with real OHLCV download (e.g. using ccxt, OKX REST, etc.).
    Here we just generate a fake price series so the bot can run.
    """
    now = pd.Timestamp.utcnow().floor("min")
    times = pd.date_range(end=now, periods=100, freq="1min")
    prices = np.cumsum(np.random.randn(len(times))) + 100
    df = pd.DataFrame({"close": prices}, index=times)
    return df


def check_signal(df: pd.DataFrame) -> str | None:
    """
    Very naive signal:
    * LONG  if last close > SMA(8)  and SMA(8)  > SMA(21)
    * SHORT if last close < SMA(8)  and SMA(8)  < SMA(21)
    Otherwise returns None.
    """
    if df is None or "close" not in df.columns:
        return None

    sma8 = df["close"].rolling(8).mean()
    sma21 = df["close"].rolling(21).mean()
    last_close = df["close"].iloc[-1]
    last_sma8 = sma8.iloc[-1]
    last_sma21 = sma21.iloc[-1]

    if last_close > last_sma8 > last_sma21:
        return "LONG"
    if last_close < last_sma8 < last_sma21:
        return "SHORT"
    return None


async def send_signal(app: Application, chat_id: int, symbol: str, interval: str, signal: str):
    """
    Sends a nicely formatted signal message to the user.
    """
    arrow = "📈" if signal == "LONG" else "📉"
    txt = (
        f"{arrow} <b>Сигнал на {signal}</b>\n"
        f"Монета: <code>{symbol}</code>\n"
        f"Тайм‑фрейм: {interval}\n"
        f"Время: {datetime.utcnow().strftime('%Y‑%m‑%d %H:%M UTC')}"
    )
    await app.bot.send_message(chat_id, txt, parse_mode="HTML")


# -------------------------------------------------------------------------
# Command Handlers
# -------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "Привет! Отправь /add <COIN‑USDT> чтобы добавить монету в отслеживание. "
        "Команды: /coins, /remove, /timeframe."
    )
    logger.info(f"/start by {chat_id}")


async def show_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    coins = user_settings[chat_id]["coins"]
    if coins:
        await update.message.reply_text("Отслеживаемые монеты:\n" + "\n".join(coins))
    else:
        await update.message.reply_text("Список монет пуст. Используй /add чтобы добавить.")

async def add_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        await update.message.reply_text("Пример: /add DOGE-USDT")
        return
    symbol = args[0].upper()
    settings = user_settings[chat_id]
    if symbol not in settings["coins"]:
        settings["coins"].append(symbol)
        await update.message.reply_text(f"✅ {symbol} добавлен.")
    else:
        await update.message.reply_text(f"{symbol} уже в списке.")


async def remove_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        await update.message.reply_text("Пример: /remove DOGE-USDT")
        return
    symbol = args[0].upper()
    settings = user_settings[chat_id]
    if symbol in settings["coins"]:
        settings["coins"].remove(symbol)
        settings["last_signals"].pop(symbol, None)
        await update.message.reply_text(f"❌ {symbol} удалён.")
    else:
        await update.message.reply_text(f"{symbol} нет в списке.")


async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        await update.message.reply_text("Пример: /timeframe 15m")
        return
    interval = args[0]
    user_settings[chat_id]["interval"] = interval
    await update.message.reply_text(f"Тайм‑фрейм установлен: {interval}")


# -------------------------------------------------------------------------
# Background task: monitor signals
# -------------------------------------------------------------------------
async def monitor_signals(app: Application):
    logger.info("Started signal monitoring")
    while True:
        try:
            for chat_id, settings in list(user_settings.items()):
                coins = settings["coins"]
                interval = settings["interval"]
                for symbol in coins:
                    df = get_ohlcv(symbol, interval)
                    signal = check_signal(df)
                    last_signal = settings["last_signals"].get(symbol)
                    if signal and signal != last_signal:
                        await send_signal(app, chat_id, symbol, interval, signal)
                        settings["last_signals"][symbol] = signal
                        logger.info(f"Sent {signal} for {symbol} to {chat_id}")
            await asyncio.sleep(MONITOR_SLEEP_SECONDS)
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")
            await asyncio.sleep(MONITOR_SLEEP_SECONDS)


# -------------------------------------------------------------------------
# Main entry
# -------------------------------------------------------------------------
async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable not set!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("coins", show_coins))
    app.add_handler(CommandHandler("add", add_coin))
    app.add_handler(CommandHandler("remove", remove_coin))
    app.add_handler(CommandHandler("timeframe", set_interval))

    # background task
    asyncio.create_task(monitor_signals(app))

    logger.info("Bot started")
    await app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
