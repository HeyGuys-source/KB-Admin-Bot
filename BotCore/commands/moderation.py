#!/usr/bin/env python3
"""
Advanced Moderation Slash Commands for Discord Bot
Comprehensive moderation system with slash commands
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
import asyncio
import re
from .base_command import BaseCommand


logger = logger('moderation')

class ModerationCommands(BaseCommand):
    """Advanced moderation slash commands with comprehensive features."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.muted_users = {}  # Store muted users with expiration times
        
    def _parse_duration(self, duration_str):
        """Parse duration string like '1h', '30m', '7d' into datetime."""
        if not duration_str:
            return None
            
        match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
        if not match:
            return None
            
        amount, unit = match.groups()
        amount = int(amount)
        
        now = datetime.now(timezone.utc)
        
        if unit == 's':
            return now + timedelta(seconds=amount)
        elif unit == 'm':
            return now + timedelta(minutes=amount)
        elif unit == 'h':
            return now + timedelta(hours=amount)
        elif unit == 'd':
            return now + timedelta(days=amount)
            
        return None
        
    async def _log_command(self, interaction, command_name, target_user=None, reason=None, duration=None, success=True, error_message=None):
        """Log command execution to database."""
        try:
            log_entry = CommandLog(
                command_name=command_name,
                user_id=str(interaction.user.id),
                target_user_id=str(target_user.id) if target_user else None,
                guild_id=str(interaction.guild.id) if interaction.guild else "0",
                channel_id=str(interaction.channel.id) if interaction.channel else "0",
                reason=reason,
                duration=duration,
                success=success,
                error_message=error_message
            )
            db.session.add(log_entry)
            
            # Update stats
            stats = BotStats.get_or_create()
            stats.total_commands += 1
            if command_name == 'ban':
                stats.total_bans += 1
            elif command_name == 'kick':
                stats.total_kicks += 1
            elif command_name == 'mute':
                stats.total_mutes += 1
            elif command_name == 'warn':
                stats.total_warnings += 1
                
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging command: {e}")
            db.session.rollback()
        
    async def _schedule_unban(self, guild, user, unban_time):
        """Schedule automatic unban."""
        await asyncio.sleep((unban_time - datetime.now(timezone.utc)).total_seconds())
        try:
            await guild.unban(user, reason="Automatic unban - ban duration expired")
            logger.info(f"Automatically unbanned {user} from {guild}")
        except Exception as e:
            logger.error(f"Error auto-unbanning {user}: {e}")

    @app_commands.command(name="ban", description="Ban a user with optional reason and duration")
    @app_commands.describe(
        member="The member to ban",
        duration="Duration of the ban (e.g., 1h, 30m, 7d)",
        reason="Reason for the ban"
    )
    async def ban_user(self, interaction: discord.Interaction, member: discord.Member, duration: str = None, reason: str = "No reason provided"):
        """Advanced ban slash command with duration support."""
        # Check permissions
        if not interaction.user.guild_permissions.ban_members:
            await self.send_embed(interaction, self.create_error_embed("Permission Denied", "You don't have permission to ban members."))
            return
            
        try:
            # Parse duration if provided
            ban_until = None
            if duration:
                ban_until = self._parse_duration(duration)
                if not ban_until:
                    await self.send_embed(interaction, self.create_error_embed("Invalid Duration", "Please use format like '1h', '30m', '7d'"))
                    return
                    
            # Send DM to user before ban
            try:
                dm_embed = self.create_error_embed(
                    "You have been banned",
                    f"**Server:** {interaction.guild.name}\n**Reason:** {reason}\n**Duration:** {duration or 'Permanent'}\n**Moderator:** {interaction.user}"
                )
                await member.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled
                
            # Ban the user
            await member.ban(reason=f"Banned by {interaction.user}: {reason}")
            
            # Log the ban
            log_embed = self.create_success_embed(
                "User Banned Successfully",
                f"**User:** {member} ({member.id})\n**Reason:** {reason}\n**Duration:** {duration or 'Permanent'}\n**Moderator:** {interaction.user}"
            )
            log_embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_embed(interaction, log_embed)
            
            # Schedule unban if duration specified
            if ban_until:
                asyncio.create_task(self._schedule_unban(interaction.guild, member, ban_until))
                
            await self._log_command(interaction, "ban", member, reason, duration, True)
                
        except discord.Forbidden:
            await self.send_embed(interaction, self.create_error_embed("Permission Error", "I don't have permission to ban this user."))
            await self._log_command(interaction, "ban", member, reason, duration, False, "Bot permission denied")
        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            await self.send_embed(interaction, self.create_error_embed("Error", "An error occurred while banning the user."))
            await self._log_command(interaction, "ban", member, reason, duration, False, str(e))

    @app_commands.command(name="unban", description="Unban a user by ID")
    @app_commands.describe(
        user_id="The ID of the user to unban",
        reason="Reason for the unban"
    )
    async def unban_user(self, interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        """Unban a user by their ID."""
        if not interaction.user.guild_permissions.ban_members:
            await self.send_embed(interaction, self.create_error_embed("Permission Denied", "You don't have permission to unban members."))
            return
            
        try:
            user_id_int = int(user_id)
            user = await self.bot.fetch_user(user_id_int)
            await interaction.guild.unban(user, reason=f"Unbanned by {interaction.user}: {reason}")
            
            embed = self.create_success_embed(
                "User Unbanned",
                f"**User:** {user} ({user.id})\n**Reason:** {reason}\n**Moderator:** {interaction.user}"
            )
            await self.send_embed(interaction, embed)
            await self._log_command(interaction, "unban", user, reason, None, True)
            
        except ValueError:
            await self.send_embed(interaction, self.create_error_embed("Error", "Invalid user ID format."))
        except discord.NotFound:
            await self.send_embed(interaction, self.create_error_embed("Error", "User not found or not banned."))
            await self._log_command(interaction, "unban", None, reason, None, False, "User not found")
        except Exception as e:
            logger.error(f"Error in unban command: {e}")
            await self.send_embed(interaction, self.create_error_embed("Error", "An error occurred while unbanning the user."))
            await self._log_command(interaction, "unban", None, reason, None, False, str(e))

    @app_commands.command(name="kick", description="Kick a user with reason")
    @app_commands.describe(
        member="The member to kick",
        reason="Reason for the kick"
    )
    async def kick_user(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Kick a user from the server."""
        if not interaction.user.guild_permissions.kick_members:
            await self.send_embed(interaction, self.create_error_embed("Permission Denied", "You don't have permission to kick members."))
            return
            
        try:
            # Send DM before kick
            try:
                dm_embed = self.create_warning_embed(
                    "You have been kicked",
                    f"**Server:** {interaction.guild.name}\n**Reason:** {reason}\n**Moderator:** {interaction.user}"
                )
                await member.send(embed=dm_embed)
            except:
                pass
                
            await member.kick(reason=f"Kicked by {interaction.user}: {reason}")
            
            embed = self.create_success_embed(
                "User Kicked",
                f"**User:** {member} ({member.id})\n**Reason:** {reason}\n**Moderator:** {interaction.user}"
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_embed(interaction, embed)
            await self._log_command(interaction, "kick", member, reason, None, True)
            
        except discord.Forbidden:
            await self.send_embed(interaction, self.create_error_embed("Permission Error", "I don't have permission to kick this user."))
            await self._log_command(interaction, "kick", member, reason, None, False, "Bot permission denied")
        except Exception as e:
            logger.error(f"Error in kick command: {e}")
            await self.send_embed(interaction, self.create_error_embed("Error", "An error occurred while kicking the user."))
            await self._log_command(interaction, "kick", member, reason, None, False, str(e))

    @app_commands.command(name="mute", description="Mute a user for specified duration")
    @app_commands.describe(
        member="The member to mute",
        duration="Duration of the mute (e.g., 10m, 1h, 1d)",
        reason="Reason for the mute"
    )
    async def mute_user(self, interaction: discord.Interaction, member: discord.Member, duration: str = "10m", reason: str = "No reason provided"):
        """Advanced mute slash command with duration."""
        if not interaction.user.guild_permissions.moderate_members:
            await self.send_embed(interaction, self.create_error_embed("Permission Denied", "You don't have permission to moderate members."))
            return
            
        try:
            # Parse duration
            mute_until = self._parse_duration(duration)
            if not mute_until:
                await self.send_embed(interaction, self.create_error_embed("Invalid Duration", "Please use format like '10m', '1h', '1d'"))
                return
            
            # Apply timeout
            await member.timeout(mute_until, reason=f"Muted by {interaction.user}: {reason}")
            
            # Store mute info
            self.muted_users[member.id] = {
                'until': mute_until,
                'reason': reason,
                'moderator': interaction.user.id
            }
            
            embed = self.create_success_embed(
                "User Muted",
                f"**User:** {member} ({member.id})\n**Duration:** {duration}\n**Reason:** {reason}\n**Moderator:** {interaction.user}"
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_embed(interaction, embed)
            await self._log_command(interaction, "mute", member, reason, duration, True)
            
        except Exception as e:
            logger.error(f"Error in mute command: {e}")
            await self.send_embed(interaction, self.create_error_embed("Error", "An error occurred while muting the user."))
            await self._log_command(interaction, "mute", member, reason, duration, False, str(e))

    @app_commands.command(name="unmute", description="Unmute a user")
    @app_commands.describe(
        member="The member to unmute",
        reason="Reason for the unmute"
    )
    async def unmute_user(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Unmute a user."""
        if not interaction.user.guild_permissions.moderate_members:
            await self.send_embed(interaction, self.create_error_embed("Permission Denied", "You don't have permission to moderate members."))
            return
            
        try:
            await member.timeout(None, reason=f"Unmuted by {interaction.user}: {reason}")
            
            if member.id in self.muted_users:
                del self.muted_users[member.id]
                
            embed = self.create_success_embed(
                "User Unmuted",
                f"**User:** {member} ({member.id})\n**Reason:** {reason}\n**Moderator:** {interaction.user}"
            )
            await self.send_embed(interaction, embed)
            await self._log_command(interaction, "unmute", member, reason, None, True)
            
        except Exception as e:
            await self.send_embed(interaction, self.create_error_embed("Error", "An error occurred while unmuting the user."))
            await self._log_command(interaction, "unmute", member, reason, None, False, str(e))

    @app_commands.command(name="warn", description="Warn a user and log the warning")
    @app_commands.describe(
        member="The member to warn",
        reason="Reason for the warning"
    )
    async def warn_user(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Warn a user and log it."""
        if not interaction.user.guild_permissions.manage_messages:
            await self.send_embed(interaction, self.create_error_embed("Permission Denied", "You don't have permission to warn members."))
            return
            
        try:
            # Send DM warning
            try:
                dm_embed = self.create_warning_embed(
                    "You received a warning",
                    f"**Server:** {interaction.guild.name}\n**Reason:** {reason}\n**Moderator:** {interaction.user}"
                )
                await member.send(embed=dm_embed)
            except:
                pass
                
            embed = self.create_warning_embed(
                "User Warned",
                f"**User:** {member} ({member.id})\n**Reason:** {reason}\n**Moderator:** {interaction.user}"
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_embed(interaction, embed)
            await self._log_command(interaction, "warn", member, reason, None, True)
            
        except Exception as e:
            await self.send_embed(interaction, self.create_error_embed("Error", "An error occurred while warning the user."))
            await self._log_command(interaction, "warn", member, reason, None, False, str(e))

    @app_commands.command(name="clear", description="Delete multiple messages")
    @app_commands.describe(
        amount="Number of messages to delete (max 100)",
        member="Only delete messages from this member"
    )
    async def clear_messages(self, interaction: discord.Interaction, amount: int = 10, member: discord.Member = None):
        """Delete multiple messages with optional user filter."""
        if not interaction.user.guild_permissions.manage_messages:
            await self.send_embed(interaction, self.create_error_embed("Permission Denied", "You don't have permission to manage messages."))
            return
            
        try:
            if amount > 100:
                amount = 100
                
            def check(message):
                if member:
                    return message.author == member
                return True
                
            # Defer the response since this might take a while
            await interaction.response.defer()
            
            deleted = await interaction.channel.purge(limit=amount, check=check)
            
            embed = self.create_success_embed(
                "Messages Cleared",
                f"**Deleted:** {len(deleted)} messages\n**Channel:** {interaction.channel.mention}\n**Moderator:** {interaction.user}"
            )
            
            if member:
                embed.add_field(name="Filter", value=f"Only messages from {member}", inline=False)
                
            await interaction.followup.send(embed=embed, delete_after=5)
            await self._log_command(interaction, "clear", member, f"Cleared {len(deleted)} messages", str(amount), True)
            
            # Update stats
            stats = BotStats.get_or_create()
            stats.total_messages_cleared += len(deleted)
            db.session.commit()
            
        except Exception as e:
            await self.send_embed(interaction, self.create_error_embed("Error", "An error occurred while clearing messages."))
            await self._log_command(interaction, "clear", member, None, str(amount), False, str(e))

    @app_commands.command(name="slowmode", description="Set channel slowmode delay")
    @app_commands.describe(delay="Slowmode delay in seconds (0 to disable)")
    async def set_slowmode(self, interaction: discord.Interaction, delay: int = 0):
        """Set slowmode for the current channel."""
        if not interaction.user.guild_permissions.manage_channels:
            await self.send_embed(interaction, self.create_error_embed("Permission Denied", "You don't have permission to manage channels."))
            return
            
        try:
            await interaction.channel.edit(slowmode_delay=delay)
            
            if delay == 0:
                embed = self.create_success_embed("Slowmode Disabled", f"Slowmode has been disabled in {interaction.channel.mention}")
            else:
                embed = self.create_success_embed("Slowmode Set", f"Slowmode set to **{delay} seconds** in {interaction.channel.mention}")
                
            await self.send_embed(interaction, embed)
            await self._log_command(interaction, "slowmode", None, f"Set to {delay} seconds", str(delay), True)
            
        except Exception as e:
            await self.send_embed(interaction, self.create_error_embed("Error", "An error occurred while setting slowmode."))
            await self._log_command(interaction, "slowmode", None, None, str(delay), False, str(e))

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(ModerationCommands(bot))
