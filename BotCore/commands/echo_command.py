#!/usr/bin/env python3
"""
Advanced Echo Command for Discord Bot
Allows moderators to send messages as the bot with format options and reply functionality
"""

import discord
from discord.ext import commands
from .base_command import BaseCommand
from utils.logger import setup_logger

logger = setup_logger('echo_command')

class EchoCommand(BaseCommand):
    """Advanced echo command with text format options and reply functionality."""
    
    def __init__(self, bot):
        super().__init__(bot)
        
    async def cog_check(self, ctx):
        """Check if user has moderation permissions."""
        return ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator
        
    @commands.command(name='echo', help='Send a message as the bot with format options')
    async def echo_message(self, ctx, message: str, text_format: str = "plain", message_id: int = None):
        """
        Advanced echo command.
        
        Args:
            message: The message content to send
            text_format: Format type - "plain" or "embed"
            message_id: Optional message ID to reply to
        """
        try:
            # Delete the original command message to hide who used it
            await ctx.message.delete()
            
            # Get the message to reply to if message_id is provided
            reply_to = None
            if message_id:
                try:
                    reply_to = await ctx.channel.fetch_message(message_id)
                except discord.NotFound:
                    # Send error in DM to avoid revealing who used the command
                    try:
                        await ctx.author.send("❌ Message with that ID not found.")
                    except:
                        pass
                    return
                except discord.Forbidden:
                    try:
                        await ctx.author.send("❌ I don't have permission to access that message.")
                    except:
                        pass
                    return
                    
            # Process the message based on format
            if text_format.lower() == "embed":
                # Create an embed message
                embed = discord.Embed(
                    description=message,
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                
                # Send the embed
                if reply_to:
                    await reply_to.reply(embed=embed, mention_author=False)
                else:
                    await ctx.send(embed=embed)
                    
            elif text_format.lower() == "plain":
                # Send plain text message
                if reply_to:
                    await reply_to.reply(message, mention_author=False)
                else:
                    await ctx.send(message)
                    
            else:
                # Invalid format - send error in DM
                try:
                    await ctx.author.send("❌ Invalid text format. Use 'plain' or 'embed'.")
                except:
                    pass
                return
                
            # Log the echo command usage (for audit purposes)
            logger.info(f"Echo command used by {ctx.author} ({ctx.author.id}) in {ctx.guild.name} - Format: {text_format}, Reply: {bool(message_id)}")
            
        except discord.Forbidden:
            try:
                await ctx.author.send("❌ I don't have permission to send messages in that channel.")
            except:
                pass
        except Exception as e:
            logger.error(f"Error in echo command: {e}")
            try:
                await ctx.author.send("❌ An error occurred while sending the message.")
            except:
                pass
                
    @commands.command(name='echoembed', help='Send an advanced embed with title and description')
    async def echo_advanced_embed(self, ctx, title: str, description: str, color: str = "blue", message_id: int = None):
        """
        Advanced echo command for embeds with more options.
        
        Args:
            title: Embed title
            description: Embed description
            color: Embed color (red, green, blue, yellow, purple, etc.)
            message_id: Optional message ID to reply to
        """
        try:
            # Delete the original command message
            await ctx.message.delete()
            
            # Get reply message if specified
            reply_to = None
            if message_id:
                try:
                    reply_to = await ctx.channel.fetch_message(message_id)
                except discord.NotFound:
                    try:
                        await ctx.author.send("❌ Message with that ID not found.")
                    except:
                        pass
                    return
                    
            # Parse color
            color_map = {
                "red": discord.Color.red(),
                "green": discord.Color.green(),
                "blue": discord.Color.blue(),
                "yellow": discord.Color.yellow(),
                "purple": discord.Color.purple(),
                "orange": discord.Color.orange(),
                "pink": discord.Color.magenta(),
                "teal": discord.Color.teal(),
                "dark_blue": discord.Color.dark_blue(),
                "dark_green": discord.Color.dark_green(),
                "dark_red": discord.Color.dark_red(),
                "gold": discord.Color.gold()
            }
            
            embed_color = color_map.get(color.lower(), discord.Color.blue())
            
            # Create the embed
            embed = discord.Embed(
                title=title,
                description=description,
                color=embed_color,
                timestamp=discord.utils.utcnow()
            )
            
            # Send the embed
            if reply_to:
                await reply_to.reply(embed=embed, mention_author=False)
            else:
                await ctx.send(embed=embed)
                
            # Log usage
            logger.info(f"Advanced echo embed used by {ctx.author} ({ctx.author.id}) in {ctx.guild.name}")
            
        except Exception as e:
            logger.error(f"Error in advanced echo command: {e}")
            try:
                await ctx.author.send("❌ An error occurred while sending the embed.")
            except:
                pass
                
    @commands.command(name='echoannounce', help='Send an announcement embed')
    async def echo_announcement(self, ctx, title: str, *, description: str):
        """
        Send a special announcement embed.
        
        Args:
            title: Announcement title
            description: Announcement description
        """
        try:
            # Delete the original command message
            await ctx.message.delete()
            
            # Create announcement embed
            embed = discord.Embed(
                title=f"📢 {title}",
                description=description,
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="Official Announcement")
            
            await ctx.send(embed=embed)
            
            # Log usage
            logger.info(f"Announcement echo used by {ctx.author} ({ctx.author.id}) in {ctx.guild.name}")
            
        except Exception as e:
            logger.error(f"Error in announcement echo: {e}")
            try:
                await ctx.author.send("❌ An error occurred while sending the announcement.")
            except:
                pass

async def setup(bot):
    """Setup function to add the echo commands to the bot."""
    await bot.add_cog(EchoCommand(bot))