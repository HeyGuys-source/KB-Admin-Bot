#!/usr/bin/env python3
"""
Advanced Discord bot implementation with comprehensive error handling,
logging, and modular command system.
"""

import discord
from discord.ext import commands, tasks
import os
import asyncio
import traceback
import json
from datetime import datetime, timezone
from utils.logger import setup_logger
from utils.error_handler import ErrorHandler
from config import BotConfig
from commands.base_command import BaseCommand

# Setup logging
logger = setup_logger('bot')

class AdvancedDiscordBot:
    """Advanced Discord bot with comprehensive error handling and monitoring."""
    
    def __init__(self):
        # Bot configuration
        self.config = BotConfig()
        self.token = self.config.DISCORD_TOKEN
        
        if not self.token:
            logger.error("Discord token not found in environment variables!")
            raise ValueError("DISCORD_TOKEN environment variable is required")
            
        # Setup bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        intents.members = True
        
        # Initialize bot
        self.bot = commands.Bot(
            command_prefix=self.config.PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True
        )
        
        # Error handler
        self.error_handler = ErrorHandler()
        
        # Bot statistics
        self.stats = {
            'start_time': None,
            'commands_executed': 0,
            'errors_handled': 0,
            'guilds_joined': 0,
            'guilds_left': 0,
            'messages_seen': 0
        }
        
        self.setup_events()
        self.setup_error_handling()
        
    def setup_events(self):
        """Setup bot event handlers."""
        
        @self.bot.event
        async def on_ready():
            """Called when bot is ready and connected."""
            self.stats['start_time'] = datetime.now(timezone.utc)
            
            logger.info(f"Bot logged in as {self.bot.user}")
            logger.info(f"Bot ID: {self.bot.user.id}")
            logger.info(f"Connected to {len(self.bot.guilds)} guilds")
            logger.info(f"Serving {sum(g.member_count for g in self.bot.guilds)} users")
            
            # Start background tasks
            if not self.status_updater.is_running():
                self.status_updater.start()
                
            if not self.ping_task.is_running():
                self.ping_task.start()
                
            # Set initial status
            await self.update_bot_status()
            
        @self.bot.event
        async def on_guild_join(guild):
            """Called when bot joins a guild."""
            self.stats['guilds_joined'] += 1
            logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
            await self.update_bot_status()
            
        @self.bot.event
        async def on_guild_remove(guild):
            """Called when bot leaves a guild."""
            self.stats['guilds_left'] += 1
            logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
            await self.update_bot_status()
            
        @self.bot.event
        async def on_message(message):
            """Called for every message."""
            if message.author == self.bot.user:
                return
                
            self.stats['messages_seen'] += 1
            
            # Process commands
            await self.bot.process_commands(message)
            
        @self.bot.event
        async def on_command(ctx):
            """Called before command execution."""
            self.stats['commands_executed'] += 1
            logger.info(f"Command '{ctx.command}' executed by {ctx.author} in {ctx.guild}")
            
        @self.bot.event
        async def on_command_error(ctx, error):
            """Global command error handler."""
            self.stats['errors_handled'] += 1
            await self.error_handler.handle_command_error(ctx, error)
            
    def setup_error_handling(self):
        """Setup comprehensive error handling."""
        
        @self.bot.event
        async def on_error(event, *args, **kwargs):
            """Global error handler for non-command errors."""
            self.stats['errors_handled'] += 1
            logger.error(f"Error in event {event}: {traceback.format_exc()}")
            
    @tasks.loop(seconds=30)
    async def status_updater(self):
        """Update bot status periodically."""
        try:
            await self.update_bot_status()
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            
    @tasks.loop(seconds=20)
    async def ping_task(self):
        """Keep-alive ping task to maintain bot activity."""
        try:
            # Log bot heartbeat
            latency = round(self.bot.latency * 1000)
            logger.debug(f"Bot heartbeat - Latency: {latency}ms")
            
            # Update keep-alive server with bot status
            await self.update_keepalive_status()
            
        except Exception as e:
            logger.error(f"Error in ping task: {e}")
            
    async def update_bot_status(self):
        """Update bot's Discord status."""
        try:
            guild_count = len(self.bot.guilds)
            user_count = sum(g.member_count for g in self.bot.guilds)
            
            status_messages = [
                f"Serving {guild_count} servers",
                f"Helping {user_count:,} users",
                f"Prefix: {self.config.PREFIX}",
                "Advanced Bot System"
            ]
            
            # Rotate status messages
            import random
            status = random.choice(status_messages)
            
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=status
                ),
                status=discord.Status.online
            )
            
        except Exception as e:
            logger.error(f"Error updating bot status: {e}")
            
    async def update_keepalive_status(self):
        """Update keep-alive server with current bot status."""
        try:
            from keep_alive import update_bot_status
            
            status_data = {
                'online': True,
                'latency': round(self.bot.latency * 1000),
                'guilds': len(self.bot.guilds),
                'users': sum(g.member_count for g in self.bot.guilds),
                'uptime': self.get_uptime(),
                'stats': self.stats.copy()
            }
            
            update_bot_status(status_data)
            
        except Exception as e:
            logger.error(f"Error updating keep-alive status: {e}")
            
    def get_uptime(self):
        """Get bot uptime in seconds."""
        if self.stats['start_time']:
            return int((datetime.now(timezone.utc) - self.stats['start_time']).total_seconds())
        return 0
        
    def add_cog(self, cog):
        """Add a command cog to the bot."""
        try:
            asyncio.create_task(self.bot.add_cog(cog))
            logger.info(f"Added cog: {cog.__class__.__name__}")
        except Exception as e:
            logger.error(f"Error adding cog {cog.__class__.__name__}: {e}")
            
    def run_bot(self):
        """Run the Discord bot."""
        try:
            logger.info("Starting Discord bot connection...")
            self.bot.run(self.token, log_handler=None)  # Disable discord.py logging
        except discord.LoginFailure:
            logger.error("Invalid Discord token provided")
            raise
        except discord.HTTPException as e:
            logger.error(f"HTTP error during bot startup: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during bot startup: {e}")
            raise
            
    async def close(self):
        """Gracefully shutdown the bot."""
        try:
            logger.info("Shutting down bot...")
            
            # Stop background tasks
            if self.status_updater.is_running():
                self.status_updater.stop()
                
            if self.ping_task.is_running():
                self.ping_task.stop()
                
            # Close bot connection
            await self.bot.close()
            logger.info("Bot shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}")
