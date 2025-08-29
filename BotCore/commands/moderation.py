#!/usr/bin/env python3
"""
Advanced Moderation Commands for Discord Bot
Comprehensive moderation system with advanced features
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import asyncio
import re
from .base_command import BaseCommand
from utils.logger import setup_logger

logger = setup_logger('moderation')

class ModerationCommands(BaseCommand):
    """Advanced moderation commands with comprehensive features."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.muted_users = {}  # Store muted users with expiration times
        
    async def cog_check(self, ctx):
        """Check if user has moderation permissions."""
        return ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator
        
    @commands.command(name='ban', help='Ban a user with optional reason and duration')
    async def ban_user(self, ctx, member: discord.Member, duration: str = None, *, reason: str = "No reason provided"):
        """Advanced ban command with duration support."""
        try:
            # Parse duration if provided
            ban_until = None
            if duration:
                ban_until = self._parse_duration(duration)
                
            # Send DM to user before ban
            try:
                dm_embed = self.create_error_embed(
                    "You have been banned",
                    f"**Server:** {ctx.guild.name}\n**Reason:** {reason}\n**Duration:** {duration or 'Permanent'}\n**Moderator:** {ctx.author}"
                )
                await member.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled
                
            # Ban the user
            await member.ban(reason=f"Banned by {ctx.author}: {reason}")
            
            # Log the ban
            log_embed = self.create_success_embed(
                "User Banned Successfully",
                f"**User:** {member} ({member.id})\n**Reason:** {reason}\n**Duration:** {duration or 'Permanent'}\n**Moderator:** {ctx.author}"
            )
            log_embed.set_thumbnail(url=member.display_avatar.url)
            await ctx.send(embed=log_embed)
            
            # Schedule unban if duration specified
            if ban_until:
                await self._schedule_unban(ctx.guild, member, ban_until)
                
        except discord.Forbidden:
            await self.send_embed(ctx, self.create_error_embed("Permission Error", "I don't have permission to ban this user."))
        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            await self.send_embed(ctx, self.create_error_embed("Error", "An error occurred while banning the user."))
            
    @commands.command(name='unban', help='Unban a user by ID or username')
    async def unban_user(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        """Unban a user by their ID."""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author}: {reason}")
            
            embed = self.create_success_embed(
                "User Unbanned",
                f"**User:** {user} ({user.id})\n**Reason:** {reason}\n**Moderator:** {ctx.author}"
            )
            await self.send_embed(ctx, embed)
            
        except discord.NotFound:
            await self.send_embed(ctx, self.create_error_embed("Error", "User not found or not banned."))
        except Exception as e:
            logger.error(f"Error in unban command: {e}")
            await self.send_embed(ctx, self.create_error_embed("Error", "An error occurred while unbanning the user."))
            
    @commands.command(name='kick', help='Kick a user with reason')
    async def kick_user(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a user from the server."""
        try:
            # Send DM before kick
            try:
                dm_embed = self.create_warning_embed(
                    "You have been kicked",
                    f"**Server:** {ctx.guild.name}\n**Reason:** {reason}\n**Moderator:** {ctx.author}"
                )
                await member.send(embed=dm_embed)
            except:
                pass
                
            await member.kick(reason=f"Kicked by {ctx.author}: {reason}")
            
            embed = self.create_success_embed(
                "User Kicked",
                f"**User:** {member} ({member.id})\n**Reason:** {reason}\n**Moderator:** {ctx.author}"
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_embed(ctx, embed)
            
        except discord.Forbidden:
            await self.send_embed(ctx, self.create_error_embed("Permission Error", "I don't have permission to kick this user."))
            
    @commands.command(name='mute', help='Mute a user for specified duration')
    async def mute_user(self, ctx, member: discord.Member, duration: str = "10m", *, reason: str = "No reason provided"):
        """Advanced mute command with duration."""
        try:
            # Parse duration
            mute_until = self._parse_duration(duration)
            
            # Apply timeout
            await member.timeout(mute_until, reason=f"Muted by {ctx.author}: {reason}")
            
            # Store mute info
            self.muted_users[member.id] = {
                'until': mute_until,
                'reason': reason,
                'moderator': ctx.author.id
            }
            
            embed = self.create_success_embed(
                "User Muted",
                f"**User:** {member} ({member.id})\n**Duration:** {duration}\n**Reason:** {reason}\n**Moderator:** {ctx.author}"
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_embed(ctx, embed)
            
        except Exception as e:
            logger.error(f"Error in mute command: {e}")
            await self.send_embed(ctx, self.create_error_embed("Error", "An error occurred while muting the user."))
            
    @commands.command(name='unmute', help='Unmute a user')
    async def unmute_user(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Unmute a user."""
        try:
            await member.timeout(None, reason=f"Unmuted by {ctx.author}: {reason}")
            
            if member.id in self.muted_users:
                del self.muted_users[member.id]
                
            embed = self.create_success_embed(
                "User Unmuted",
                f"**User:** {member} ({member.id})\n**Reason:** {reason}\n**Moderator:** {ctx.author}"
            )
            await self.send_embed(ctx, embed)
            
        except Exception as e:
            await self.send_embed(ctx, self.create_error_embed("Error", "An error occurred while unmuting the user."))
            
    @commands.command(name='warn', help='Warn a user and log the warning')
    async def warn_user(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a user and log it."""
        try:
            # Send DM warning
            try:
                dm_embed = self.create_warning_embed(
                    "You received a warning",
                    f"**Server:** {ctx.guild.name}\n**Reason:** {reason}\n**Moderator:** {ctx.author}"
                )
                await member.send(embed=dm_embed)
            except:
                pass
                
            embed = self.create_warning_embed(
                "User Warned",
                f"**User:** {member} ({member.id})\n**Reason:** {reason}\n**Moderator:** {ctx.author}"
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_embed(ctx, embed)
            
        except Exception as e:
            await self.send_embed(ctx, self.create_error_embed("Error", "An error occurred while warning the user."))
            
    @commands.command(name='clear', help='Delete multiple messages')
    async def clear_messages(self, ctx, amount: int = 10, member: discord.Member = None):
        """Delete multiple messages with optional user filter."""
        try:
            if amount > 100:
                amount = 100
                
            def check(message):
                if member:
                    return message.author == member
                return True
                
            deleted = await ctx.channel.purge(limit=amount + 1, check=check)
            
            embed = self.create_success_embed(
                "Messages Cleared",
                f"**Deleted:** {len(deleted) - 1} messages\n**Channel:** {ctx.channel.mention}\n**Moderator:** {ctx.author}"
            )
            
            if member:
                embed.add_field(name="Filter", value=f"Only messages from {member}", inline=False)
                
            msg = await self.send_embed(ctx, embed)
            await asyncio.sleep(5)
            await msg.delete()
            
        except Exception as e:
            await self.send_embed(ctx, self.create_error_embed("Error", "An error occurred while clearing messages."))
            
    @commands.command(name='slowmode', help='Set channel slowmode delay')
    async def set_slowmode(self, ctx, delay: int = 0):
        """Set slowmode for the current channel."""
        try:
            await ctx.channel.edit(slowmode_delay=delay)
            
            if delay == 0:
                embed = self.create_success_embed("Slowmode Disabled", f"Slowmode has been disabled in {ctx.channel.mention}")
            else:
                embed = self.create_success_embed("Slowmode Set", f"Slowmode set to **{delay} seconds** in {ctx.channel.mention}")
                
            await self.send_embed(ctx, embed)
            
        except Exception as e:
            await self.send_embed(ctx, self.create_error_embed("Error", "An error occurred while setting slowmode."))
            
    @commands.command(name='lock', help='Lock a channel')
    async def lock_channel(self, ctx, channel: discord.TextChannel = None):
        """Lock a channel to prevent messages."""
        if not channel:
            channel = ctx.channel
            
        try:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            
            embed = self.create_success_embed(
                "Channel Locked",
                f"**Channel:** {channel.mention}\n**Moderator:** {ctx.author}"
            )
            await self.send_embed(ctx, embed)
            
        except Exception as e:
            await self.send_embed(ctx, self.create_error_embed("Error", "An error occurred while locking the channel."))
            
    @commands.command(name='unlock', help='Unlock a channel')
    async def unlock_channel(self, ctx, channel: discord.TextChannel = None):
        """Unlock a channel to allow messages."""
        if not channel:
            channel = ctx.channel
            
        try:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = None
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            
            embed = self.create_success_embed(
                "Channel Unlocked",
                f"**Channel:** {channel.mention}\n**Moderator:** {ctx.author}"
            )
            await self.send_embed(ctx, embed)
            
        except Exception as e:
            await self.send_embed(ctx, self.create_error_embed("Error", "An error occurred while unlocking the channel."))
            
    @commands.command(name='nick', help='Change a user\'s nickname')
    async def change_nickname(self, ctx, member: discord.Member, *, nickname: str = None):
        """Change a user's nickname."""
        try:
            old_nick = member.display_name
            await member.edit(nick=nickname)
            
            embed = self.create_success_embed(
                "Nickname Changed",
                f"**User:** {member} ({member.id})\n**Old Nickname:** {old_nick}\n**New Nickname:** {nickname or 'Reset'}\n**Moderator:** {ctx.author}"
            )
            await self.send_embed(ctx, embed)
            
        except Exception as e:
            await self.send_embed(ctx, self.create_error_embed("Error", "An error occurred while changing the nickname."))
            
    @commands.command(name='role', help='Add or remove a role from a user')
    async def manage_role(self, ctx, member: discord.Member, role: discord.Role, action: str = "add"):
        """Add or remove a role from a user."""
        try:
            if action.lower() == "add":
                await member.add_roles(role)
                embed = self.create_success_embed(
                    "Role Added",
                    f"**User:** {member} ({member.id})\n**Role:** {role.name}\n**Moderator:** {ctx.author}"
                )
            elif action.lower() == "remove":
                await member.remove_roles(role)
                embed = self.create_success_embed(
                    "Role Removed",
                    f"**User:** {member} ({member.id})\n**Role:** {role.name}\n**Moderator:** {ctx.author}"
                )
            else:
                embed = self.create_error_embed("Invalid Action", "Use 'add' or 'remove'")
                
            await self.send_embed(ctx, embed)
            
        except Exception as e:
            await self.send_embed(ctx, self.create_error_embed("Error", "An error occurred while managing the role."))
            
    @commands.command(name='userinfo', help='Get detailed information about a user')
    async def user_info(self, ctx, member: discord.Member = None):
        """Get detailed information about a user."""
        if not member:
            member = ctx.author
            
        embed = self.create_info_embed("User Information")
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="Display Name", value=member.display_name, inline=True)
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
        embed.add_field(name="Status", value=str(member.status).title(), inline=True)
        embed.add_field(name="Bot Account", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="Role Count", value=len(member.roles) - 1, inline=True)
        
        await self.send_embed(ctx, embed)
        
    @commands.command(name='serverinfo', help='Get detailed server information')
    async def server_info(self, ctx):
        """Get detailed information about the server."""
        guild = ctx.guild
        
        embed = self.create_info_embed(f"Server Information - {guild.name}")
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Verification Level", value=str(guild.verification_level).title(), inline=True)
        embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="Boost Count", value=guild.premium_subscription_count, inline=True)
        
        await self.send_embed(ctx, embed)
        
    @commands.command(name='history', help='Get message history for a user')
    async def message_history(self, ctx, member: discord.Member, limit: int = 20):
        """Get recent message history for a user."""
        if limit > 50:
            limit = 50
            
        messages = []
        async for message in ctx.channel.history(limit=200):
            if message.author == member:
                messages.append(f"**{message.created_at.strftime('%H:%M')}**: {message.content[:100]}{'...' if len(message.content) > 100 else ''}")
                if len(messages) >= limit:
                    break
                    
        if not messages:
            embed = self.create_warning_embed("No Messages", f"No recent messages found from {member.mention}")
        else:
            embed = self.create_info_embed(f"Message History - {member.display_name}")
            embed.description = "\n".join(messages[:10])  # Limit to prevent embed size issues
            
        await self.send_embed(ctx, embed)
        
    def _parse_duration(self, duration_str):
        """Parse duration string into datetime object."""
        duration_str = duration_str.lower()
        
        # Extract number and unit
        match = re.match(r'(\d+)([smhd])', duration_str)
        if not match:
            return datetime.now(timezone.utc) + timedelta(minutes=10)  # Default 10 minutes
            
        amount, unit = match.groups()
        amount = int(amount)
        
        if unit == 's':
            delta = timedelta(seconds=amount)
        elif unit == 'm':
            delta = timedelta(minutes=amount)
        elif unit == 'h':
            delta = timedelta(hours=amount)
        elif unit == 'd':
            delta = timedelta(days=amount)
        else:
            delta = timedelta(minutes=10)
            
        return datetime.now(timezone.utc) + delta
        
    async def _schedule_unban(self, guild, member, unban_time):
        """Schedule an unban for later."""
        async def unban_later():
            await asyncio.sleep((unban_time - datetime.now(timezone.utc)).total_seconds())
            try:
                await guild.unban(member, reason="Temporary ban expired")
                logger.info(f"Auto-unbanned {member} from {guild.name}")
            except:
                pass
                
        asyncio.create_task(unban_later())

async def setup(bot):
    """Setup function to add the moderation commands to the bot."""
    await bot.add_cog(ModerationCommands(bot))