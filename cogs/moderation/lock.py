import nextcord
from nextcord.ext import commands
import time
import asyncio
from utils.embed_helper import EmbedHelper
from utils.time_helper import TimeHelper
from utils.error_handler import ErrorHandler
#=============================================================================================================================================================
class LockCommands(commands.Cog):
    """Commands for locking and unlocking channels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.error_handler = ErrorHandler(bot)
        self.locked_channels = {}  # Store temporarily locked channels
    #============================================================================================================================================================= 
    @nextcord.slash_command(
        name="lock",
        description="Lock a channel to prevent members from sending messages"
    )
    async def lock(
        self, 
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            description="The channel to lock (defaults to current channel)",
            required=False
        ),
        reason: str = nextcord.SlashOption(
            description="Reason for locking the channel",
            required=False
        ),
        duration: str = nextcord.SlashOption(
            description="Lock duration (e.g. 1h, 2d, 7d). Leave empty for indefinite",
            required=False
        )
    ):
        """Lock a channel to prevent members from sending messages"""
        # Check if the user has permission to manage channels
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Channels"),
                ephemeral=True
            )
            return
            
        # Check if the bot has permission to manage channels
        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Manage Channels"),
                ephemeral=True
            )
            return
            
        # Use current channel if none specified
        if channel is None:
            channel = interaction.channel
            
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
            
        # Defer response since channel permission updates might take time
        await interaction.response.defer(ephemeral=False)
        
        # Get the default role (@everyone)
        default_role = interaction.guild.default_role
        
        # Check if the channel is already locked
        current_perms = channel.overwrites_for(default_role)
        if current_perms.send_messages is False:
            await interaction.followup.send(
                embed=EmbedHelper.error_embed(
                    "Channel Already Locked",
                    f"{channel.mention} is already locked."
                ),
                ephemeral=True
            )
            return
            
        # Store the original permissions to restore later
        original_perms = channel.overwrites_for(default_role)
        
        # Create new permission overwrite
        new_perms = nextcord.PermissionOverwrite(**{k: v for k, v in original_perms._values.items()})
        new_perms.send_messages = False
        
        # Create lock embed
        lock_embed = EmbedHelper.moderation_embed(
            "Channel Locked",
            f"{channel.mention} has been locked. Members cannot send messages.",
            emoji="🔒",
            moderator=interaction.user,
            reason=reason
        )
        
        if expiry_time:
            lock_embed.add_field(name="Duration", value=duration_text, inline=True)
            lock_embed.add_field(name="Unlocks At", value=f"<t:{int(expiry_time)}:F>", inline=True)
        else:
            lock_embed.add_field(name="Duration", value="Indefinite", inline=True)
            
        # Apply the new permissions
        try:
            await channel.set_permissions(
                default_role,
                overwrite=new_perms,
                reason=f"Channel locked by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
            )
            
            # Store the lock information for temporary locks
            if expiry_time:
                self.locked_channels[channel.id] = {
                    'guild_id': interaction.guild.id,
                    'channel_id': channel.id,
                    'expiry': expiry_time,
                    'original_perms': original_perms,
                    'moderator_id': interaction.user.id,
                    'reason': reason
                }
                
                # Schedule the unlock task
                self.bot.loop.create_task(self.schedule_unlock(
                    channel.id,
                    interaction.guild.id,
                    expiry_time,
                    interaction.user.id,
                    reason
                ))
                
            # Send confirmation to the channel
            await interaction.followup.send(embed=lock_embed)
            
            # Send notification to the locked channel if it's different from the command channel
            if channel.id != interaction.channel.id:
                notification_embed = EmbedHelper.moderation_embed(
                    "Channel Locked",
                    f"This channel has been locked by {interaction.user.mention}.",
                    emoji="🔒",
                    moderator=interaction.user,
                    reason=reason
                )
                
                if expiry_time:
                    notification_embed.add_field(name="Duration", value=duration_text, inline=True)
                    notification_embed.add_field(name="Unlocks At", value=f"<t:{int(expiry_time)}:F>", inline=True)
                else:
                    notification_embed.add_field(name="Duration", value="Indefinite", inline=True)
                    
                await channel.send(embed=notification_embed)
                
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=lock_embed)
            except:
                pass
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "lock", True)
    #=============================================================================================================================================================  
    @nextcord.slash_command(
        name="unlock",
        description="Unlock a previously locked channel"
    )
    async def unlock(
        self, 
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            description="The channel to unlock (defaults to current channel)",
            required=False
        ),
        reason: str = nextcord.SlashOption(
            description="Reason for unlocking the channel",
            required=False
        )
    ):
        """Unlock a previously locked channel"""
        # Check if the user has permission to manage channels
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Channels"),
                ephemeral=True
            )
            return
            
        # Check if the bot has permission to manage channels
        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Manage Channels"),
                ephemeral=True
            )
            return
            
        # Use current channel if none specified
        if channel is None:
            channel = interaction.channel
            
        # Set default reason if none provided
        if not reason:
            reason = "No reason provided"
            
        # Defer response since channel permission updates might take time
        await interaction.response.defer(ephemeral=False)
        
        # Get the default role (@everyone)
        default_role = interaction.guild.default_role
        
        # Check if the channel is actually locked
        current_perms = channel.overwrites_for(default_role)
        if current_perms.send_messages is not False:
            await interaction.followup.send(
                embed=EmbedHelper.error_embed(
                    "Channel Not Locked",
                    f"{channel.mention} is not locked."
                ),
                ephemeral=True
            )
            return
            
        # Create new permission overwrite
        new_perms = nextcord.PermissionOverwrite(**{k: v for k, v in current_perms._values.items()})
        new_perms.send_messages = None  # Reset to default
        
        # If there are no other permission overwrites, remove the overwrite entirely
        should_remove = True
        for perm, value in new_perms._values.items():
            if value is not None and perm != 'send_messages':
                should_remove = False
                break
                
        # Create unlock embed
        unlock_embed = EmbedHelper.moderation_embed(
            "Channel Unlocked",
            f"{channel.mention} has been unlocked. Members can now send messages.",
            emoji="🔓",
            moderator=interaction.user,
            reason=reason
        )
        
        # Apply the new permissions
        try:
            if should_remove:
                await channel.set_permissions(
                    default_role,
                    overwrite=None,
                    reason=f"Channel unlocked by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
                )
            else:
                await channel.set_permissions(
                    default_role,
                    overwrite=new_perms,
                    reason=f"Channel unlocked by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
                )
                
            # Remove from locked channels if it was temporarily locked
            if channel.id in self.locked_channels:
                del self.locked_channels[channel.id]
                
            # Send confirmation to the channel
            await interaction.followup.send(embed=unlock_embed)
            
            # Send notification to the unlocked channel if it's different from the command channel
            if channel.id != interaction.channel.id:
                notification_embed = EmbedHelper.moderation_embed(
                    "Channel Unlocked",
                    f"This channel has been unlocked by {interaction.user.mention}.",
                    emoji="🔓",
                    moderator=interaction.user,
                    reason=reason
                )
                
                await channel.send(embed=notification_embed)
                
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=unlock_embed)
            except:
                pass
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "unlock", True)
    #=============================================================================================================================================================       
    @nextcord.slash_command(
        name="lockdown",
        description="Lock multiple channels at once"
    )
    async def lockdown(
        self, 
        interaction: nextcord.Interaction,
        category: nextcord.CategoryChannel = nextcord.SlashOption(
            description="Category to lock (all text channels in the category)",
            required=False
        ),
        reason: str = nextcord.SlashOption(
            description="Reason for the lockdown",
            required=False
        ),
        duration: str = nextcord.SlashOption(
            description="Lockdown duration (e.g. 1h, 2d, 7d). Leave empty for indefinite",
            required=False
        )
    ):
        """Lock multiple channels at once (entire category or server)"""
        # Check if the user has permission to manage channels
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Channels"),
                ephemeral=True
            )
            return
            
        # Check if the bot has permission to manage channels
        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Manage Channels"),
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
            
        # Defer response since this might take time
        await interaction.response.defer(ephemeral=False)
        
        # Get the default role (@everyone)
        default_role = interaction.guild.default_role
        
        # Determine which channels to lock
        channels_to_lock = []
        if category:
            # Lock all text channels in the category
            channels_to_lock = [c for c in category.channels if isinstance(c, nextcord.TextChannel)]
            lockdown_target = f"category **{category.name}**"
        else:
            # Lock all text channels in the server
            channels_to_lock = [c for c in interaction.guild.channels if isinstance(c, nextcord.TextChannel)]
            lockdown_target = "the entire server"
            
        if not channels_to_lock:
            await interaction.followup.send(
                embed=EmbedHelper.error_embed(
                    "No Channels Found",
                    "No text channels were found to lock."
                ),
                ephemeral=True
            )
            return
            
        # Create lockdown embed
        lockdown_embed = EmbedHelper.moderation_embed(
            "Lockdown Initiated",
            f"A lockdown has been initiated for {lockdown_target}.",
            emoji="🔒",
            moderator=interaction.user,
            reason=reason
        )
        
        if expiry_time:
            lockdown_embed.add_field(name="Duration", value=duration_text, inline=True)
            lockdown_embed.add_field(name="Unlocks At", value=f"<t:{int(expiry_time)}:F>", inline=True)
        else:
            lockdown_embed.add_field(name="Duration", value="Indefinite", inline=True)
            
        # Lock all the channels
        locked_count = 0
        already_locked = 0
        failed_count = 0
        
        for channel in channels_to_lock:
            try:
                # Check if already locked
                current_perms = channel.overwrites_for(default_role)
                if current_perms.send_messages is False:
                    already_locked += 1
                    continue
                    
                # Store the original permissions
                original_perms = channel.overwrites_for(default_role)
                
                # Create new permission overwrite
                new_perms = nextcord.PermissionOverwrite(**{k: v for k, v in original_perms._values.items()})
                new_perms.send_messages = False
                
                # Apply the new permissions
                await channel.set_permissions(
                    default_role,
                    overwrite=new_perms,
                    reason=f"Lockdown by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
                )
                
                # Store the lock information for temporary locks
                if expiry_time:
                    self.locked_channels[channel.id] = {
                        'guild_id': interaction.guild.id,
                        'channel_id': channel.id,
                        'expiry': expiry_time,
                        'original_perms': original_perms,
                        'moderator_id': interaction.user.id,
                        'reason': reason
                    }
                    
                    # Schedule the unlock task
                    self.bot.loop.create_task(self.schedule_unlock(
                        channel.id,
                        interaction.guild.id,
                        expiry_time,
                        interaction.user.id,
                        reason
                    ))
                    
                locked_count += 1
                
                # Send notification to the channel
                notification_embed = EmbedHelper.moderation_embed(
                    "Channel Locked",
                    f"This channel has been locked as part of a lockdown by {interaction.user.mention}.",
                    emoji="🔒",
                    moderator=interaction.user,
                    reason=reason
                )
                
                if expiry_time:
                    notification_embed.add_field(name="Duration", value=duration_text, inline=True)
                    notification_embed.add_field(name="Unlocks At", value=f"<t:{int(expiry_time)}:F>", inline=True)
                else:
                    notification_embed.add_field(name="Duration", value="Indefinite", inline=True)
                    
                await channel.send(embed=notification_embed)
                
            except:
                failed_count += 1
                
        # Add the results to the embed
        lockdown_embed.add_field(
            name="Results", 
            value=f"✅ **{locked_count}** channels locked\n⏭️ **{already_locked}** channels already locked\n❌ **{failed_count}** channels failed",
            inline=False
        )
        
        # Send confirmation
        await interaction.followup.send(embed=lockdown_embed)
        
        # Try to send to mod-logs channel if it exists
        try:
            log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
            if log_channel:
                await log_channel.send(embed=lockdown_embed)
        except:
            pass
    #=============================================================================================================================================================        
    @nextcord.slash_command(
        name="unlockdown",
        description="Unlock multiple locked channels at once"
    )
    async def unlockdown(
        self, 
        interaction: nextcord.Interaction,
        category: nextcord.CategoryChannel = nextcord.SlashOption(
            description="Category to unlock (all text channels in the category)",
            required=False
        ),
        reason: str = nextcord.SlashOption(
            description="Reason for ending the lockdown",
            required=False
        )
    ):
        """Unlock multiple locked channels at once (entire category or server)"""
        # Check if the user has permission to manage channels
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Channels"),
                ephemeral=True
            )
            return
            
        # Check if the bot has permission to manage channels
        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Manage Channels"),
                ephemeral=True
            )
            return
            
        # Set default reason if none provided
        if not reason:
            reason = "No reason provided"
            
        # Defer response since this might take time
        await interaction.response.defer(ephemeral=False)
        
        # Get the default role (@everyone)
        default_role = interaction.guild.default_role
        
        # Determine which channels to unlock
        channels_to_unlock = []
        if category:
            # Unlock all text channels in the category
            channels_to_unlock = [c for c in category.channels if isinstance(c, nextcord.TextChannel)]
            unlockdown_target = f"category **{category.name}**"
        else:
            # Unlock all text channels in the server
            channels_to_unlock = [c for c in interaction.guild.channels if isinstance(c, nextcord.TextChannel)]
            unlockdown_target = "the entire server"
            
        if not channels_to_unlock:
            await interaction.followup.send(
                embed=EmbedHelper.error_embed(
                    "No Channels Found",
                    "No text channels were found to unlock."
                ),
                ephemeral=True
            )
            return
            
        # Create unlockdown embed
        unlockdown_embed = EmbedHelper.moderation_embed(
            "Lockdown Ended",
            f"The lockdown has been ended for {unlockdown_target}.",
            emoji="🔓",
            moderator=interaction.user,
            reason=reason
        )
        
        # Unlock all the channels
        unlocked_count = 0
        already_unlocked = 0
        failed_count = 0
        
        for channel in channels_to_unlock:
            try:
                # Check if actually locked
                current_perms = channel.overwrites_for(default_role)
                if current_perms.send_messages is not False:
                    already_unlocked += 1
                    continue
                    
                # Create new permission overwrite
                new_perms = nextcord.PermissionOverwrite(**{k: v for k, v in current_perms._values.items()})
                new_perms.send_messages = None  # Reset to default
                
                # If there are no other permission overwrites, remove the overwrite entirely
                should_remove = True
                for perm, value in new_perms._values.items():
                    if value is not None and perm != 'send_messages':
                        should_remove = False
                        break
                        
                # Apply the new permissions
                if should_remove:
                    await channel.set_permissions(
                        default_role,
                        overwrite=None,
                        reason=f"Lockdown ended by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
                    )
                else:
                    await channel.set_permissions(
                        default_role,
                        overwrite=new_perms,
                        reason=f"Lockdown ended by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
                    )
                    
                # Remove from locked channels if it was temporarily locked
                if channel.id in self.locked_channels:
                    del self.locked_channels[channel.id]
                    
                unlocked_count += 1
                
                # Send notification to the channel
                notification_embed = EmbedHelper.moderation_embed(
                    "Channel Unlocked",
                    f"This channel has been unlocked by {interaction.user.mention}. The lockdown has ended.",
                    emoji="🔓",
                    moderator=interaction.user,
                    reason=reason
                )
                
                await channel.send(embed=notification_embed)
                
            except:
                failed_count += 1
                
        # Add the results to the embed
        unlockdown_embed.add_field(
            name="Results", 
            value=f"✅ **{unlocked_count}** channels unlocked\n⏭️ **{already_unlocked}** channels already unlocked\n❌ **{failed_count}** channels failed",
            inline=False
        )
        
        # Send confirmation
        await interaction.followup.send(embed=unlockdown_embed)
        
        # Try to send to mod-logs channel if it exists
        try:
            log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
            if log_channel:
                await log_channel.send(embed=unlockdown_embed)
        except:
            pass
    #=============================================================================================================================================================        
    async def schedule_unlock(self, channel_id, guild_id, expiry_time, moderator_id, original_reason):
        """Schedule a channel to be unlocked after a duration"""
        # Calculate seconds to wait
        seconds_to_wait = expiry_time - time.time()
        if seconds_to_wait <= 0:
            return
            
        # Wait until the expiry time
        await asyncio.sleep(seconds_to_wait)
        
        # Check if the channel is still in the locked channels dict
        if channel_id not in self.locked_channels:
            return  # Channel was manually unlocked
            
        # Get the guild and channel
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
            
        # Get the channel
        channel = guild.get_channel(channel_id)
        if not channel:
            return
            
        # Get the default role (@everyone)
        default_role = guild.default_role
        
        # Check if the channel is still locked
        current_perms = channel.overwrites_for(default_role)
        if current_perms.send_messages is not False:
            return  # Channel is not locked anymore
            
        # Get the moderator
        moderator = guild.get_member(moderator_id) or await self.bot.fetch_user(moderator_id)
        
        # Create new permission overwrite
        new_perms = nextcord.PermissionOverwrite(**{k: v for k, v in current_perms._values.items()})
        new_perms.send_messages = None  # Reset to default
        
        # If there are no other permission overwrites, remove the overwrite entirely
        should_remove = True
        for perm, value in new_perms._values.items():
            if value is not None and perm != 'send_messages':
                should_remove = False
                break
                
        try:
            # Apply the new permissions
            if should_remove:
                await channel.set_permissions(
                    default_role,
                    overwrite=None,
                    reason=f"Automatic unlock after duration | Originally locked by {moderator} for: {original_reason}"
                )
            else:
                await channel.set_permissions(
                    default_role,
                    overwrite=new_perms,
                    reason=f"Automatic unlock after duration | Originally locked by {moderator} for: {original_reason}"
                )
                
            # Remove from locked channels
            if channel_id in self.locked_channels:
                del self.locked_channels[channel_id]
                
            # Create unlock embed
            unlock_embed = EmbedHelper.moderation_embed(
                "Channel Automatically Unlocked",
                f"This channel has been automatically unlocked after the set duration.",
                emoji="🔓",
                reason=f"Duration expired (Originally locked for: {original_reason})"
            )
            
            # Send notification to the channel
            await channel.send(embed=unlock_embed)
            
            # Try to send to mod-logs channel if it exists
            log_channel = nextcord.utils.get(guild.channels, name="mod-logs")
            if log_channel:
                log_embed = EmbedHelper.moderation_embed(
                    "Channel Automatically Unlocked",
                    f"{channel.mention} has been automatically unlocked after the set duration.",
                    emoji="🔓",
                    reason=f"Duration expired (Originally locked for: {original_reason})"
                )
                
                await log_channel.send(embed=log_embed)
                
        except:
            # If there's an error, just silently fail
            pass
#=============================================================================================================================================================