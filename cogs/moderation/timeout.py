import nextcord
import random
from nextcord.ext import commands
from nextcord import Interaction
from datetime import timedelta
from enum import Enum
from typing import Optional


class DurationType(str, Enum):
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"


class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = bot.error_handler

    # TIMEOUT COMMANDS
    #=============================================================================================================================================================
    @nextcord.slash_command(name="timeout", description="Manage member timeouts")
    async def timeout(self, interaction: Interaction):
        """Parent command for timeout-related functionality"""
        pass
    
    # TIMEOUT ADD COMMAND
    #=============================================================================================================================================================
    @timeout.subcommand(
        name="add", 
        description="Timeout a member for a specified duration"
    )
    async def timeout_add(
        self, 
        interaction: Interaction, 
        member: nextcord.Member = nextcord.SlashOption(
            description="The member to timeout",
            required=True
        ), 
        duration: str = nextcord.SlashOption(
            description="Duration (e.g., 10s, 5m, 2h, 3d)",
            required=True
        ),
        reason: Optional[str] = nextcord.SlashOption(
            description="Reason for timeout (optional)",
            required=False
        )
    ):
        """
        Timeout a member for a specified duration.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        member: The member to timeout
        duration: Duration in format like 10s, 5m, 2h, 3d (seconds, minutes, hours, days)
        reason: Optional reason for the timeout
        """
        try:
            # Check if user has permission to moderate members
            if not interaction.user.guild_permissions.moderate_members:
                await interaction.response.send_message(
                    "❌ You need the **Moderate Members** permission to use this command.", 
                    ephemeral=True
                )
                return
            
            # Check if the bot can timeout the target member
            if not interaction.guild.me.guild_permissions.moderate_members:
                await interaction.response.send_message(
                    "❌ I don't have the **Moderate Members** permission required to timeout users.",
                    ephemeral=True
                )
                return
                
            # Check if trying to timeout someone with higher role
            if member.top_role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    f"❌ I cannot timeout {member.mention} as their highest role is above or equal to mine.",
                    ephemeral=True
                )
                return
                
            # Check if trying to timeout server owner
            if member.id == interaction.guild.owner_id:
                await interaction.response.send_message(
                    "❌ I cannot timeout the server owner.",
                    ephemeral=True
                )
                return
                
            # Check if trying to timeout themselves
            if member.id == interaction.user.id:
                await interaction.response.send_message(
                    "❌ You cannot timeout yourself.",
                    ephemeral=True
                )
                return
                
            # Check if user has permission over target
            if interaction.user.id != interaction.guild.owner_id and member.top_role >= interaction.user.top_role:
                await interaction.response.send_message(
                    f"❌ You cannot timeout {member.mention} as their highest role is above or equal to yours.",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # List of timeout reasons
            timeout_reasons = [
                "Breaking server rules",
                "Spamming in channels",
                "Disruptive behavior",
                "Excessive toxicity",
                "Inappropriate content",
                "Harassment of members",
                "Ignoring moderator warnings"
            ]

            # Select a random reason if reason is not provided
            if reason is None:
                reason = random.choice(timeout_reasons)

            # Parse duration string (e.g., 10s, 5m, 2h, 3d)
            import re
            match = re.fullmatch(r"(\d+)([smhd])", duration.strip().lower())
            if not match:
                await interaction.followup.send(
                    "❌ Invalid duration format. Please use formats like: `10s`, `5m`, `2h`, `3d` " +
                    "(seconds, minutes, hours, days).", 
                    ephemeral=True
                )
                return

            value, unit = int(match.group(1)), match.group(2)
            
            # Check for zero values
            if value == 0:
                await interaction.followup.send(
                    "❌ Duration must be greater than 0.",
                    ephemeral=True
                )
                return
                
            # Check for Discord's maximum timeout limit (28 days)
            if unit == "d" and value > 28:
                await interaction.followup.send(
                    "❌ Discord only allows timeouts up to 28 days.",
                    ephemeral=True
                )
                return
                
            # Convert duration to timedelta and human-readable text
            if unit == "s":
                time_delta = timedelta(seconds=value)
                duration_text = f"{value} second{'s' if value != 1 else ''}"
            elif unit == "m":
                time_delta = timedelta(minutes=value)
                duration_text = f"{value} minute{'s' if value != 1 else ''}"
            elif unit == "h":
                time_delta = timedelta(hours=value)
                duration_text = f"{value} hour{'s' if value != 1 else ''}"
            elif unit == "d":
                time_delta = timedelta(days=value)
                duration_text = f"{value} day{'s' if value != 1 else ''}"
            else:
                await interaction.followup.send(
                    "❌ Invalid duration unit. Use s, m, h, or d.", 
                    ephemeral=True
                )
                return

            # Check if member is already timed out
            if member.timed_out:
                await interaction.followup.send(
                    f"⚠️ {member.mention} is already timed out. Their timeout has been updated to {duration_text}.",
                    ephemeral=False
                )
            
            # Apply timeout 
            await member.timeout(time_delta, reason=f"{reason} - By {interaction.user}")
            
            # Create and send embed
            embed = nextcord.Embed(
                title="⏳ Member Timed Out", 
                color=nextcord.Color.orange(),
                timestamp=interaction.created_at
            )
            embed.add_field(name="Member", value=f"{member.mention} ({member.name})", inline=True)
            embed.add_field(name="Duration", value=duration_text, inline=True)
            embed.add_field(name="Expires", value=f"<t:{int((interaction.created_at + time_delta).timestamp())}:R>", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await interaction.followup.send(embed=embed)
            
            # Send a direct message to the timed out member
            try:
                dm_embed = nextcord.Embed(
                    title="You Have Been Timed Out",
                    description=f"You have been timed out in **{interaction.guild.name}**.",
                    color=nextcord.Color.red(),
                    timestamp=interaction.created_at
                )
                dm_embed.add_field(name="Duration", value=duration_text, inline=True)
                dm_embed.add_field(name="Expires", value=f"<t:{int((interaction.created_at + time_delta).timestamp())}:R>", inline=True)
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
                dm_embed.set_footer(text=f"If you believe this was a mistake, please contact the server staff.")
                
                await member.send(embed=dm_embed)
            except nextcord.HTTPException:
                # Add a note to the original embed if DM fails
                embed.add_field(name="Note", value="⚠️ Could not send DM notification to the user.", inline=False)
                await interaction.edit_original_message(embed=embed)
                
        except nextcord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to timeout this member. Please check my role permissions.", 
                ephemeral=True
            )
        except Exception as e:
            # Let the global error handler handle other exceptions
            await self.error_handler.handle_command_error(interaction, e, "timeout add")
    #=============================================================================================================================================================
    
    # TIMEOUT REMOVE COMMAND
    #=============================================================================================================================================================
    @timeout.subcommand(
        name="remove", 
        description="Remove timeout from a member"
    )
    async def timeout_remove(
        self, 
        interaction: Interaction, 
        member: nextcord.Member = nextcord.SlashOption(
            description="The member to remove timeout from",
            required=True
        ), 
        reason: Optional[str] = nextcord.SlashOption(
            description="Reason for removing timeout (optional)",
            required=False
        )
    ):
        """
        Remove timeout from a member.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        member: The member to remove timeout from
        reason: Optional reason for removing the timeout
        """
        try:
            # Check if user has permission to moderate members
            if not interaction.user.guild_permissions.moderate_members:
                await interaction.response.send_message(
                    "❌ You need the **Moderate Members** permission to use this command.", 
                    ephemeral=True
                )
                return
                
            # Check if the bot can remove timeout
            if not interaction.guild.me.guild_permissions.moderate_members:
                await interaction.response.send_message(
                    "❌ I don't have the **Moderate Members** permission required to remove timeouts.",
                    ephemeral=True
                )
                return
                
            # Check if the member is actually timed out
            if not member.timed_out:
                await interaction.response.send_message(
                    f"ℹ️ {member.mention} is not currently timed out.",
                    ephemeral=True
                )
                return
                
            # Default reason if none provided
            if reason is None:
                reason = f"Timeout removed by {interaction.user}"
            
            # Remove timeout by setting it to None
            await member.timeout(None, reason=f"{reason} - By {interaction.user}")
            
            # Create embed for confirmation
            embed = nextcord.Embed(
                title="⏳ Timeout Removed", 
                color=nextcord.Color.green(),
                timestamp=interaction.created_at
            )
            embed.add_field(name="Member", value=f"{member.mention} ({member.name})", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await interaction.response.send_message(embed=embed)
            
            # Send DM to notify the user
            try:
                dm_embed = nextcord.Embed(
                    title="Timeout Removed",
                    description=f"Your timeout in **{interaction.guild.name}** has been removed.",
                    color=nextcord.Color.green(),
                    timestamp=interaction.created_at
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
                
                await member.send(embed=dm_embed)
            except nextcord.HTTPException:
                pass  # Silently fail if DM can't be sent
                
        except nextcord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to modify timeouts for this member.", 
                ephemeral=True
            )
        except Exception as e:
            # Let the global error handler handle other exceptions
            await self.error_handler.handle_command_error(interaction, e, "timeout remove")
    #=============================================================================================================================================================