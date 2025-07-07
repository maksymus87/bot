import logging
import requests
import pandas as pd
from config import OKX_BASE_URL

logger = logging.getLogger(__name__)

def get_ohlcv(symbol, interval="15m", limit=100):
    """
    Fetch OHLCV data from OKX API.
    
    Args:
        symbol (str): Trading pair symbol (e.g., 'BTC-USDT')
        interval (str): Timeframe (1m, 5m, 15m, etc.)
        limit (int): Number of candles to fetch
        
    Returns:
        pd.DataFrame: OHLCV data with columns [timestamp, open, high, low, close, volume, turnover]
        None: If API call fails
    """
    url = f"{OKX_BASE_URL}/market/history-candles"
    params = {
        "instId": symbol,
        "bar": interval,
        "limit": limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != "0":
            logger.error(f"OKX API error for {symbol}: {data.get('msg')}")
            return None
            
        if not data.get("data"):
            logger.warning(f"No data returned for {symbol}")
            return None
            
        # Create DataFrame from API response
        # OKX API returns: [timestamp, open, high, low, close, volume, volumeCcy, volumeCcyQuote, confirm]
        df = pd.DataFrame(
            data["data"], 
            columns=["timestamp", "open", "high", "low", "close", "volume", "volumeCcy", "volumeCcyQuote", "confirm"]
        )
        
        # Keep only the columns we need
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        
        # Convert price and volume columns to float
        numeric_columns = ["open", "high", "low", "close", "volume"]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
        
        # Sort by timestamp (oldest first)
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"Successfully fetched {len(df)} candles for {symbol}")
        return df
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching data for {symbol}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching data for {symbol}: {e}")
        return None
