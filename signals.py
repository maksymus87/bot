import logging
import pandas as pd
import numpy as np
from config import EMA_SHORT, EMA_LONG, RSI_PERIOD, MIN_CANDLES

logger = logging.getLogger(__name__)

def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    alpha = 2 / (period + 1)
    ema = np.zeros(len(prices))
    ema[0] = prices.iloc[0]
    
    for i in range(1, len(prices)):
        ema[i] = alpha * prices.iloc[i] + (1 - alpha) * ema[i-1]
    
    return pd.Series(ema, index=prices.index)

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    avg_gains = gains.rolling(window=period).mean()
    avg_losses = losses.rolling(window=period).mean()
    
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def check_signal(df):
    """
    Analyze price data and generate trading signals based on technical indicators.
    
    Signal conditions:
    - LONG: EMA8 crosses above EMA21, RSI > 50, MACD > 0
    - SHORT: EMA8 crosses below EMA21, RSI < 50, MACD < 0
    
    Args:
        df (pd.DataFrame): OHLCV data
        
    Returns:
        str: 'LONG', 'SHORT', or None
    """
    if df is None or len(df) < MIN_CANDLES:
        logger.warning(f"Insufficient data for analysis: {len(df) if df is not None else 0} candles")
        return None
    
    try:
        # Calculate technical indicators
        df = df.copy()
        
        # Exponential Moving Averages
        df["EMA8"] = calculate_ema(df["close"], EMA_SHORT)
        df["EMA21"] = calculate_ema(df["close"], EMA_LONG)
        
        # RSI (Relative Strength Index)
        df["RSI"] = calculate_rsi(df["close"], RSI_PERIOD)
        
        # MACD (Moving Average Convergence Divergence)
        macd_line, signal_line, histogram = calculate_macd(df["close"])
        df["MACD_12_26_9"] = macd_line
        df["MACDs_12_26_9"] = signal_line
        df["MACDh_12_26_9"] = histogram
        
        # Get current and previous values
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Check for missing values
        required_cols = ["EMA8", "EMA21", "RSI", "MACD_12_26_9"]
        if any(pd.isna(current[col]) or pd.isna(previous[col]) for col in required_cols):
            logger.warning("Missing indicator values, skipping signal check")
            return None
        
        # Detect EMA crossovers
        ema8_current = current["EMA8"]
        ema8_previous = previous["EMA8"]
        ema21_current = current["EMA21"]
        ema21_previous = previous["EMA21"]
        
        cross_up = (ema8_previous <= ema21_previous) and (ema8_current > ema21_current)
        cross_down = (ema8_previous >= ema21_previous) and (ema8_current < ema21_current)
        
        # Get indicator values
        rsi = current["RSI"]
        macd_value = current["MACD_12_26_9"]
        
        # Generate signals
        if cross_up and rsi > 50 and macd_value > 0:
            logger.info(f"LONG signal detected - RSI: {rsi:.2f}, MACD: {macd_value:.6f}")
            return "LONG"
        elif cross_down and rsi < 50 and macd_value < 0:
            logger.info(f"SHORT signal detected - RSI: {rsi:.2f}, MACD: {macd_value:.6f}")
            return "SHORT"
        
        return None
        
    except Exception as e:
        logger.error(f"Error in signal analysis: {e}")
        return None

def format_signal_message(symbol, interval, signal, current_data=None):
    """
    Format a trading signal message for Telegram.
    
    Args:
        symbol (str): Trading pair symbol
        interval (str): Timeframe
        signal (str): 'LONG' or 'SHORT'
        current_data (pd.Series, optional): Current candle data for additional info
        
    Returns:
        str: Formatted message
    """
    emoji = "📈" if signal == "LONG" else "📉"
    direction = "вверх" if signal == "LONG" else "вниз"
    
    message = f"{emoji} Сигнал на {signal}\n"
    message += f"Монета: {symbol}\n"
    message += f"Таймфрейм: {interval}\n\n"
    
    if signal == "LONG":
        message += "✅ EMA8 пересёк EMA21 вверх\n"
        message += "✅ RSI > 50\n"
        message += "✅ MACD в положительной зоне"
    else:
        message += "✅ EMA8 пересёк EMA21 вниз\n"
        message += "✅ RSI < 50\n"
        message += "✅ MACD в отрицательной зоне"
    
    # Add current price if available
    if current_data is not None and not pd.isna(current_data.get("close")):
        price = current_data["close"]
        message += f"\n\n💰 Текущая цена: ${price:.6f}"
    
    return message
