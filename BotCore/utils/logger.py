#!/usr/bin/env python3
"""
Comprehensive logging system for the Discord bot.
Provides structured logging with different levels and output formats.
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
import traceback

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m'   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        """Format log record with colors."""
        log_color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format message
        formatted_message = f"{log_color}[{timestamp}] [{record.levelname:8}] [{record.name:12}] {record.getMessage()}{self.RESET}"
        
        # Add exception info if present
        if record.exc_info:
            formatted_message += f"\n{self.formatException(record.exc_info)}"
            
        return formatted_message

class BotLogger:
    """Advanced logging system for the Discord bot."""
    
    def __init__(self, name, level='INFO', log_to_file=False, log_file_path='logs/bot.log'):
        self.name = name
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.log_to_file = log_to_file
        self.log_file_path = log_file_path
        self.logger = None
        
        self._setup_logger()
        
    def _setup_logger(self):
        """Setup the logger with handlers and formatters."""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.level)
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_formatter = ColoredFormatter()
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if enabled
        if self.log_to_file:
            self._setup_file_handler()
            
        # Prevent propagation to root logger
        self.logger.propagate = False
        
    def _setup_file_handler(self):
        """Setup file logging with rotation."""
        try:
            # Create logs directory if it doesn't exist
            log_dir = os.path.dirname(self.log_file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            # Rotating file handler (10MB max, 5 backup files)
            file_handler = RotatingFileHandler(
                self.log_file_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(self.level)
            
            # File formatter (more detailed)
            file_formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)-12s | %(funcName)-15s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            self.logger.error(f"Failed to setup file logging: {e}")
            
    def debug(self, message, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)
        
    def info(self, message, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)
        
    def warning(self, message, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)
        
    def error(self, message, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)
        
    def critical(self, message, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)
        
    def exception(self, message, *args, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, *args, **kwargs)
        
    def log_function_call(self, func_name, *args, **kwargs):
        """Log function call with arguments."""
        args_str = ', '.join([str(arg) for arg in args])
        kwargs_str = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
        all_args = ', '.join(filter(None, [args_str, kwargs_str]))
        self.debug(f"Calling {func_name}({all_args})")
        
    def log_performance(self, operation, duration):
        """Log performance metrics."""
        self.info(f"Performance: {operation} took {duration:.2f}s")
        
    def log_bot_event(self, event_type, details):
        """Log bot events with structured format."""
        self.info(f"Bot Event [{event_type}]: {details}")
        
    def log_command_usage(self, command, user, guild, success=True):
        """Log command usage."""
        status = "SUCCESS" if success else "FAILED"
        self.info(f"Command [{status}]: '{command}' by {user} in {guild}")
        
    def log_error_with_context(self, error, context=None):
        """Log error with additional context."""
        error_msg = f"Error: {str(error)}"
        if context:
            error_msg += f" | Context: {context}"
        error_msg += f"\nTraceback: {traceback.format_exc()}"
        self.error(error_msg)

# Global logger instances
_loggers = {}

def setup_logger(name, level=None, log_to_file=None, log_file_path=None):
    """
    Setup and return a logger instance.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_file_path: Path to log file
        
    Returns:
        BotLogger instance
    """
    # Use defaults from environment if not provided
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO')
    if log_to_file is None:
        log_to_file = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'
    if log_file_path is None:
        log_file_path = os.getenv('LOG_FILE_PATH', 'logs/bot.log')
        
    # Return existing logger if already created
    if name in _loggers:
        return _loggers[name]
        
    # Create new logger
    logger = BotLogger(name, level, log_to_file, log_file_path)
    _loggers[name] = logger
    
    return logger

def get_logger(name):
    """Get existing logger by name."""
    return _loggers.get(name)

# Setup basic logging for discord.py
logging.basicConfig(level=logging.WARNING)
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('discord.http').setLevel(logging.WARNING)
