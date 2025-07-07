import logging
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
from bot.handlers import (
    start, show_coins, add_coin, remove_coin, set_interval, 
    send_signal, user_settings
)
from bot.api import get_ohlcv
from bot.signals import check_signal
from config import BOT_TOKEN, MONITOR_SLEEP_SECONDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

async def monitor_signals(app):
    """
    Continuously monitor trading signals for all users.
    
    This function runs in a loop, checking each user's watchlist
    for new trading signals and sending notifications when found.
    """
    logger.info("Starting signal monitoring loop")
    
    while True:
        try:
            # Process each user's settings
            for chat_id, settings in user_settings.items():
                coins = settings.get("coins", [])
                interval = settings.get("interval", "15m")
                
                if not coins:
                    continue
                
                logger.debug(f"Checking signals for user {chat_id}: {len(coins)} coins")
                
                # Check each coin in user's watchlist
                for symbol in coins:
                    try:
                        # Fetch OHLCV data
                        df = get_ohlcv(symbol, interval)
                        if df is None:
                            logger.warning(f"No data available for {symbol}")
                            continue
                        
                        # Analyze for trading signals
                        signal = check_signal(df)
                        if signal is None:
                            continue
                        
                        # Check if this is a new signal (different from last)
                        last_signal = settings["last_signals"].get(symbol)
                        if signal != last_signal:
                            # Send notification to user
                            await send_signal(app, chat_id, symbol, interval, signal)
                            
                            # Update last signal to prevent duplicates
                            settings["last_signals"][symbol] = signal
                            
                            logger.info(f"New {signal} signal for {symbol} sent to user {chat_id}")
                        
                    except Exception as e:
                        logger.error(f"Error processing {symbol} for user {chat_id}: {e}")
                        continue
            
            # Wait before next check
            await asyncio.sleep(MONITOR_SLEEP_SECONDS)
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            await asyncio.sleep(MONITOR_SLEEP_SECONDS)

async def main():
    """Main application entry point."""
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        logger.error("BOT_TOKEN not set. Please set the BOT_TOKEN environment variable.")
        return
    
    # Create application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("coins", show_coins))
    app.add_handler(CommandHandler("add", add_coin))
    app.add_handler(CommandHandler("remove", remove_coin))
    app.add_handler(CommandHandler("timeframe", set_interval))
    
    logger.info("Bot handlers registered successfully")
    
    # Start signal monitoring as a background task
    asyncio.create_task(monitor_signals(app))
    
    # Start bot polling
    try:
        await app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
