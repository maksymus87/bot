import os

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")

# API configuration
OKX_BASE_URL = "https://www.okx.com/api/v5"

# Trading configuration
DEFAULT_COINS = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "HBAR-USDT", "DOGE-USDT", "H-USDT", "SOON-USDT"]
DEFAULT_INTERVAL = "15m"
ALLOWED_INTERVALS = ["1m", "5m", "15m"]
MONITOR_SLEEP_SECONDS = 60

# Technical analysis parameters
EMA_SHORT = 8
EMA_LONG = 21
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
MIN_CANDLES = 30
