import nextcord
from nextcord.ext import commands
import time
import asyncio
from utils.embed_helper import EmbedHelper
from utils.time_helper import TimeHelper
from utils.error_handler import ErrorHandler
#=============================================================================================================================================================
class BanCommands(commands.Cog):
    """Commands for banning and unbanning users"""
    
    def __init__(self, bot):
        self.bot = bot
        self.error_handler = ErrorHandler(bot)
    #=============================================================================================================================================================
    @nextcord.slash_command(
        name="ban",
        description="Ban a user from the server"
    )
    async def ban(
        self, 
        interaction: nextcord.Interaction,
        user: nextcord.User = nextcord.SlashOption(description="The user to ban"),  # Changed from Member to User
        reason: str = nextcord.SlashOption(description="Reason for the ban", required=False),
        delete_messages: str = nextcord.SlashOption(
            name="delete-messages",
            description="Delete message history",
            choices={"Don't Delete Any": "0", "Last 24 Hours": "1", "Last 7 Days": "7"},
            required=False,
            default="0"
        ),
        duration: str = nextcord.SlashOption(
            description="Ban duration (e.g. 1h, 2d, 7d). Leave empty for permanent ban",
            required=False
        )
    ):
        """Ban a user from the server with optional duration"""
        # Check if the user has permission to ban
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Ban Members"),
                ephemeral=True
            )
            return
            
        # Check if the bot has permission to ban
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Ban Members"),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to ban themselves
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Invalid User",
                    "You cannot ban yourself."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to ban the bot
        if user.id == self.bot.user.id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Invalid User",
                    "I cannot ban myself."
                ),
                ephemeral=True
            )
            return
        
        # Get the member object if the user is in the guild
        member = interaction.guild.get_member(user.id)
        
        # Only perform role hierarchy checks if the user is a member of the guild
        if member is not None:
            # Check if the user is trying to ban someone with a higher role
            if interaction.guild.me.top_role <= member.top_role:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Role Hierarchy Error",
                        "I cannot ban this user because their highest role is above or equal to my highest role."
                    ),
                    ephemeral=True
                )
                return
                
            # Check if the command user has a lower role than the target
            if interaction.user.top_role <= member.top_role and interaction.user.id != interaction.guild.owner_id:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Role Hierarchy Error",
                        "You cannot ban this user because their highest role is above or equal to your highest role."
                    ),
                    ephemeral=True
                )
                return
            
        # Set default reason if none provided
        if not reason:
            reason = "No reason provided"
            
        # Parse duration if provided
        expiry_time = None
        duration_text = "Permanent"
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
            
        # Defer response since ban might take time
        await interaction.response.defer(ephemeral=False)
        
        # Convert delete_messages to seconds (from days)
        delete_seconds = int(delete_messages) * 24 * 60 * 60  # Convert days to seconds
        
        # Create ban embed for the server logs
        ban_embed = EmbedHelper.moderation_embed(
            "User Banned",
            f"{user.mention} has been banned from the server.",
            emoji="🔨",
            member=user,
            moderator=interaction.user,
            reason=reason
        )
        
        if expiry_time:
            ban_embed.add_field(name="Duration", value=duration_text, inline=True)
            ban_embed.add_field(name="Expires", value=f"<t:{int(expiry_time)}:F>", inline=True)
        else:
            ban_embed.add_field(name="Duration", value="Permanent", inline=True)
            
        # Try to DM the user before banning
        try:
            dm_embed = EmbedHelper.moderation_embed(
                "You've Been Banned",
                f"You have been banned from **{interaction.guild.name}**",
                emoji="🔨",
                moderator=interaction.user,
                reason=reason
            )
            
            if expiry_time:
                dm_embed.add_field(name="Duration", value=duration_text, inline=True)
                dm_embed.add_field(name="Expires", value=f"<t:{int(expiry_time)}:F>", inline=True)
            else:
                dm_embed.add_field(name="Duration", value="Permanent", inline=True)
                
            await user.send(embed=dm_embed)
        except:
            # User might have DMs disabled
            ban_embed.add_field(name="Note", value="Could not DM user about the ban", inline=False)
            
        # Ban the user
        try:
            await interaction.guild.ban(
                user, 
                reason=f"Banned by {interaction.user} ({interaction.user.id}) | Reason: {reason}",
                delete_message_seconds=delete_seconds
            )
            
            # Store temporary ban in database if duration is set
            if expiry_time:
                # This is where you would store the temporary ban in a database
                # For example:
                # await self.bot.db.add_temp_ban(user.id, interaction.guild.id, expiry_time)
                pass
                
            # Send confirmation to the channel
            await interaction.followup.send(embed=ban_embed)
            
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=ban_embed)
            except:
                pass
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "ban", True)
    #=============================================================================================================================================================
    @nextcord.slash_command(
        name="unban",
        description="Unban a user from the server"
    )
    async def unban(
        self, 
        interaction: nextcord.Interaction,
        user_id: str = nextcord.SlashOption(description="The ID of the user to unban"),
        reason: str = nextcord.SlashOption(description="Reason for the unban", required=False)
    ):
        """Unban a user from the server"""
        # Check if the user has permission to unban
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Ban Members"),
                ephemeral=True
            )
            return
            
        # Check if the bot has permission to unban
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Ban Members"),
                ephemeral=True
            )
            return
            
        # Set default reason if none provided
        if not reason:
            reason = "No reason provided"
            
        # Defer response since fetching bans might take time
        await interaction.response.defer(ephemeral=False)
        
        # Validate user ID format
        try:
            user_id = int(user_id)
        except ValueError:
            await interaction.followup.send(
                embed=EmbedHelper.error_embed(
                    "Invalid User ID",
                    "Please provide a valid user ID (numbers only)."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is banned
        try:
            ban_entry = None
            banned_users = [entry async for entry in interaction.guild.bans()]
            for entry in banned_users:
                if entry.user.id == user_id:
                    ban_entry = entry
                    break
                    
            if not ban_entry:
                await interaction.followup.send(
                    embed=EmbedHelper.error_embed(
                        "User Not Banned",
                        f"User with ID `{user_id}` is not banned from this server."
                    ),
                    ephemeral=True
                )
                return
                
            # Unban the user
            await interaction.guild.unban(
                ban_entry.user,
                reason=f"Unbanned by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
            )
            
            # Create unban embed
            unban_embed = EmbedHelper.moderation_embed(
                "User Unbanned",
                f"**{ban_entry.user}** (`{ban_entry.user.id}`) has been unbanned from the server.",
                emoji="🔓",
                moderator=interaction.user,
                reason=reason
            )
            
            # Send confirmation to the channel
            await interaction.followup.send(embed=unban_embed)
            
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=unban_embed)
            except:
                pass
                
            # Remove from temp bans if exists
            # This is where you would remove the temporary ban from a database
            # For example:
            # await self.bot.db.remove_temp_ban(user_id, interaction.guild.id)
            
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "unban", True)
    #=============================================================================================================================================================    
    @nextcord.slash_command(
        name="baninfo",
        description="Get information about a banned user"
    )
    async def baninfo(
        self, 
        interaction: nextcord.Interaction,
        user_id: str = nextcord.SlashOption(description="The ID of the banned user")
    ):
        """Get information about a banned user"""
        # Check if the user has permission to view bans
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Ban Members"),
                ephemeral=True
            )
            return
            
        # Defer response since fetching bans might take time
        await interaction.response.defer(ephemeral=False)
        
        # Validate user ID format
        try:
            user_id = int(user_id)
        except ValueError:
            await interaction.followup.send(
                embed=EmbedHelper.error_embed(
                    "Invalid User ID",
                    "Please provide a valid user ID (numbers only)."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is banned
        try:
            ban_entry = None
            banned_users = [entry async for entry in interaction.guild.bans()]
            for entry in banned_users:
                if entry.user.id == user_id:
                    ban_entry = entry
                    break
                    
            if not ban_entry:
                await interaction.followup.send(
                    embed=EmbedHelper.error_embed(
                        "User Not Banned",
                        f"User with ID `{user_id}` is not banned from this server."
                    ),
                    ephemeral=True
                )
                return
                
            # Create ban info embed
            info_embed = EmbedHelper.info_embed(
                "Ban Information",
                f"Information about banned user **{ban_entry.user}** (`{ban_entry.user.id}`)"
            )
            
            info_embed.add_field(name="User", value=f"{ban_entry.user} (`{ban_entry.user.id}`)", inline=False)
            info_embed.add_field(name="Reason", value=ban_entry.reason or "No reason provided", inline=False)
            
            # Add user avatar if available
            if ban_entry.user.avatar:
                info_embed.set_thumbnail(url=ban_entry.user.avatar.url)
                
            # Check if there's a temporary ban in the database
            # This is where you would check for temporary ban info
            # For example:
            # temp_ban = await self.bot.db.get_temp_ban(user_id, interaction.guild.id)
            # if temp_ban:
            #     info_embed.add_field(name="Duration", value=TimeHelper.format_time_remaining(temp_ban.expiry), inline=True)
            #     info_embed.add_field(name="Expires", value=f"<t:{int(temp_ban.expiry)}:F>", inline=True)
            
            await interaction.followup.send(embed=info_embed)
            
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "baninfo", True)
#=============================================================================================================================================================