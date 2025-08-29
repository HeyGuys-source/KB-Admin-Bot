#!/usr/bin/env python3
"""
Main entry point for the Discord bot system.
This module initializes and runs both the Discord bot and Flask keep-alive server.
"""

import os
import sys
import asyncio
import threading
import signal
import time
from utils.logger import setup_logger
from bot import AdvancedDiscordBot
from keep_alive import app as flask_app

# Setup logging
logger = setup_logger('main')

class BotSystem:
    """Main bot system that manages both Discord bot and Flask server."""
    
    def __init__(self):
        self.bot = None
        self.flask_thread = None
        self.running = False
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.shutdown()
        
    def start_flask_server(self):
        """Start Flask keep-alive server in a separate thread."""
        try:
            logger.info("Starting Flask keep-alive server...")
            flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        except Exception as e:
            logger.error(f"Flask server error: {e}")
            
    def start_bot(self):
        """Start the Discord bot."""
        try:
            self.bot = AdvancedDiscordBot()
            logger.info("Starting Discord bot...")
            self.bot.run_bot()
        except Exception as e:
            logger.error(f"Bot startup error: {e}")
            self.restart_bot()
            
    def restart_bot(self):
        """Restart the bot after a delay."""
        logger.info("Restarting bot in 10 seconds...")
        time.sleep(10)
        self.start_bot()
        
    def run(self):
        """Main run method that starts both Flask and Discord bot."""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.running = True
        logger.info("Starting Advanced Discord Bot System...")
        
        # Start Flask server in separate thread
        self.flask_thread = threading.Thread(target=self.start_flask_server, daemon=True)
        self.flask_thread.start()
        
        # Give Flask time to start
        time.sleep(2)
        
        # Start Discord bot (blocking)
        self.start_bot()
        
    def shutdown(self):
        """Shutdown all components gracefully."""
        self.running = False
        logger.info("Shutting down bot system...")
        
        if self.bot:
            try:
                asyncio.create_task(self.bot.close())
            except:
                pass
                
        logger.info("Bot system shutdown complete.")
        sys.exit(0)

# Flask app reference for gunicorn
app = flask_app

if __name__ == "__main__":
    try:
        bot_system = BotSystem()
        bot_system.run()
    except KeyboardInterrupt:
        logger.info("Bot system interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in bot system: {e}")
        sys.exit(1)
