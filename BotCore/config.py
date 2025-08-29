#!/usr/bin/env python3
"""
Configuration management for the Discord bot system.
Handles environment variables and default settings.
"""

import os
from utils.logger import setup_logger

logger = setup_logger('config')

class BotConfig:
    """Bot configuration class handling all environment variables and settings."""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults."""
        
        # Discord Bot Settings
        self.DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')
        self.PREFIX = os.getenv('BOT_PREFIX', '!')
        self.OWNER_ID = int(os.getenv('OWNER_ID', '0')) if os.getenv('OWNER_ID') else None
        
        # Bot Behavior Settings
        self.MAX_MESSAGE_LENGTH = int(os.getenv('MAX_MESSAGE_LENGTH', '2000'))
        self.COMMAND_COOLDOWN = float(os.getenv('COMMAND_COOLDOWN', '1.0'))
        self.ERROR_CHANNEL_ID = int(os.getenv('ERROR_CHANNEL_ID', '0')) if os.getenv('ERROR_CHANNEL_ID') else None
        
        # Keep-alive Settings
        self.PING_INTERVAL = int(os.getenv('PING_INTERVAL', '20'))
        self.STATUS_UPDATE_INTERVAL = int(os.getenv('STATUS_UPDATE_INTERVAL', '30'))
        self.FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
        
        # Logging Settings
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'
        self.LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/bot.log')
        
        # Database Settings (for future use)
        self.DATABASE_URL = os.getenv('DATABASE_URL', '')
        self.USE_DATABASE = os.getenv('USE_DATABASE', 'false').lower() == 'true'
        
        # Security Settings
        self.SESSION_SECRET = os.getenv('SESSION_SECRET', 'advanced-discord-bot-secret')
        self.ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
        
        # Feature Flags
        self.ENABLE_LOGGING = os.getenv('ENABLE_LOGGING', 'true').lower() == 'true'
        self.ENABLE_ERROR_REPORTING = os.getenv('ENABLE_ERROR_REPORTING', 'true').lower() == 'true'
        self.ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
        
        # Validate required settings
        self._validate_config()
        
        # Log configuration
        self._log_config()
        
    def _validate_config(self):
        """Validate required configuration values."""
        if not self.DISCORD_TOKEN:
            logger.error("DISCORD_TOKEN environment variable is required!")
            raise ValueError("DISCORD_TOKEN environment variable is required")
            
        if len(self.DISCORD_TOKEN) < 50:
            logger.warning("DISCORD_TOKEN appears to be invalid (too short)")
            
        if self.OWNER_ID and self.OWNER_ID <= 0:
            logger.warning("OWNER_ID should be a valid Discord user ID")
            
    def _log_config(self):
        """Log current configuration (excluding sensitive data)."""
        logger.info("Bot Configuration:")
        logger.info(f"  Prefix: {self.PREFIX}")
        logger.info(f"  Owner ID: {self.OWNER_ID or 'Not set'}")
        logger.info(f"  Max Message Length: {self.MAX_MESSAGE_LENGTH}")
        logger.info(f"  Command Cooldown: {self.COMMAND_COOLDOWN}s")
        logger.info(f"  Ping Interval: {self.PING_INTERVAL}s")
        logger.info(f"  Status Update Interval: {self.STATUS_UPDATE_INTERVAL}s")
        logger.info(f"  Flask Port: {self.FLASK_PORT}")
        logger.info(f"  Log Level: {self.LOG_LEVEL}")
        logger.info(f"  Log to File: {self.LOG_TO_FILE}")
        logger.info(f"  Database Enabled: {self.USE_DATABASE}")
        logger.info(f"  Logging Enabled: {self.ENABLE_LOGGING}")
        logger.info(f"  Error Reporting Enabled: {self.ENABLE_ERROR_REPORTING}")
        logger.info(f"  Metrics Enabled: {self.ENABLE_METRICS}")
        
    def get_env_info(self):
        """Get environment information for status display."""
        return {
            'prefix': self.PREFIX,
            'ping_interval': self.PING_INTERVAL,
            'status_update_interval': self.STATUS_UPDATE_INTERVAL,
            'log_level': self.LOG_LEVEL,
            'features': {
                'logging': self.ENABLE_LOGGING,
                'error_reporting': self.ENABLE_ERROR_REPORTING,
                'metrics': self.ENABLE_METRICS,
                'database': self.USE_DATABASE
            }
        }

# Global config instance
config = BotConfig()
