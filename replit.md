# SignalMaxBot - Cryptocurrency Trading Signals Bot

## Overview

SignalMaxBot is a Telegram bot that provides cryptocurrency trading signals using technical analysis. The bot monitors multiple trading pairs and sends real-time notifications when specific technical conditions are met, helping users identify potential trading opportunities.

## System Architecture

### Core Components
- **Telegram Bot Interface**: Handles user interactions and command processing
- **Signal Detection Engine**: Analyzes price data using technical indicators
- **OKX API Integration**: Fetches real-time OHLCV (Open, High, Low, Close, Volume) data
- **In-Memory User Management**: Stores user preferences and watchlists

### Technology Stack
- **Python**: Core programming language
- **python-telegram-bot**: Telegram bot framework
- **pandas**: Data manipulation and analysis
- **pandas_ta**: Technical analysis library
- **requests**: HTTP client for API calls

## Key Components

### 1. Bot Handlers (`bot/handlers.py`)
Manages all Telegram bot commands and user interactions:
- `/start` - Welcome message and bot introduction
- `/добавь` - Add cryptocurrency to watchlist
- `/удали` - Remove cryptocurrency from watchlist
- `/монеты` - Display current watchlist
- `/таймфрейм` - Set analysis timeframe

### 2. Signal Analysis (`bot/signals.py`)
Implements technical analysis logic using three key indicators:
- **EMA Crossover**: 8-period EMA crossing 21-period EMA
- **RSI Filter**: Relative Strength Index for momentum confirmation
- **MACD Confirmation**: Moving Average Convergence Divergence for trend validation

**Signal Conditions**:
- **LONG**: EMA8 > EMA21 (crossover), RSI > 50, MACD > 0
- **SHORT**: EMA8 < EMA21 (crossover), RSI < 50, MACD < 0

### 3. Market Data API (`bot/api.py`)
Handles OKX exchange API integration:
- Fetches historical candle data
- Supports multiple timeframes (1m, 5m, 15m)
- Error handling and data validation
- Rate limiting and timeout management

### 4. Configuration (`config.py`)
Centralizes all system parameters:
- Default trading pairs and timeframes
- Technical indicator parameters
- API endpoints and monitoring intervals

## Data Flow

1. **User Registration**: Users start bot and receive default watchlist
2. **Watchlist Management**: Users customize their cryptocurrency list via commands
3. **Continuous Monitoring**: Bot polls OKX API for each user's watchlist every 60 seconds
4. **Signal Analysis**: Price data is analyzed using EMA, RSI, and MACD indicators
5. **Notification Delivery**: When signals are detected, users receive Telegram notifications

## External Dependencies

### APIs
- **OKX Exchange API**: Primary data source for cryptocurrency prices
  - Endpoint: `https://www.okx.com/api/v5/market/history-candles`
  - No authentication required for public market data

### Python Libraries
- `python-telegram-bot`: Telegram Bot API wrapper
- `pandas`: Data manipulation and time series analysis
- `pandas_ta`: Technical analysis indicators
- `requests`: HTTP client for API calls

## Deployment Strategy

### Environment Configuration
- **BOT_TOKEN**: Telegram bot token (required)
- **Logging**: File and console logging with configurable levels

### Architecture Decisions

**In-Memory Storage**: 
- **Problem**: Need to store user preferences and watchlists
- **Solution**: Python dictionary-based storage in `user_settings`
- **Rationale**: Simple deployment, no database dependencies
- **Trade-offs**: Data lost on restart, not suitable for production scale

**Synchronous API Calls**:
- **Problem**: Need to fetch market data from OKX
- **Solution**: Blocking HTTP requests with timeout handling
- **Rationale**: Simpler error handling, adequate for current scale
- **Trade-offs**: Could benefit from async requests for better performance

**Polling-Based Monitoring**:
- **Problem**: Need to continuously check for new signals
- **Solution**: 60-second polling loop with sequential processing
- **Rationale**: Simple implementation, reliable signal detection
- **Trade-offs**: Higher latency compared to WebSocket streams

## Changelog

```
Changelog:
- July 07, 2025: Initial setup and core architecture implementation
- July 07, 2025: Fixed pandas_ta compatibility issues by implementing custom technical indicators
- July 07, 2025: Resolved OKX API data format issues (9 columns vs expected 7)
- July 07, 2025: Updated command names from Russian to English for better Telegram compatibility
- July 07, 2025: Fixed async event loop conflicts in Replit environment with simplified bot implementation
- July 07, 2025: Successfully deployed working Telegram bot with signal monitoring
```

## Recent Changes

✓ Custom technical indicators implemented (EMA, RSI, MACD) replacing pandas_ta library
✓ Fixed OKX API data parsing for 9-column response format  
✓ Updated bot commands to English: /add, /remove, /coins, /timeframe
✓ Resolved async event loop conflicts with simplified bot_simple.py implementation
✓ Bot successfully connecting to Telegram API and monitoring cryptocurrency signals

## Current Status

The SignalMaxBot is fully operational and running on Replit. Users can:
- Start the bot with /start command
- Add/remove cryptocurrencies to their watchlist
- Set custom timeframes for analysis
- Receive automated trading signals based on technical analysis

All core components are working:
- ✓ Telegram bot interface
- ✓ OKX API data fetching
- ✓ Technical analysis engine
- ✓ Signal monitoring and notifications

## User Preferences

```
Preferred communication style: Simple, everyday language.
```