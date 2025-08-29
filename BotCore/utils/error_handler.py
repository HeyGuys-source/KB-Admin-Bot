#!/usr/bin/env python3
"""
Comprehensive error handling system for the Discord bot.
Handles various types of errors and provides appropriate responses.
"""

import discord
from discord.ext import commands
import traceback
import sys
from datetime import datetime, timezone
from utils.logger import setup_logger

logger = setup_logger('error_handler')

class ErrorHandler:
    """Advanced error handling for Discord bot commands and events."""
    
    def __init__(self):
        self.error_count = 0
        self.error_history = []
        
    async def handle_command_error(self, ctx, error):
        """
        Handle command errors with appropriate responses.
        
        Args:
            ctx: Discord command context
            error: The error that occurred
        """
        self.error_count += 1
        error_id = f"ERR_{int(datetime.now(timezone.utc).timestamp())}_{self.error_count}"
        
        # Log error details
        logger.error(f"Command error [{error_id}]: {type(error).__name__}: {str(error)}")
        logger.error(f"Command: {ctx.command}")
        logger.error(f"User: {ctx.author} (ID: {ctx.author.id})")
        logger.error(f"Guild: {ctx.guild.name if ctx.guild else 'DM'} (ID: {ctx.guild.id if ctx.guild else 'N/A'})")
        logger.error(f"Channel: {ctx.channel} (ID: {ctx.channel.id})")
        logger.error(f"Message: {ctx.message.content}")
        logger.error(f"Traceback: {traceback.format_exception(type(error), error, error.__traceback__)}")
        
        # Store error in history
        self.error_history.append({
            'id': error_id,
            'timestamp': datetime.now(timezone.utc),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'command': str(ctx.command),
            'user_id': ctx.author.id,
            'guild_id': ctx.guild.id if ctx.guild else None,
            'channel_id': ctx.channel.id
        })
        
        # Keep only last 100 errors
        if len(self.error_history) > 100:
            self.error_history.pop(0)
        
        # Handle specific error types
        embed = discord.Embed(color=discord.Color.red())
        embed.set_footer(text=f"Error ID: {error_id}")
        
        if isinstance(error, commands.CommandNotFound):
            # Don't respond to unknown commands
            return
            
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.title = "Missing Required Argument"
            embed.description = f"You're missing the `{error.param.name}` argument."
            if ctx.command.help:
                embed.add_field(name="Usage", value=f"`{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}`", inline=False)
                
        elif isinstance(error, commands.BadArgument):
            embed.title = "Invalid Argument"
            embed.description = "One of your arguments is invalid. Please check your input and try again."
            if ctx.command.help:
                embed.add_field(name="Usage", value=f"`{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}`", inline=False)
                
        elif isinstance(error, commands.CommandOnCooldown):
            embed.title = "Command on Cooldown"
            embed.description = f"This command is on cooldown. Try again in `{error.retry_after:.1f}` seconds."
            
        elif isinstance(error, commands.MissingPermissions):
            embed.title = "Missing Permissions"
            perms = ', '.join([perm.replace('_', ' ').title() for perm in error.missing_permissions])
            embed.description = f"You need the following permissions to use this command: `{perms}`"
            
        elif isinstance(error, commands.BotMissingPermissions):
            embed.title = "Bot Missing Permissions"
            perms = ', '.join([perm.replace('_', ' ').title() for perm in error.missing_permissions])
            embed.description = f"I need the following permissions to run this command: `{perms}`"
            
        elif isinstance(error, commands.NoPrivateMessage):
            embed.title = "Guild Only Command"
            embed.description = "This command can only be used in a server, not in DMs."
            
        elif isinstance(error, commands.PrivateMessageOnly):
            embed.title = "DM Only Command"
            embed.description = "This command can only be used in DMs, not in a server."
            
        elif isinstance(error, commands.NotOwner):
            embed.title = "Owner Only Command"
            embed.description = "This command can only be used by the bot owner."
            
        elif isinstance(error, commands.DisabledCommand):
            embed.title = "Command Disabled"
            embed.description = "This command is currently disabled."
            
        elif isinstance(error, discord.HTTPException):
            embed.title = "Discord API Error"
            if error.status == 403:
                embed.description = "I don't have permission to perform this action."
            elif error.status == 404:
                embed.description = "The requested resource was not found."
            elif error.status == 429:
                embed.description = "I'm being rate limited by Discord. Please try again later."
            else:
                embed.description = f"A Discord API error occurred: {error.text}"
                
        elif isinstance(error, discord.Forbidden):
            embed.title = "Permission Denied"
            embed.description = "I don't have permission to perform this action."
            
        elif isinstance(error, discord.NotFound):
            embed.title = "Not Found"
            embed.description = "The requested resource was not found."
            
        else:
            # Generic error
            embed.title = "An Error Occurred"
            embed.description = "An unexpected error occurred while processing your command."
            
            # Log full traceback for debugging
            logger.error(f"Unhandled error [{error_id}]: {''.join(traceback.format_exception(type(error), error, error.__traceback__))}")
            
        # Try to send error message
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            # If we can't send embed, try plain text
            try:
                await ctx.send(f"❌ {embed.title}: {embed.description}")
            except discord.HTTPException:
                # If we can't send anything, log it
                logger.error(f"Failed to send error message for error {error_id}")
                
    async def handle_task_error(self, task_name, error):
        """
        Handle errors in background tasks.
        
        Args:
            task_name: Name of the task that errored
            error: The error that occurred
        """
        self.error_count += 1
        error_id = f"TASK_ERR_{int(datetime.now(timezone.utc).timestamp())}_{self.error_count}"
        
        logger.error(f"Task error [{error_id}] in {task_name}: {type(error).__name__}: {str(error)}")
        logger.error(f"Traceback: {''.join(traceback.format_exception(type(error), error, error.__traceback__))}")
        
        # Store error in history
        self.error_history.append({
            'id': error_id,
            'timestamp': datetime.now(timezone.utc),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'task_name': task_name,
            'user_id': None,
            'guild_id': None,
            'channel_id': None
        })
        
    def get_error_stats(self):
        """Get error statistics."""
        recent_errors = [e for e in self.error_history 
                        if (datetime.now(timezone.utc) - e['timestamp']).total_seconds() < 3600]
        
        return {
            'total_errors': self.error_count,
            'recent_errors': len(recent_errors),
            'error_history_count': len(self.error_history)
        }
        
    def get_recent_errors(self, limit=10):
        """Get recent errors for debugging."""
        return self.error_history[-limit:] if self.error_history else []

# Global error handler instance
global_error_handler = ErrorHandler()
