import nextcord
from nextcord.ext import commands
import time
import asyncio
from utils.embed_helper import EmbedHelper
from utils.time_helper import TimeHelper
from utils.error_handler import ErrorHandler
#=============================================================================================================================================================
class DeafenCommands(commands.Cog):
    """Commands for deafening and undeafening users in voice channels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.error_handler = ErrorHandler(bot)
    #=============================================================================================================================================================
    @nextcord.slash_command(
        name="deafen",
        description="Deafen a user in a voice channel"
    )
    async def deafen(
        self, 
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="The user to deafen"),
        reason: str = nextcord.SlashOption(description="Reason for deafening", required=False),
        duration: str = nextcord.SlashOption(
            description="Deafen duration (e.g. 1h, 2d, 7d). Leave empty for indefinite",
            required=False
        )
    ):
        """Deafen a user in a voice channel with optional duration"""
        # Check if the user has permission to deafen
        if not interaction.user.guild_permissions.deafen_members:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Deafen Members"),
                ephemeral=True
            )
            return
            
        # Check if the bot has permission to deafen
        if not interaction.guild.me.guild_permissions.deafen_members:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Deafen Members"),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to deafen themselves
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Invalid User",
                    "You cannot deafen yourself."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to deafen the bot
        if user.id == self.bot.user.id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Invalid User",
                    "I cannot deafen myself."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to deafen someone with a higher role
        if interaction.guild.me.top_role <= user.top_role:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Role Hierarchy Error",
                    "I cannot deafen this user because their highest role is above or equal to my highest role."
                ),
                ephemeral=True
            )
            return
            
        # Check if the command user has a lower role than the target
        if interaction.user.top_role <= user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Role Hierarchy Error",
                    "You cannot deafen this user because their highest role is above or equal to your highest role."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is in a voice channel
        if not user.voice:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Not in Voice Channel",
                    f"{user.mention} is not in a voice channel."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is already deafened
        if user.voice.deaf:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Already Deafened",
                    f"{user.mention} is already deafened."
                ),
                ephemeral=True
            )
            return
            
        # Set default reason if none provided
        if not reason:
            reason = "No reason provided"
            
        # Parse duration if provided
        expiry_time = None
        duration_text = "Indefinite"
        if duration:
            seconds = TimeHelper.parse_time(duration)
            if seconds is None:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Invalid Duration",
                        "Please provide a valid duration format (e.g. 30s, 5m, 2h, 7d)."
                    ),
                    ephemeral=True
                )
                return
                
            expiry_time = time.time() + seconds
            duration_text = TimeHelper.format_time_remaining(expiry_time)
            
        # Defer response since deafening might take time
        await interaction.response.defer(ephemeral=False)
        
        # Create deafen embed for the server logs
        deafen_embed = EmbedHelper.moderation_embed(
            "User Deafened",
            f"{user.mention} has been deafened in voice channels.",
            emoji="🔇",
            member=user,
            moderator=interaction.user,
            reason=reason
        )
        
        if expiry_time:
            deafen_embed.add_field(name="Duration", value=duration_text, inline=True)
            deafen_embed.add_field(name="Expires", value=f"<t:{int(expiry_time)}:F>", inline=True)
        else:
            deafen_embed.add_field(name="Duration", value="Indefinite", inline=True)
            
        # Try to DM the user before deafening
        try:
            dm_embed = EmbedHelper.moderation_embed(
                "You've Been Deafened",
                f"You have been deafened in voice channels in **{interaction.guild.name}**",
                emoji="🔇",
                moderator=interaction.user,
                reason=reason
            )
            
            if expiry_time:
                dm_embed.add_field(name="Duration", value=duration_text, inline=True)
                dm_embed.add_field(name="Expires", value=f"<t:{int(expiry_time)}:F>", inline=True)
            else:
                dm_embed.add_field(name="Duration", value="Indefinite", inline=True)
                
            await user.send(embed=dm_embed)
        except:
            # User might have DMs disabled
            deafen_embed.add_field(name="Note", value="Could not DM user about the deafen action", inline=False)
            
        # Deafen the user
        try:
            await user.edit(
                deafen=True,
                reason=f"Deafened by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
            )
            
            # Send confirmation to the channel
            await interaction.followup.send(embed=deafen_embed)
            
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=deafen_embed)
            except:
                pass
                
            # If duration is set, schedule undeafen
            if expiry_time:
                # Schedule the undeafen task
                self.bot.loop.create_task(self.schedule_undeafen(
                    user.id, 
                    interaction.guild.id, 
                    expiry_time, 
                    interaction.user.id, 
                    reason
                ))
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "deafen", True)
    #=============================================================================================================================================================  
    @nextcord.slash_command(
        name="undeafen",
        description="Undeafen a user in a voice channel"
    )
    async def undeafen(
        self, 
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="The user to undeafen"),
        reason: str = nextcord.SlashOption(description="Reason for undeafening", required=False)
    ):
        """Undeafen a user in a voice channel"""
        # Check if the user has permission to undeafen
        if not interaction.user.guild_permissions.deafen_members:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Deafen Members"),
                ephemeral=True
            )
            return
            
        # Check if the bot has permission to undeafen
        if not interaction.guild.me.guild_permissions.deafen_members:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Deafen Members"),
                ephemeral=True
            )
            return
            
        # Check if the user is in a voice channel
        if not user.voice:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Not in Voice Channel",
                    f"{user.mention} is not in a voice channel."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is not deafened
        if not user.voice.deaf:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Not Deafened",
                    f"{user.mention} is not deafened."
                ),
                ephemeral=True
            )
            return
            
        # Set default reason if none provided
        if not reason:
            reason = "No reason provided"
            
        # Defer response since undeafening might take time
        await interaction.response.defer(ephemeral=False)
        
        # Create undeafen embed
        undeafen_embed = EmbedHelper.moderation_embed(
            "User Undeafened",
            f"{user.mention} has been undeafened in voice channels.",
            emoji="🔊",
            member=user,
            moderator=interaction.user,
            reason=reason
        )
        
        # Try to DM the user about undeafening
        try:
            dm_embed = EmbedHelper.moderation_embed(
                "You've Been Undeafened",
                f"You have been undeafened in voice channels in **{interaction.guild.name}**",
                emoji="🔊",
                moderator=interaction.user,
                reason=reason
            )
            
            await user.send(embed=dm_embed)
        except:
            # User might have DMs disabled
            undeafen_embed.add_field(name="Note", value="Could not DM user about the undeafen action", inline=False)
            
        # Undeafen the user
        try:
            await user.edit(
                deafen=False,
                reason=f"Undeafened by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
            )
            
            # Send confirmation to the channel
            await interaction.followup.send(embed=undeafen_embed)
            
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=undeafen_embed)
            except:
                pass
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "undeafen", True)
            
    async def schedule_undeafen(self, user_id, guild_id, expiry_time, moderator_id, original_reason):
        """Schedule a user to be undeafened after a duration"""
        # Calculate seconds to wait
        seconds_to_wait = expiry_time - time.time()
        if seconds_to_wait <= 0:
            return
            
        # Wait until the expiry time
        await asyncio.sleep(seconds_to_wait)
        
        # Get the guild and user
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
            
        # Get the user
        user = guild.get_member(user_id)
        if not user:
            return
            
        # Check if the user is still in a voice channel and still deafened
        if not user.voice or not user.voice.deaf:
            return
            
        # Get the moderator
        moderator = guild.get_member(moderator_id) or await self.bot.fetch_user(moderator_id)
        
        # Undeafen the user
        try:
            await user.edit(
                deafen=False,
                reason=f"Automatic undeafen after duration | Originally deafened by {moderator} for: {original_reason}"
            )
            
            # Create undeafen embed
            undeafen_embed = EmbedHelper.moderation_embed(
                "User Automatically Undeafened",
                f"{user.mention} has been automatically undeafened after the set duration.",
                emoji="🔊",
                member=user,
                reason=f"Duration expired (Originally deafened for: {original_reason})"
            )
            
            # Try to send to mod-logs channel if it exists
            log_channel = nextcord.utils.get(guild.channels, name="mod-logs")
            if log_channel:
                await log_channel.send(embed=undeafen_embed)
                
            # Try to DM the user about undeafening
            try:
                dm_embed = EmbedHelper.moderation_embed(
                    "You've Been Undeafened",
                    f"You have been automatically undeafened in **{guild.name}** after the set duration.",
                    emoji="🔊",
                    reason=f"Duration expired (Originally deafened for: {original_reason})"
                )
                
                await user.send(embed=dm_embed)
            except:
                pass
                
        except:
            # If there's an error, just silently fail
            pass
#=============================================================================================================================================================