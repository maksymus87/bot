import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import DEFAULT_COINS, DEFAULT_INTERVAL, ALLOWED_INTERVALS

logger = logging.getLogger(__name__)

# In-memory storage for user settings
user_settings = {}

def get_user_settings(chat_id):
    """Get or create user settings."""
    if chat_id not in user_settings:
        user_settings[chat_id] = {
            "coins": DEFAULT_COINS.copy(),
            "interval": DEFAULT_INTERVAL,
            "last_signals": {}
        }
    return user_settings[chat_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    chat_id = update.effective_chat.id
    settings = get_user_settings(chat_id)
    
    welcome_message = (
        "👋 Привет! Я SignalMaxBot.\n\n"
        "Я помогаю отслеживать торговые сигналы криптовалют "
        "используя технический анализ (EMA, RSI, MACD).\n\n"
        "📋 Доступные команды:\n"
        "/add SYMBOL - добавить монету для отслеживания\n"
        "/remove SYMBOL - удалить монету из списка\n"
        "/coins - показать список отслеживаемых монет\n"
        "/timeframe INTERVAL - установить таймфрейм (1m, 5m, 15m)\n"
        "/start - показать это сообщение\n\n"
        f"⚙️ Текущие настройки:\n"
        f"Таймфрейм: {settings['interval']}\n"
        f"Монет в списке: {len(settings['coins'])}"
    )
    
    await update.message.reply_text(welcome_message)
    logger.info(f"User {chat_id} started the bot")

async def show_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /coins command - show user's coin list."""
    chat_id = update.effective_chat.id
    settings = get_user_settings(chat_id)
    coins = settings["coins"]
    
    if not coins:
        message = "📝 Ты не отслеживаешь ни одной монеты.\n\nИспользуй /add SYMBOL чтобы добавить монету."
    else:
        message = f"📊 Отслеживаемые монеты ({len(coins)}):\n\n"
        for i, coin in enumerate(coins, 1):
            message += f"{i}. {coin}\n"
        message += f"\n⏱ Таймфрейм: {settings['interval']}"
    
    await update.message.reply_text(message)
    logger.info(f"User {chat_id} requested coin list")

async def add_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add command - add coin to watchlist."""
    chat_id = update.effective_chat.id
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Неправильное использование команды.\n\n"
            "Правильный формат: /add SYMBOL\n"
            "Пример: /add BTC-USDT"
        )
        return
    
    symbol = context.args[0].upper()
    settings = get_user_settings(chat_id)
    
    if symbol in settings["coins"]:
        await update.message.reply_text(f"⚠️ Монета {symbol} уже в списке отслеживания.")
    else:
        settings["coins"].append(symbol)
        await update.message.reply_text(
            f"✅ Монета {symbol} добавлена в список отслеживания.\n\n"
            f"Всего монет: {len(settings['coins'])}"
        )
        logger.info(f"User {chat_id} added coin {symbol}")

async def remove_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remove command - remove coin from watchlist."""
    chat_id = update.effective_chat.id
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Неправильное использование команды.\n\n"
            "Правильный формат: /remove SYMBOL\n"
            "Пример: /remove BTC-USDT"
        )
        return
    
    symbol = context.args[0].upper()
    settings = get_user_settings(chat_id)
    
    if symbol not in settings["coins"]:
        await update.message.reply_text(f"⚠️ Монеты {symbol} нет в списке отслеживания.")
    else:
        settings["coins"].remove(symbol)
        # Clear last signal for removed coin
        settings["last_signals"].pop(symbol, None)
        await update.message.reply_text(
            f"✅ Монета {symbol} удалена из списка отслеживания.\n\n"
            f"Осталось монет: {len(settings['coins'])}"
        )
        logger.info(f"User {chat_id} removed coin {symbol}")

async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /timeframe command - set timeframe."""
    chat_id = update.effective_chat.id
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Неправильное использование команды.\n\n"
            "Правильный формат: /timeframe INTERVAL\n"
            f"Доступные таймфреймы: {', '.join(ALLOWED_INTERVALS)}\n"
            "Пример: /timeframe 15m"
        )
        return
    
    interval = context.args[0].lower()
    
    if interval not in ALLOWED_INTERVALS:
        await update.message.reply_text(
            f"❌ Недопустимый таймфрейм: {interval}\n\n"
            f"Доступные варианты: {', '.join(ALLOWED_INTERVALS)}"
        )
        return
    
    settings = get_user_settings(chat_id)
    old_interval = settings["interval"]
    settings["interval"] = interval
    
    # Clear last signals when changing timeframe
    settings["last_signals"].clear()
    
    await update.message.reply_text(
        f"✅ Таймфрейм изменён с {old_interval} на {interval}\n\n"
        "История сигналов очищена для корректной работы с новым таймфреймом."
    )
    logger.info(f"User {chat_id} changed interval from {old_interval} to {interval}")

async def send_signal(app, chat_id, symbol, interval, signal):
    """Send trading signal to user."""
    try:
        from bot.signals import format_signal_message
        message = format_signal_message(symbol, interval, signal)
        await app.bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Sent {signal} signal for {symbol} to user {chat_id}")
    except Exception as e:
        logger.error(f"Failed to send signal to user {chat_id}: {e}")
