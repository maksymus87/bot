#!/usr/bin/env python3
"""
Simplified Telegram Trading Bot for Replit environment
"""
import logging
import asyncio
import os
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def monitor_signals_simple(app):
    """Simplified signal monitoring loop"""
    logger.info("Starting signal monitoring loop")
    
    while True:
        try:
            if not user_settings:
                await asyncio.sleep(MONITOR_SLEEP_SECONDS)
                continue
                
            for chat_id, settings in list(user_settings.items()):
                coins = settings.get("coins", [])
                interval = settings.get("interval", "15m")
                
                for symbol in coins:
                    try:
                        df = get_ohlcv(symbol, interval)
                        if df is None:
                            continue
                        
                        signal = check_signal(df)
                        if signal is None:
                            continue
                        
                        last_signal = settings["last_signals"].get(symbol)
                        if signal != last_signal:
                            await send_signal(app, chat_id, symbol, interval, signal)
                            settings["last_signals"][symbol] = signal
                            logger.info(f"New {signal} signal for {symbol} sent to user {chat_id}")
                        
                    except Exception as e:
                        logger.error(f"Error processing {symbol} for user {chat_id}: {e}")
                        continue
            
            await asyncio.sleep(MONITOR_SLEEP_SECONDS)
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            await asyncio.sleep(MONITOR_SLEEP_SECONDS)

def main():
    """Main function using a simpler approach"""
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
    
    # Start monitoring in background
    async def run_bot():
        # Start monitoring task
        monitor_task = asyncio.create_task(monitor_signals_simple(app))
        
        # Start polling
        try:
            async with app:
                await app.start()
                await app.updater.start_polling(drop_pending_updates=True)
                await asyncio.Event().wait()  # Keep running
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        finally:
            monitor_task.cancel()
            await app.stop()
    
    # Run with proper event loop handling
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")

if __name__ == "__main__":
    main()