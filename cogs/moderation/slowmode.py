import nextcord
from nextcord.ext import commands
import asyncio
import time
from datetime import datetime, timedelta
from utils.embed_helper import EmbedHelper
from utils.error_handler import ErrorHandler
from utils.time_helper import TimeHelper
#=============================================================================================================================================================
class SlowmodeCommands(commands.Cog):
    """Commands for managing channel slowmode"""
    
    def __init__(self, bot):
        self.bot = bot
        self.error_handler = ErrorHandler(bot)
        self.temporary_slowmodes = {}  # Store channels with temporary slowmode
    #=============================================================================================================================================================    
    @nextcord.slash_command(
        name="slowmode",
        description="Set, modify, or remove slowmode in a channel"
    )
    async def slowmode(
        self, 
        interaction: nextcord.Interaction,
        duration: str = nextcord.SlashOption(
            description="Slowmode duration (e.g. 5s, 10m, 2h, 0 to disable)",
            required=True
        ),
        channel: nextcord.TextChannel = nextcord.SlashOption(
            description="The channel to set slowmode in (defaults to current channel)",
            required=False
        ),
        reason: str = nextcord.SlashOption(
            description="Reason for changing slowmode",
            required=False
        ),
        temp_duration: str = nextcord.SlashOption(
            description="How long to keep slowmode active (e.g. 30m, 2h, 1d)",
            required=False
        )
    ):
        """Set, modify, or remove slowmode in a channel"""
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
            
        # Parse the slowmode duration
        seconds = 0
        if duration.lower() != "0" and duration.lower() != "off":
            seconds = TimeHelper.parse_time(duration)
            if seconds is None:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Invalid Duration",
                        "Please provide a valid duration format (e.g. 5s, 10m, 2h) or '0' to disable slowmode."
                    ),
                    ephemeral=True
                )
                return
                
            # Discord's slowmode limit is 21600 seconds (6 hours)
            if seconds > 21600:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Duration Too Long",
                        "Slowmode cannot be set for longer than 6 hours (21600 seconds)."
                    ),
                    ephemeral=True
                )
                return
                
        # Parse temporary duration if provided
        temp_expiry = None
        temp_duration_text = None
        if temp_duration:
            temp_seconds = TimeHelper.parse_time(temp_duration)
            if temp_seconds is None:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Invalid Temporary Duration",
                        "Please provide a valid duration format (e.g. 30m, 2h, 1d) for how long to keep slowmode active."
                    ),
                    ephemeral=True
                )
                return
                
            temp_expiry = time.time() + temp_seconds
            temp_duration_text = TimeHelper.format_time_remaining(temp_expiry)
            
        # Defer response since channel updates might take time
        await interaction.response.defer(ephemeral=False)
        
        try:
            # Get current slowmode
            current_slowmode = channel.slowmode_delay
            
            # Set the new slowmode
            await channel.edit(
                slowmode_delay=seconds,
                reason=f"Slowmode {'set' if seconds > 0 else 'disabled'} by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
            )
            
            # Create appropriate embed based on action
            if seconds > 0:
                # Format the slowmode duration for display
                if seconds < 60:
                    formatted_duration = f"{seconds} second{'s' if seconds != 1 else ''}"
                elif seconds < 3600:
                    minutes = seconds // 60
                    formatted_duration = f"{minutes} minute{'s' if minutes != 1 else ''}"
                else:
                    hours = seconds // 3600
                    formatted_duration = f"{hours} hour{'s' if hours != 1 else ''}"
                    
                # Create slowmode enabled embed
                action_text = "updated" if current_slowmode > 0 else "enabled"
                slowmode_embed = EmbedHelper.moderation_embed(
                    f"Slowmode {action_text.capitalize()}",
                    f"Slowmode in {channel.mention} has been {action_text} to **{formatted_duration}**.",
                    emoji="⏱️",
                    moderator=interaction.user,
                    reason=reason
                )
                
                if temp_duration_text:
                    slowmode_embed.add_field(name="Active For", value=temp_duration_text, inline=True)
                    slowmode_embed.add_field(name="Disables At", value=f"<t:{int(temp_expiry)}:F>", inline=True)
                    
                    # Store the temporary slowmode info
                    self.temporary_slowmodes[channel.id] = {
                        'guild_id': interaction.guild.id,
                        'channel_id': channel.id,
                        'expiry': temp_expiry,
                        'moderator_id': interaction.user.id,
                        'reason': reason
                    }
                    
                    # Schedule the slowmode removal
                    self.bot.loop.create_task(self.schedule_slowmode_removal(
                        channel.id,
                        interaction.guild.id,
                        temp_expiry,
                        interaction.user.id,
                        reason
                    ))
            else:
                # Create slowmode disabled embed
                slowmode_embed = EmbedHelper.moderation_embed(
                    "Slowmode Disabled",
                    f"Slowmode in {channel.mention} has been disabled.",
                    emoji="⏱️",
                    moderator=interaction.user,
                    reason=reason
                )
                
                # Remove from temporary slowmodes if it was temporary
                if channel.id in self.temporary_slowmodes:
                    del self.temporary_slowmodes[channel.id]
                    
            # Send confirmation to the channel
            await interaction.followup.send(embed=slowmode_embed)
            
            # Send notification to the affected channel if it's different from the command channel
            if channel.id != interaction.channel.id:
                notification_embed = slowmode_embed.copy()
                notification_embed.description = f"Slowmode in this channel has been {'set to **' + formatted_duration + '**' if seconds > 0 else 'disabled'}."
                
                await channel.send(embed=notification_embed)
                
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=slowmode_embed)
            except:
                pass
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "slowmode", True)
    #=============================================================================================================================================================        
    @nextcord.slash_command(
        name="slowmode-info",
        description="Show information about current slowmode settings"
    )
    async def slowmode_info(
        self, 
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            description="The channel to check slowmode in (defaults to current channel)",
            required=False
        )
    ):
        """Show information about current slowmode settings"""
        # Use current channel if none specified
        if channel is None:
            channel = interaction.channel
            
        # Get current slowmode
        current_slowmode = channel.slowmode_delay
        
        # Create info embed
        if current_slowmode > 0:
            # Format the slowmode duration for display
            if current_slowmode < 60:
                formatted_duration = f"{current_slowmode} second{'s' if current_slowmode != 1 else ''}"
            elif current_slowmode < 3600:
                minutes = current_slowmode // 60
                formatted_duration = f"{minutes} minute{'s' if minutes != 1 else ''}"
            else:
                hours = current_slowmode // 3600
                formatted_duration = f"{hours} hour{'s' if hours != 1 else ''}"
                
            info_embed = EmbedHelper.info_embed(
                "Slowmode Information",
                f"Slowmode is currently **enabled** in {channel.mention}."
            )
            
            info_embed.add_field(name="Current Delay", value=formatted_duration, inline=True)
            
            # Add temporary slowmode info if applicable
            if channel.id in self.temporary_slowmodes:
                temp_info = self.temporary_slowmodes[channel.id]
                time_remaining = TimeHelper.format_time_remaining(temp_info['expiry'])
                
                info_embed.add_field(name="Time Remaining", value=time_remaining, inline=True)
                info_embed.add_field(name="Disables At", value=f"<t:{int(temp_info['expiry'])}:F>", inline=True)
                
                # Get the moderator who set it
                moderator_id = temp_info['moderator_id']
                moderator = interaction.guild.get_member(moderator_id)
                if moderator:
                    info_embed.add_field(name="Set By", value=moderator.mention, inline=True)
                    
                # Add reason if available
                if 'reason' in temp_info and temp_info['reason']:
                    info_embed.add_field(name="Reason", value=temp_info['reason'], inline=False)
        else:
            info_embed = EmbedHelper.info_embed(
                "Slowmode Information",
                f"Slowmode is currently **disabled** in {channel.mention}."
            )
            
        # Send the info embed
        await interaction.response.send_message(embed=info_embed, ephemeral=False)
    #=============================================================================================================================================================    
    @nextcord.slash_command(
        name="channel-slowmode",
        description="Set slowmode for multiple channels at once"
    )
    async def channel_slowmode(
        self, 
        interaction: nextcord.Interaction,
        duration: str = nextcord.SlashOption(
            description="Slowmode duration (e.g. 5s, 10m, 2h, 0 to disable)",
            required=True
        ),
        category: nextcord.CategoryChannel = nextcord.SlashOption(
            description="Category to set slowmode in (all text channels in the category)",
            required=False
        ),
        reason: str = nextcord.SlashOption(
            description="Reason for changing slowmode",
            required=False
        ),
        temp_duration: str = nextcord.SlashOption(
            description="How long to keep slowmode active (e.g. 30m, 2h, 1d)",
            required=False
        )
    ):
        """Set slowmode for multiple channels at once"""
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
            
        # Parse the slowmode duration
        seconds = 0
        if duration.lower() != "0" and duration.lower() != "off":
            seconds = TimeHelper.parse_time(duration)
            if seconds is None:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Invalid Duration",
                        "Please provide a valid duration format (e.g. 5s, 10m, 2h) or '0' to disable slowmode."
                    ),
                    ephemeral=True
                )
                return
                
            # Discord's slowmode limit is 21600 seconds (6 hours)
            if seconds > 21600:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Duration Too Long",
                        "Slowmode cannot be set for longer than 6 hours (21600 seconds)."
                    ),
                    ephemeral=True
                )
                return
                
        # Parse temporary duration if provided
        temp_expiry = None
        temp_duration_text = None
        if temp_duration:
            temp_seconds = TimeHelper.parse_time(temp_duration)
            if temp_seconds is None:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Invalid Temporary Duration",
                        "Please provide a valid duration format (e.g. 30m, 2h, 1d) for how long to keep slowmode active."
                    ),
                    ephemeral=True
                )
                return
                
            temp_expiry = time.time() + temp_seconds
            temp_duration_text = TimeHelper.format_time_remaining(temp_expiry)
            
        # Defer response since this might take time
        await interaction.response.defer(ephemeral=False)
        
        # Determine which channels to modify
        channels_to_modify = []
        if category:
            # Set slowmode for all text channels in the category
            channels_to_modify = [c for c in category.channels if isinstance(c, nextcord.TextChannel)]
            target_description = f"category **{category.name}**"
        else:
            # Set slowmode for all text channels in the server
            channels_to_modify = [c for c in interaction.guild.channels if isinstance(c, nextcord.TextChannel)]
            target_description = "the entire server"
            
        if not channels_to_modify:
            await interaction.followup.send(
                embed=EmbedHelper.error_embed(
                    "No Channels Found",
                    "No text channels were found to modify."
                ),
                ephemeral=True
            )
            return
            
        # Format the slowmode duration for display
        if seconds > 0:
            if seconds < 60:
                formatted_duration = f"{seconds} second{'s' if seconds != 1 else ''}"
            elif seconds < 3600:
                minutes = seconds // 60
                formatted_duration = f"{minutes} minute{'s' if minutes != 1 else ''}"
            else:
                hours = seconds // 3600
                formatted_duration = f"{hours} hour{'s' if hours != 1 else ''}"
                
            action_text = "set"
        else:
            formatted_duration = "disabled"
            action_text = "disabled"
            
        # Create bulk slowmode embed
        bulk_embed = EmbedHelper.moderation_embed(
            f"Slowmode {action_text.capitalize()} in Bulk",
            f"Slowmode has been {action_text} to **{formatted_duration}** for {target_description}.",
            emoji="⏱️",
            moderator=interaction.user,
            reason=reason
        )
        
        if temp_duration_text and seconds > 0:
            bulk_embed.add_field(name="Active For", value=temp_duration_text, inline=True)
            bulk_embed.add_field(name="Disables At", value=f"<t:{int(temp_expiry)}:F>", inline=True)
            
        # Apply slowmode to all channels
        success_count = 0
        failed_count = 0
        
        for channel in channels_to_modify:
            try:
                await channel.edit(
                    slowmode_delay=seconds,
                    reason=f"Bulk slowmode {'set' if seconds > 0 else 'disabled'} by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
                )
                
                # Store the temporary slowmode info if applicable
                if temp_expiry and seconds > 0:
                    self.temporary_slowmodes[channel.id] = {
                        'guild_id': interaction.guild.id,
                        'channel_id': channel.id,
                        'expiry': temp_expiry,
                        'moderator_id': interaction.user.id,
                        'reason': reason
                    }
                    
                    # Schedule the slowmode removal
                    self.bot.loop.create_task(self.schedule_slowmode_removal(
                        channel.id,
                        interaction.guild.id,
                        temp_expiry,
                        interaction.user.id,
                        reason
                    ))
                elif seconds == 0 and channel.id in self.temporary_slowmodes:
                    # Remove from temporary slowmodes if it was temporary
                    del self.temporary_slowmodes[channel.id]
                    
                success_count += 1
            except:
                failed_count += 1
                
        # Add the results to the embed
        bulk_embed.add_field(
            name="Results", 
            value=f"✅ **{success_count}** channels modified\n❌ **{failed_count}** channels failed",
            inline=False
        )
        
        # Send confirmation
        await interaction.followup.send(embed=bulk_embed)
        
        # Try to send to mod-logs channel if it exists
        try:
            log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
            if log_channel:
                await log_channel.send(embed=bulk_embed)
        except:
            pass
    #=============================================================================================================================================================
    @nextcord.slash_command(
        name="slowmode-remove",
        description="Quickly remove slowmode from a channel"
    )
    async def remove_slowmode(
        self, 
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            description="The channel to remove slowmode from (defaults to current channel)",
            required=False
        ),
        reason: str = nextcord.SlashOption(
            description="Reason for removing slowmode",
            required=False
        )
    ):
        """Quickly remove slowmode from a channel"""
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
            
        # Check if slowmode is even active
        if channel.slowmode_delay == 0:
            await interaction.response.send_message(
                embed=EmbedHelper.info_embed(
                    "No Slowmode Active",
                    f"Slowmode is already disabled in {channel.mention}."
                ),
                ephemeral=True
            )
            return
            
        # Defer response since channel updates might take time
        await interaction.response.defer(ephemeral=False)
        
        try:
            # Remove slowmode
            await channel.edit(
                slowmode_delay=0,
                reason=f"Slowmode disabled by {interaction.user} ({interaction.user.id}) | Reason: {reason}"
            )
            
            # Create slowmode disabled embed
            slowmode_embed = EmbedHelper.moderation_embed(
                "Slowmode Removed",
                f"Slowmode in {channel.mention} has been removed.",
                emoji="⏱️",
                moderator=interaction.user,
                reason=reason
            )
            
            # Remove from temporary slowmodes if it was temporary
            was_temporary = False
            if channel.id in self.temporary_slowmodes:
                was_temporary = True
                del self.temporary_slowmodes[channel.id]
                slowmode_embed.add_field(
                    name="Note", 
                    value="This channel had a temporary slowmode that has now been canceled.", 
                    inline=False
                )
                
            # Send confirmation to the channel
            await interaction.followup.send(embed=slowmode_embed)
            
            # Send notification to the affected channel if it's different from the command channel
            if channel.id != interaction.channel.id:
                notification_embed = slowmode_embed.copy()
                notification_embed.description = "Slowmode in this channel has been removed."
                
                await channel.send(embed=notification_embed)
                
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=slowmode_embed)
            except:
                pass
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "remove-slowmode", True)
    #=============================================================================================================================================================        
    async def schedule_slowmode_removal(self, channel_id, guild_id, expiry_time, moderator_id, original_reason):
        """Schedule a channel to have slowmode removed after a duration"""
        # Calculate seconds to wait
        seconds_to_wait = expiry_time - time.time()
        if seconds_to_wait <= 0:
            return
            
        # Wait until the expiry time
        await asyncio.sleep(seconds_to_wait)
        
        # Check if the channel is still in the temporary slowmodes dict
        if channel_id not in self.temporary_slowmodes:
            return  # Slowmode was manually disabled
            
        # Get the guild and channel
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
            
        # Get the channel
        channel = guild.get_channel(channel_id)
        if not channel:
            return
            
        # Check if the channel still has slowmode
        if channel.slowmode_delay == 0:
            return  # Slowmode is already disabled
            
        # Get the moderator
        moderator = guild.get_member(moderator_id) or await self.bot.fetch_user(moderator_id)
        
        try:
            # Disable the slowmode
            await channel.edit(
                slowmode_delay=0,
                reason=f"Automatic slowmode removal after duration | Originally set by {moderator} for: {original_reason}"
            )
            
            # Remove from temporary slowmodes
            if channel_id in self.temporary_slowmodes:
                del self.temporary_slowmodes[channel_id]
                
            # Create slowmode disabled embed
            disabled_embed = EmbedHelper.moderation_embed(
                "Slowmode Automatically Disabled",
                f"Slowmode in {channel.mention} has been automatically disabled after the set duration.",
                emoji="⏱️",
                reason=f"Duration expired (Originally set for: {original_reason})"
            )
            
            # Send notification to the channel
            await channel.send(embed=disabled_embed)
            
            # Try to send to mod-logs channel if it exists
            log_channel = nextcord.utils.get(guild.channels, name="mod-logs")
            if log_channel:
                log_embed = EmbedHelper.moderation_embed(
                    "Slowmode Automatically Disabled",
                    f"Slowmode in {channel.mention} has been automatically disabled after the set duration.",
                    emoji="⏱️",
                    reason=f"Duration expired (Originally set for: {original_reason})"
                )
                
                await log_channel.send(embed=log_embed)
                
        except:
            # If there's an error, just silently fail
            pass
#=============================================================================================================================================================