#!/usr/bin/env python3
"""
Base command class for Discord bot commands.
Provides common functionality and structure for all bot commands.
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
from utils.logger import setup_logger
from utils.error_handler import global_error_handler

logger = setup_logger('commands')

class BaseCommand(commands.Cog):
    """
    Base class for all bot commands.
    Provides common functionality like logging, error handling, and utilities.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.command_count = 0
        self.last_used = None
        
    async def cog_before_invoke(self, ctx):
        """Called before every command in this cog."""
        self.command_count += 1
        self.last_used = datetime.now(timezone.utc)
        
        # Log command usage
        logger.log_command_usage(
            command=ctx.command.qualified_name,
            user=f"{ctx.author} ({ctx.author.id})",
            guild=f"{ctx.guild.name} ({ctx.guild.id})" if ctx.guild else "DM"
        )
        
    async def cog_after_invoke(self, ctx):
        """Called after every command in this cog."""
        logger.debug(f"Command {ctx.command.qualified_name} completed successfully")
        
    async def cog_command_error(self, ctx, error):
        """Handle errors in this cog."""
        await global_error_handler.handle_command_error(ctx, error)
        
    def create_embed(self, title=None, description=None, color=None):
        """
        Create a standard embed with common formatting.
        
        Args:
            title: Embed title
            description: Embed description
            color: Embed color (defaults to bot's theme color)
            
        Returns:
            discord.Embed: Configured embed
        """
        if color is None:
            color = discord.Color.blue()
            
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        return embed
        
    def create_success_embed(self, title, description=None):
        """Create a success embed (green)."""
        return self.create_embed(
            title=f"✅ {title}",
            description=description,
            color=discord.Color.green()
        )
        
    def create_error_embed(self, title, description=None):
        """Create an error embed (red)."""
        return self.create_embed(
            title=f"❌ {title}",
            description=description,
            color=discord.Color.red()
        )
        
    def create_warning_embed(self, title, description=None):
        """Create a warning embed (yellow)."""
        return self.create_embed(
            title=f"⚠️ {title}",
            description=description,
            color=discord.Color.yellow()
        )
        
    def create_info_embed(self, title, description=None):
        """Create an info embed (blue)."""
        return self.create_embed(
            title=f"ℹ️ {title}",
            description=description,
            color=discord.Color.blue()
        )
        
    async def send_embed(self, ctx, embed):
        """
        Send an embed with error handling.
        
        Args:
            ctx: Command context
            embed: Embed to send
            
        Returns:
            discord.Message or None if failed
        """
        try:
            return await ctx.send(embed=embed)
        except discord.HTTPException as e:
            logger.error(f"Failed to send embed: {e}")
            # Try sending plain text fallback
            try:
                return await ctx.send(f"**{embed.title}**\n{embed.description}")
            except discord.HTTPException:
                logger.error("Failed to send fallback message")
                return None
                
    def get_user_permissions(self, member):
        """
        Get a list of permissions for a member.
        
        Args:
            member: Discord member
            
        Returns:
            list: List of permission names
        """
        perms = member.guild_permissions
        return [perm for perm, value in perms if value]
        
    def format_time(self, dt):
        """
        Format datetime for display.
        
        Args:
            dt: datetime object
            
        Returns:
            str: Formatted time string
        """
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        
    def get_command_stats(self):
        """Get statistics for this command cog."""
        return {
            'command_count': self.command_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'cog_name': self.__class__.__name__
        }

class ExampleCommand(BaseCommand):
    """Example command to demonstrate the base class usage."""
    
    @commands.command(name='ping', help='Check bot latency')
    async def ping(self, ctx):
        """Simple ping command to test bot responsiveness."""
        latency = round(self.bot.latency * 1000)
        
        embed = self.create_info_embed(
            title="Pong! 🏓",
            description=f"Bot latency: `{latency}ms`"
        )
        
        await self.send_embed(ctx, embed)
        
    @commands.command(name='info', help='Get bot information')
    async def info(self, ctx):
        """Get basic bot information."""
        embed = self.create_info_embed(
            title="Bot Information",
            description="Advanced Discord Bot System"
        )
        
        embed.add_field(name="Guilds", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=sum(g.member_count for g in self.bot.guilds), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        await self.send_embed(ctx, embed)
        
    @commands.command(name='test_error', help='Test error handling')
    @commands.is_owner()
    async def test_error(self, ctx):
        """Test command for error handling (owner only)."""
        # Intentionally raise an error for testing
        raise Exception("This is a test error for debugging purposes")

# Function to add example commands to bot
async def setup(bot):
    """Setup function to add the example commands to the bot."""
    await bot.add_cog(ExampleCommand(bot))
