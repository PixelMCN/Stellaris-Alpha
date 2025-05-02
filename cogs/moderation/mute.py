import nextcord
from nextcord.ext import commands
import time
import asyncio
from utils.embed_helper import EmbedHelper
from utils.time_helper import TimeHelper
from utils.error_handler import ErrorHandler
#=============================================================================================================================================================
class MuteCommands(commands.Cog):
    """Commands for muting and unmuting users in text channels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.error_handler = ErrorHandler(bot)
    #=============================================================================================================================================================    
    @nextcord.slash_command(
        name="mute",
        description="Mute a user in text channels"
    )
    async def mute(
        self, 
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="The user to mute"),
        reason: str = nextcord.SlashOption(description="Reason for muting", required=False),
        duration: str = nextcord.SlashOption(
            description="Mute duration (e.g. 10s, 5m, 1h, 2d). Leave empty for indefinite",
            required=False
        )
    ):
        """Mute a user in text channels with optional duration"""
        # Check if the user has permission to mute
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return
            
        # Check if the bot has permission to mute
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to mute themselves
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Invalid User",
                    "You cannot mute yourself."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to mute the bot
        if user.id == self.bot.user.id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Invalid User",
                    "I cannot mute myself."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to mute someone with a higher role
        if interaction.guild.me.top_role <= user.top_role:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Role Hierarchy Error",
                    "I cannot mute this user because their highest role is above or equal to my highest role."
                ),
                ephemeral=True
            )
            return
            
        # Check if the command user has a lower role than the target
        if interaction.user.top_role <= user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Role Hierarchy Error",
                    "You cannot mute this user because their highest role is above or equal to your highest role."
                ),
                ephemeral=True
            )
            return
            
        # Set default reason if none provided
        if not reason:
            reason = "No reason provided"
            
        # Defer response since muting might take time
        await interaction.response.defer(ephemeral=False)
        
        # Find or create muted role
        muted_role = nextcord.utils.get(interaction.guild.roles, name="Muted")
        if not muted_role:
            try:
                # Create the muted role if it doesn't exist
                muted_role = await interaction.guild.create_role(
                    name="Muted",
                    reason="Creating Muted role for mute command",
                    color=nextcord.Color.dark_gray()
                )
                
                # Set permissions for the muted role in all text channels
                for channel in interaction.guild.channels:
                    if isinstance(channel, nextcord.TextChannel):
                        await channel.set_permissions(
                            muted_role,
                            send_messages=False,
                            add_reactions=False,
                            create_public_threads=False,
                            create_private_threads=False,
                            send_messages_in_threads=False
                        )
                    elif isinstance(channel, nextcord.VoiceChannel):
                        await channel.set_permissions(
                            muted_role,
                            speak=False
                        )
            except Exception as e:
                await self.error_handler.handle_command_error(interaction, e, "mute", True)
                return
                
        # Check if user already has the muted role
        if muted_role in user.roles:
            await interaction.followup.send(
                embed=EmbedHelper.error_embed(
                    "Already Muted",
                    f"{user.mention} is already muted."
                ),
                ephemeral=True
            )
            return
            
        # Parse duration if provided
        expiry_time = None
        duration_text = "Indefinite"
        if duration:
            seconds = TimeHelper.parse_time(duration)
            if seconds is None:
                await interaction.followup.send(
                    embed=EmbedHelper.error_embed(
                        "Invalid Duration",
                        "Please provide a valid duration format (e.g. 30s, 5m, 2h, 7d)."
                    ),
                    ephemeral=True
                )
                return
                
            expiry_time = time.time() + seconds
            duration_text = TimeHelper.format_time_remaining(expiry_time)
            
        # Create mute embed for the server logs
        mute_embed = EmbedHelper.moderation_embed(
            "User Muted",
            f"{user.mention} has been muted in text channels.",
            emoji="🔇",
            member=user,
            moderator=interaction.user,
            reason=reason
        )
        
        if expiry_time:
            mute_embed.add_field(name="Duration", value=duration_text, inline=True)
            mute_embed.add_field(name="Expires", value=f"<t:{int(expiry_time)}:F>", inline=True)
        else:
            mute_embed.add_field(name="Duration", value="Indefinite", inline=True)
            
        # Try to DM the user before muting
        try:
            dm_embed = EmbedHelper.moderation_embed(
                "You've Been Muted",
                f"You have been muted in **{interaction.guild.name}**",
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
            mute_embed.add_field(name="Note", value="Could not DM user about the mute action", inline=False)
            
        # Mute the user
        try:
            await user.add_roles(
                muted_role,
                reason=f"Muted by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
            )
            
            # Send confirmation to the channel
            await interaction.followup.send(embed=mute_embed)
            
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=mute_embed)
            except:
                pass
                
            # If duration is set, schedule unmute
            if expiry_time:
                # Schedule the unmute task
                self.bot.loop.create_task(self.schedule_unmute(
                    user.id, 
                    interaction.guild.id, 
                    expiry_time, 
                    interaction.user.id, 
                    reason
                ))
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "mute", True)
    #=============================================================================================================================================================        
    @nextcord.slash_command(
        name="unmute",
        description="Unmute a user in text channels"
    )
    async def unmute(
        self, 
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="The user to unmute"),
        reason: str = nextcord.SlashOption(description="Reason for unmuting", required=False)
    ):
        """Unmute a user in text channels"""
        # Check if the user has permission to unmute
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return
            
        # Check if the bot has permission to unmute
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return
            
        # Find muted role
        muted_role = nextcord.utils.get(interaction.guild.roles, name="Muted")
        if not muted_role:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "No Muted Role",
                    "There is no 'Muted' role in this server."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is not muted
        if muted_role not in user.roles:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Not Muted",
                    f"{user.mention} is not muted."
                ),
                ephemeral=True
            )
            return
            
        # Set default reason if none provided
        if not reason:
            reason = "No reason provided"
            
        # Defer response since unmuting might take time
        await interaction.response.defer(ephemeral=False)
        
        # Create unmute embed
        unmute_embed = EmbedHelper.moderation_embed(
            "User Unmuted",
            f"{user.mention} has been unmuted in text channels.",
            emoji="🔊",
            member=user,
            moderator=interaction.user,
            reason=reason
        )
        
        # Try to DM the user about unmuting
        try:
            dm_embed = EmbedHelper.moderation_embed(
                "You've Been Unmuted",
                f"You have been unmuted in **{interaction.guild.name}**",
                emoji="🔊",
                moderator=interaction.user,
                reason=reason
            )
            
            await user.send(embed=dm_embed)
        except:
            # User might have DMs disabled
            unmute_embed.add_field(name="Note", value="Could not DM user about the unmute action", inline=False)
            
        # Unmute the user
        try:
            await user.remove_roles(
                muted_role,
                reason=f"Unmuted by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
            )
            
            # Send confirmation to the channel
            await interaction.followup.send(embed=unmute_embed)
            
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=unmute_embed)
            except:
                pass
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "unmute", True)
    #=============================================================================================================================================================        
    async def schedule_unmute(self, user_id, guild_id, expiry_time, moderator_id, original_reason):
        """Schedule a user to be unmuted after a duration"""
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
            
        # Get the muted role
        muted_role = nextcord.utils.get(guild.roles, name="Muted")
        if not muted_role or muted_role not in user.roles:
            return
            
        # Get the moderator
        moderator = guild.get_member(moderator_id) or await self.bot.fetch_user(moderator_id)
        
        # Unmute the user
        try:
            await user.remove_roles(
                muted_role,
                reason=f"Automatic unmute after duration | Originally muted by {moderator} for: {original_reason}"
            )
            
            # Create unmute embed
            unmute_embed = EmbedHelper.moderation_embed(
                "User Automatically Unmuted",
                f"{user.mention} has been automatically unmuted after the set duration.",
                emoji="🔊",
                member=user,
                reason=f"Duration expired (Originally muted for: {original_reason})"
            )
            
            # Try to send to mod-logs channel if it exists
            log_channel = nextcord.utils.get(guild.channels, name="mod-logs")
            if log_channel:
                await log_channel.send(embed=unmute_embed)
                
            # Try to DM the user about unmuting
            try:
                dm_embed = EmbedHelper.moderation_embed(
                    "You've Been Unmuted",
                    f"You have been automatically unmuted in **{guild.name}** after the set duration.",
                    emoji="🔊",
                    reason=f"Duration expired (Originally muted for: {original_reason})"
                )
                
                await user.send(embed=dm_embed)
            except:
                pass
                
        except:
            # If there's an error, just silently fail
            pass
#=============================================================================================================================================================