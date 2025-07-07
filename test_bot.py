#!/usr/bin/env python3
"""
Test script for SignalMaxBot components
"""
import logging
from bot.api import get_ohlcv
from bot.signals import check_signal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api():
    """Test OKX API connection"""
    logger.info("Testing OKX API connection...")
    df = get_ohlcv('BTC-USDT', '15m', 50)
    if df is not None:
        logger.info(f"✓ Successfully fetched {len(df)} candles for BTC-USDT")
        logger.info(f"Latest price: ${df.iloc[-1]['close']:.2f}")
        return df
    else:
        logger.error("✗ Failed to fetch data")
        return None

def test_signals(df):
    """Test signal analysis"""
    if df is None:
        return None
    
    logger.info("Testing signal analysis...")
    signal = check_signal(df)
    if signal:
        logger.info(f"✓ Signal detected: {signal}")
    else:
        logger.info("✓ No signal at this time")
    return signal

if __name__ == "__main__":
    # Test API
    data = test_api()
    
    # Test signals
    test_signals(data)
    
    logger.info("Test completed successfully!")