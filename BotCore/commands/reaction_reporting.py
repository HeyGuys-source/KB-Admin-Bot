#!/usr/bin/env python3
"""
Reaction-Based Message Reporting System
Handles message reporting via emoji reactions with decorative embeds
"""

import discord
from discord.ext import commands
from .base_command import BaseCommand
from utils.logger import setup_logger

logger = setup_logger('reaction_reporting')

class ReactionReporting(BaseCommand):
    """Reaction-based message reporting system."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.report_emoji_id = 1406321078086668419  # The custom emoji ID for reporting
        self.report_channel_id = 1410841913111875675  # Channel to send reports to
        
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle reaction additions for message reporting."""
        try:
            # Ignore bot reactions
            if user.bot:
                return
                
            # Check if it's the report emoji
            if hasattr(reaction.emoji, 'id') and reaction.emoji.id == self.report_emoji_id:
                await self._handle_message_report(reaction, user)
                
        except Exception as e:
            logger.error(f"Error in reaction reporting: {e}")
            
    async def _handle_message_report(self, reaction, reporter):
        """Handle a message report via reaction."""
        try:
            message = reaction.message
            guild = message.guild
            
            # Remove the reaction after a few seconds
            await asyncio.sleep(2)
            try:
                await reaction.remove(reporter)
            except:
                pass  # Ignore if we can't remove the reaction
                
            # Get the report channel
            report_channel = self.bot.get_channel(self.report_channel_id)
            if not report_channel:
                logger.error(f"Report channel {self.report_channel_id} not found")
                return
                
            # Create decorative report embed
            embed = discord.Embed(
                title="🚨 Message Report",
                description="A message has been reported by a user",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            
            # Add reporter information
            embed.add_field(
                name="📋 Reporter Information",
                value=f"**User ID:** {reporter.id}\n"
                      f"**Username:** {reporter.name}#{reporter.discriminator}\n"
                      f"**Display Name:** {reporter.display_name}",
                inline=False
            )
            
            # Add reported user information
            reported_user = message.author
            embed.add_field(
                name="⚠️ Reported User Information", 
                value=f"**User ID:** {reported_user.id}\n"
                      f"**Username:** {reported_user.name}#{reported_user.discriminator}\n"
                      f"**Display Name:** {reported_user.display_name}",
                inline=False
            )
            
            # Add message information
            message_content = message.content if message.content else "*[No text content]*"
            if len(message_content) > 1000:
                message_content = message_content[:1000] + "..."
                
            embed.add_field(
                name="💬 Reported Message",
                value=f"**Content:** {message_content}\n"
                      f"**Channel:** {message.channel.mention}\n"
                      f"**Message ID:** {message.id}\n"
                      f"**Jump to Message:** [Click Here]({message.jump_url})",
                inline=False
            )
            
            # Add attachment info if any
            if message.attachments:
                attachment_info = []
                for attachment in message.attachments:
                    attachment_info.append(f"• {attachment.filename} ({attachment.size} bytes)")
                    
                embed.add_field(
                    name="📎 Attachments",
                    value="\n".join(attachment_info[:5]),  # Limit to 5 attachments
                    inline=False
                )
                
            # Add embeds info if any
            if message.embeds:
                embed.add_field(
                    name="📄 Message Contains Embeds",
                    value=f"This message contains {len(message.embeds)} embed(s)",
                    inline=False
                )
                
            # Add server information
            embed.add_field(
                name="🏠 Server Information",
                value=f"**Server:** {guild.name}\n**Server ID:** {guild.id}",
                inline=False
            )
            
            # Set thumbnails
            embed.set_thumbnail(url=reported_user.display_avatar.url)
            
            # Add footer with additional info
            embed.set_footer(
                text=f"Report submitted • Message sent {message.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
                icon_url=reporter.display_avatar.url
            )
            
            # Add reaction count info
            if reaction.count > 1:
                embed.add_field(
                    name="📊 Report Count",
                    value=f"This message has been reported {reaction.count} time(s)",
                    inline=False
                )
                
            # Send the report
            await report_channel.send(embed=embed)
            
            # Add action buttons for moderators
            view = ReportActionView(message, reported_user, reporter)
            action_embed = discord.Embed(
                title="🔧 Moderator Actions",
                description="Choose an action to take on this report:",
                color=discord.Color.blue()
            )
            
            await report_channel.send(embed=action_embed, view=view)
            
            logger.info(f"Message report sent - Reporter: {reporter.id}, Reported: {reported_user.id}, Message: {message.id}")
            
        except Exception as e:
            logger.error(f"Error handling message report: {e}")


class ReportActionView(discord.ui.View):
    """Action buttons for message reports."""
    
    def __init__(self, message, reported_user, reporter):
        super().__init__(timeout=3600)  # 1 hour timeout
        self.message = message
        self.reported_user = reported_user
        self.reporter = reporter
        
    @discord.ui.button(label="Delete Message", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Delete the reported message."""
        try:
            await self.message.delete()
            
            embed = discord.Embed(
                title="✅ Action Taken",
                description=f"Message deleted by {interaction.user.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.NotFound:
            embed = discord.Embed(
                title="❌ Message Not Found",
                description="The message has already been deleted or could not be found.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while deleting the message.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            
    @discord.ui.button(label="Warn User", style=discord.ButtonStyle.secondary, emoji="⚠️")
    async def warn_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Warn the reported user."""
        try:
            # Send DM warning
            try:
                dm_embed = discord.Embed(
                    title="⚠️ Warning",
                    description=f"Your message in {self.message.guild.name} has been reported and reviewed by moderators. Please follow server rules.",
                    color=discord.Color.yellow()
                )
                await self.reported_user.send(embed=dm_embed)
                dm_status = "✅ DM sent successfully"
            except:
                dm_status = "❌ Could not send DM (user has DMs disabled)"
                
            embed = discord.Embed(
                title="⚠️ User Warned",
                description=f"Warning issued to {self.reported_user.mention} by {interaction.user.mention}\n{dm_status}",
                color=discord.Color.yellow()
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while warning the user.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            
    @discord.ui.button(label="No Action Needed", style=discord.ButtonStyle.success, emoji="✅")
    async def no_action(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mark the report as resolved with no action."""
        embed = discord.Embed(
            title="✅ Report Resolved",
            description=f"Report marked as resolved by {interaction.user.mention} - No action taken",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
        
    @discord.ui.button(label="Jump to Message", style=discord.ButtonStyle.secondary, emoji="🔗")
    async def jump_to_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Send the message jump URL."""
        embed = discord.Embed(
            title="🔗 Jump to Reported Message",
            description=f"[Click here to jump to the reported message]({self.message.jump_url})",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# Import asyncio for the sleep function
import asyncio

async def setup(bot):
    """Setup function to add the reaction reporting system to the bot."""
    await bot.add_cog(ReactionReporting(bot))