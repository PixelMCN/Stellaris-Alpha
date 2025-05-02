import nextcord
from nextcord.ext import commands
import time
from utils.embed_helper import EmbedHelper
from utils.error_handler import ErrorHandler
from utils.time_helper import TimeHelper
#=============================================================================================================================================================
class KickCommands(commands.Cog):
    """Commands for kicking users from the server"""
    
    def __init__(self, bot):
        self.bot = bot
        self.error_handler = ErrorHandler(bot)
        
    @nextcord.slash_command(
        name="kick",
        description="Kick a user from the server"
    )
    async def kick(
        self, 
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="The user to kick"),
        reason: str = nextcord.SlashOption(description="Reason for the kick", required=False)
    ):
        """Kick a user from the server with an optional reason"""
        # Check if the user has permission to kick
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Kick Members"),
                ephemeral=True
            )
            return
            
        # Check if the bot has permission to kick
        if not interaction.guild.me.guild_permissions.kick_members:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Kick Members"),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to kick themselves
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Invalid User",
                    "You cannot kick yourself."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to kick the bot
        if user.id == self.bot.user.id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Invalid User",
                    "I cannot kick myself."
                ),
                ephemeral=True
            )
            return
            
        # Make sure we're working with a Member object, not a User object
        if not isinstance(user, nextcord.Member):
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Invalid User",
                    "The specified user is not a member of this server."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to kick someone with a higher role
        if interaction.guild.me.top_role <= user.top_role:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Role Hierarchy Error",
                    "I cannot kick this user because their highest role is above or equal to my highest role."
                ),
                ephemeral=True
            )
            return
            
        # Check if the command user has a lower role than the target
        if interaction.user.top_role <= user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Role Hierarchy Error",
                    "You cannot kick this user because their highest role is above or equal to your highest role."
                ),
                ephemeral=True
            )
            return
            
        # Set default reason if none provided
        if not reason:
            reason = "No reason provided"
            
        # Defer response since kicking might take time
        await interaction.response.defer(ephemeral=False)
        
        # Create kick embed for the server logs
        kick_embed = EmbedHelper.moderation_embed(
            "User Kicked",
            f"{user.mention} has been kicked from the server.",
            emoji="👢",
            member=user,
            moderator=interaction.user,
            reason=reason
        )
        
        # Try to DM the user before kicking
        try:
            dm_embed = EmbedHelper.moderation_embed(
                "You've Been Kicked",
                f"You have been kicked from **{interaction.guild.name}**",
                emoji="👢",
                moderator=interaction.user,
                reason=reason
            )
            
            # Add server icon if available
            if interaction.guild.icon:
                dm_embed.set_thumbnail(url=interaction.guild.icon.url)
                
            # Add invitation link if the bot has permission to create invites
            if interaction.guild.me.guild_permissions.create_instant_invite:
                try:
                    # Try to get an invite from the system channel or first text channel
                    invite_channel = interaction.guild.system_channel or interaction.guild.text_channels[0]
                    invite = await invite_channel.create_invite(max_age=86400, max_uses=1, reason="Kick command - temporary invite")
                    dm_embed.add_field(name="Rejoin Server", value=f"[Click here to rejoin]({invite})", inline=False)
                except:
                    pass
                    
            await user.send(embed=dm_embed)
        except:
            # User might have DMs disabled
            kick_embed.add_field(name="Note", value="Could not DM user about the kick", inline=False)
            
        # Kick the user
        try:
            await interaction.guild.kick(
                user, 
                reason=f"Kicked by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
            )
            
            # Send confirmation to the channel
            await interaction.followup.send(embed=kick_embed)
            
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=kick_embed)
            except:
                pass
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "kick", True)
    #=============================================================================================================================================================
    @nextcord.slash_command(
        name="softban",
        description="Kick a user and delete their messages"
    )
    async def softban(
        self, 
        interaction: nextcord.Interaction,
        user: nextcord.Member = nextcord.SlashOption(description="The user to softban"),
        delete_messages: str = nextcord.SlashOption(
            description="Delete message history",
            choices={"Don't Delete Any": "0", "Last 24 Hours": "1", "Last 7 Days": "7"},
            required=False,
            default="1"
        ),
        reason: str = nextcord.SlashOption(description="Reason for the softban", required=False)
    ):
        """Softban a user (ban and immediately unban to delete messages)"""
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
            
        # Check if the user is trying to softban themselves
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Invalid User",
                    "You cannot softban yourself."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to softban the bot
        if user.id == self.bot.user.id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Invalid User",
                    "I cannot softban myself."
                ),
                ephemeral=True
            )
            return
            
        # Make sure we're working with a Member object, not a User object
        if not isinstance(user, nextcord.Member):
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Invalid User",
                    "The specified user is not a member of this server."
                ),
                ephemeral=True
            )
            return
            
        # Check if the user is trying to softban someone with a higher role
        if interaction.guild.me.top_role <= user.top_role:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Role Hierarchy Error",
                    "I cannot softban this user because their highest role is above or equal to my highest role."
                ),
                ephemeral=True
            )
            return
            
        # Check if the command user has a lower role than the target
        if interaction.user.top_role <= user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Role Hierarchy Error",
                    "You cannot softban this user because their highest role is above or equal to your highest role."
                ),
                ephemeral=True
            )
            return
            
        # Set default reason if none provided
        if not reason:
            reason = "No reason provided"
            
        # Defer response since softbanning might take time
        await interaction.response.defer(ephemeral=False)
        
        # Convert delete_messages to days
        delete_days = int(delete_messages)
        
        # Create softban embed for the server logs
        softban_embed = EmbedHelper.moderation_embed(
            "User Softbanned",
            f"{user.mention} has been softbanned from the server.",
            emoji="🧹",
            member=user,
            moderator=interaction.user,
            reason=reason
        )
        
        # Try to DM the user before softbanning
        try:
            dm_embed = EmbedHelper.moderation_embed(
                "You've Been Softbanned",
                f"You have been softbanned from **{interaction.guild.name}**\nA softban is a kick that also removes your recent messages.",
                emoji="🧹",
                moderator=interaction.user,
                reason=reason
            )
            
            # Add server icon if available
            if interaction.guild.icon:
                dm_embed.set_thumbnail(url=interaction.guild.icon.url)
                
            # Add invitation link if the bot has permission to create invites
            if interaction.guild.me.guild_permissions.create_instant_invite:
                try:
                    # Try to get an invite from the system channel or first text channel
                    invite_channel = interaction.guild.system_channel or interaction.guild.text_channels[0]
                    invite = await invite_channel.create_invite(max_age=86400, max_uses=1, reason="Softban command - temporary invite")
                    dm_embed.add_field(name="Rejoin Server", value=f"[Click here to rejoin]({invite})", inline=False)
                except:
                    pass
                    
            await user.send(embed=dm_embed)
        except:
            # User might have DMs disabled
            softban_embed.add_field(name="Note", value="Could not DM user about the softban", inline=False)
            
        # Softban the user (ban and immediately unban)
        try:
            # Ban the user
            await interaction.guild.ban(
                user, 
                reason=f"Softbanned by {interaction.user} ({interaction.user.id}) | Reason: {reason}",
                delete_message_days=delete_days
            )
            
            # Immediately unban the user
            await interaction.guild.unban(
                user,
                reason=f"Softban removal - Originally softbanned by {interaction.user} ({interaction.user.id})"
            )
            
            # Send confirmation to the channel
            await interaction.followup.send(embed=softban_embed)
            
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=softban_embed)
            except:
                pass
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "softban", True)
#=============================================================================================================================================================