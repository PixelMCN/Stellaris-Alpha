import nextcord
from nextcord.ext import commands
import asyncio
from utils.embed_helper import EmbedHelper
from utils.error_handler import ErrorHandler
from utils.embed_helper import EmbedColors
import datetime
#=============================================================================================================================================================
class LogsCommands(commands.Cog):
    """Commands for setting up logging channels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.error_handler = ErrorHandler(bot)
        
    @nextcord.slash_command(
        name="logs",
        description="Set up logging channels for moderation actions"
    )
    async def logs(
        self, 
        interaction: nextcord.Interaction,
        category_name: str = nextcord.SlashOption(
            description="Name for the logs category (defaults to 'Logs')",
            required=False,
            default="Logs"
        )
    ):
        """Set up logging channels for moderation actions"""
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
            
        # Defer response since channel creation might take time
        await interaction.response.defer(ephemeral=False)
        
        # Check if log channels already exist
        existing_channels = []
        mod_logs = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
        if mod_logs:
            existing_channels.append("mod-logs")
            
        error_logs = nextcord.utils.get(interaction.guild.channels, name="error-logs")
        if error_logs:
            existing_channels.append("error-logs")
            
        message_logs = nextcord.utils.get(interaction.guild.channels, name="message-logs")
        if message_logs:
            existing_channels.append("message-logs")
            
        if existing_channels:
            # Create confirmation view
            view = LogsConfirmationView(self.bot, interaction, category_name, existing_channels)
            
            # Create embed for confirmation
            confirm_embed = EmbedHelper.warning_embed(
                "Logs Channels Already Exist",
                f"The following log channels already exist: **{', '.join(existing_channels)}**\n\n"
                f"Would you like to recreate them? This will delete the existing channels and create new ones."
            )
            
            await interaction.followup.send(embed=confirm_embed, view=view)
            return
            
        # If no existing channels, create them directly
        await self.create_log_channels(interaction, category_name)
        
    async def create_log_channels(self, interaction, category_name):
        """Create the logging channels"""
        try:
            # Find or create the logs category
            category = nextcord.utils.get(interaction.guild.categories, name=category_name)
            if not category:
                category = await interaction.guild.create_category(
                    name=category_name,
                    reason=f"Logs category created by {interaction.user}"
                )
                
            # Create permission overwrites for the category
            # Only staff should be able to see these channels
            overwrites = {
                interaction.guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: nextcord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Add overwrites for roles with moderation permissions
            for role in interaction.guild.roles:
                if role.permissions.ban_members or role.permissions.kick_members or role.permissions.manage_messages:
                    overwrites[role] = nextcord.PermissionOverwrite(read_messages=True)
                    
            # Update category permissions
            await category.edit(overwrites=overwrites)
            
            # Create mod-logs channel
            mod_logs = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
            if mod_logs:
                await mod_logs.delete(reason=f"Recreating mod-logs channel by {interaction.user}")
                
            mod_logs = await interaction.guild.create_text_channel(
                name="mod-logs",
                category=category,
                topic="Logs for moderation actions",
                reason=f"Mod logs channel created by {interaction.user}",
                overwrites=overwrites
            )
            
            # Create error-logs channel
            error_logs = nextcord.utils.get(interaction.guild.channels, name="error-logs")
            if error_logs:
                await error_logs.delete(reason=f"Recreating error-logs channel by {interaction.user}")
                
            error_logs = await interaction.guild.create_text_channel(
                name="error-logs",
                category=category,
                topic="Logs for bot errors",
                reason=f"Error logs channel created by {interaction.user}",
                overwrites=overwrites
            )
            
            # Create message-logs channel
            message_logs = nextcord.utils.get(interaction.guild.channels, name="message-logs")
            if message_logs:
                await message_logs.delete(reason=f"Recreating message-logs channel by {interaction.user}")
                
            message_logs = await interaction.guild.create_text_channel(
                name="message-logs",
                category=category,
                topic="Logs for message edits and deletions",
                reason=f"Message logs channel created by {interaction.user}",
                overwrites=overwrites
            )
            
            # Create success embed
            success_embed = EmbedHelper.success_embed(
                "Logging Channels Created",
                f"Successfully created the following logging channels:\n"
                f"• {mod_logs.mention} - For moderation actions\n"
                f"• {error_logs.mention} - For bot errors\n"
                f"• {message_logs.mention} - For message edits and deletions\n\n"
                f"These channels are only visible to staff members with moderation permissions."
            )
            
            await interaction.followup.send(embed=success_embed)
            
            # Send a welcome message to each channel
            mod_welcome = nextcord.Embed(
                title="📝 Moderation Logs Channel",
                description="This channel will log all moderation actions performed by staff members.",
                color=EmbedColors.MODERATION
            )
            mod_welcome.add_field(
                name="Logged Actions",
                value="• Bans and Unbans\n• Mutes and Unmutes\n• Channel Locks\n• Slowmode Changes\n• Voice Deafens",
                inline=False
            )
            await mod_logs.send(embed=mod_welcome)
            
            error_welcome = nextcord.Embed(
                title="⚠️ Error Logs Channel",
                description="This channel will log all errors encountered by the bot.",
                color=EmbedColors.ERROR
            )
            error_welcome.add_field(
                name="Information",
                value="Error logs include details about the command, user, and error traceback to help with debugging.",
                inline=False
            )
            await error_logs.send(embed=error_welcome)
            
            message_welcome = nextcord.Embed(
                title="💬 Message Logs Channel",
                description="This channel will log all message edits and deletions.",
                color=EmbedColors.INFO
            )
            message_welcome.add_field(
                name="Logged Actions",
                value="• Message edits\n• Message deletions\n• Bulk message deletions",
                inline=False
            )
            await message_logs.send(embed=message_welcome)
            
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "logs", True)
#=============================================================================================================================================================
class LogsConfirmationView(nextcord.ui.View):
    """View for confirming recreation of log channels"""
    
    def __init__(self, bot, interaction, category_name, existing_channels):
        super().__init__(timeout=60)
        self.bot = bot
        self.interaction = interaction
        self.category_name = category_name
        self.existing_channels = existing_channels
        self.error_handler = ErrorHandler(bot)
    #=============================================================================================================================================================
    @nextcord.ui.button(label="Yes, recreate channels", style=nextcord.ButtonStyle.danger)
    async def confirm_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Confirm button to recreate the channels"""
        # Disable all buttons
        for child in self.children:
            child.disabled = True
            
        await interaction.response.edit_message(view=self)
        
        # Get the logs command instance
        logs_cog = self.bot.get_cog("LogsCommands")
        if logs_cog:
            await logs_cog.create_log_channels(self.interaction, self.category_name)
        else:
            await interaction.followup.send(
                embed=EmbedHelper.error_embed(
                    "Error",
                    "Could not find the logs command. Please try again later."
                )
            )
    #=============================================================================================================================================================
    @nextcord.ui.button(label="No, keep existing channels", style=nextcord.ButtonStyle.secondary)
    async def cancel_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Cancel button to keep existing channels"""
        # Disable all buttons
        for child in self.children:
            child.disabled = True
            
        await interaction.response.edit_message(view=self)
        
        # Send cancellation message
        await interaction.followup.send(
            embed=EmbedHelper.info_embed(
                "Operation Cancelled",
                f"Keeping existing log channels: **{', '.join(self.existing_channels)}**"
            )
        )
        
    async def on_timeout(self):
        """Handle timeout"""
        # Disable all buttons
        for child in self.children:
            child.disabled = True
            
        try:
            await self.interaction.edit_original_message(view=self)
        except:
            pass


#=============================================================================================================================================================

class MessageLogEvents(commands.Cog):
    """Events for logging message edits and deletions"""
    
    def __init__(self, bot):
        self.bot = bot
        self.message_cache = {}  # Cache for storing message content for edit logs
        self.max_cache_size = 1000  # Maximum number of messages to cache
        
    def get_message_logs_channel(self, guild):
        """Get the message logs channel for a guild"""
        channel = nextcord.utils.get(guild.text_channels, name="message-logs")
        # Check permissions to ensure the bot can send messages to this channel
        if channel and channel.permissions_for(guild.me).send_messages:
            return channel
        return None
        
    @commands.Cog.listener()
    async def on_message(self, message):
        """Cache messages for edit logging"""
        # Skip bot messages and DMs
        if message.author.bot or not message.guild:
            return
            
        # Cache the message content for future edit comparisons
        # Use a simple LRU-like cache by checking the size
        if len(self.message_cache) >= self.max_cache_size:
            # Remove the oldest item if we've reached max size
            oldest_key = next(iter(self.message_cache))
            self.message_cache.pop(oldest_key)
            
        # Store message content with message ID as key
        self.message_cache[message.id] = {
            "content": message.content,
            "attachments": [attachment.url for attachment in message.attachments],
            "timestamp": datetime.datetime.now()
        }
        
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        """Log message edits using raw event to catch all edits"""
        # Ignore DM channels
        if not payload.guild_id:
            return
            
        # Get guild and channel
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
            
        # Get the message logs channel
        logs_channel = self.get_message_logs_channel(guild)
        if not logs_channel:
            return
            
        # Get the channel where the message was edited
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return
            
        # Try to fetch the message that was edited
        try:
            # Get the after state of the message
            after = await channel.fetch_message(payload.message_id)
            
            # Skip bot messages
            if after.author.bot:
                return
                
            # Get before content from cache
            cached_info = self.message_cache.get(payload.message_id, {})
            before_content = cached_info.get("content", "Unknown (not in cache)")
            
            # Skip if content didn't change (could be embed or other update)
            if before_content == after.content:
                return
                
            # Create embed for edit log
            embed = nextcord.Embed(
                title="Message Edited",
                description=f"Message edited in {channel.mention}",
                color=EmbedColors.INFO,
                timestamp=datetime.datetime.now()
            )
            
            embed.set_author(
                name=f"{after.author} ({after.author.id})",
                icon_url=after.author.display_avatar.url
            )
            
            # Add fields for before and after content
            if before_content:
                embed.add_field(
                    name="Before",
                    value=before_content[:1024],
                    inline=False
                )
            
            embed.add_field(
                name="After",
                value=after.content[:1024] if after.content else "(No content)",
                inline=False
            )
            
            embed.add_field(
                name="Message Link",
                value=f"[Jump to Message]({after.jump_url})",
                inline=False
            )
            
            # Send the log
            await logs_channel.send(embed=embed)
            
            # Update cache with new content
            if payload.message_id in self.message_cache:
                self.message_cache[payload.message_id]["content"] = after.content
                
        except (nextcord.NotFound, nextcord.Forbidden, nextcord.HTTPException) as e:
            # Can't fetch the message (deleted, no permissions, etc.)
            # We can still log with limited information from payload data
            data = payload.data
            
            # If we can get data from the payload
            if "content" in data:
                embed = nextcord.Embed(
                    title="Message Edited (Limited Info)",
                    description=f"Message edited in <#{payload.channel_id}>",
                    color=EmbedColors.INFO,
                    timestamp=datetime.datetime.now()
                )
                
                embed.add_field(
                    name="After",
                    value=data["content"][:1024] if data["content"] else "(No content)",
                    inline=False
                )
                
                embed.add_field(
                    name="Message ID",
                    value=f"{payload.message_id}",
                    inline=False
                )
                
                # Send the log with limited info
                await logs_channel.send(embed=embed)
        
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        """Log message deletions using raw event to catch all deletions"""
        # Ignore DM channels
        if not payload.guild_id:
            return
            
        # Get guild
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
            
        # Get the message logs channel
        logs_channel = self.get_message_logs_channel(guild)
        if not logs_channel:
            return
            
        # Get channel where message was deleted
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return
            
        # Get cached message data
        message_data = self.message_cache.get(payload.message_id, {})
        
        # If we have cached data for this message
        if message_data:
            # Create embed for deletion log
            embed = nextcord.Embed(
                title="Message Deleted",
                description=f"Message deleted in {channel.mention}",
                color=EmbedColors.WARNING,
                timestamp=datetime.datetime.now()
            )
            
            # If we have the cached message
            content = message_data.get("content", "")
            attachments = message_data.get("attachments", [])
            
            # Add author info if we have cached author data
            if hasattr(payload, "cached_message") and payload.cached_message:
                author = payload.cached_message.author
                embed.set_author(
                    name=f"{author} ({author.id})",
                    icon_url=author.display_avatar.url
                )
            
            # Add content field if we have content
            if content:
                embed.add_field(
                    name="Content",
                    value=content[:1024],
                    inline=False
                )
            
            # Add attachments if any
            if attachments:
                embed.add_field(
                    name="Attachments",
                    value="\n".join(attachments)[:1024],
                    inline=False
                )
            
            # Add message ID
            embed.add_field(
                name="Message ID",
                value=f"{payload.message_id}",
                inline=False
            )
            
            # Send the log
            await logs_channel.send(embed=embed)
            
            # Remove from cache
            del self.message_cache[payload.message_id]
        else:
            # Message was not in cache, log with limited information
            embed = nextcord.Embed(
                title="Message Deleted (Limited Info)",
                description=f"Message deleted in {channel.mention}",
                color=EmbedColors.WARNING,
                timestamp=datetime.datetime.now()
            )
            
            # Add message ID
            embed.add_field(
                name="Message ID",
                value=f"{payload.message_id}",
                inline=False
            )
            
            # Add cached message info if available
            if hasattr(payload, "cached_message") and payload.cached_message:
                cached_message = payload.cached_message
                
                embed.set_author(
                    name=f"{cached_message.author} ({cached_message.author.id})",
                    icon_url=cached_message.author.display_avatar.url
                )
                
                if cached_message.content:
                    embed.add_field(
                        name="Content",
                        value=cached_message.content[:1024],
                        inline=False
                    )
                
                if cached_message.attachments:
                    attachments = [attachment.url for attachment in cached_message.attachments]
                    embed.add_field(
                        name="Attachments",
                        value="\n".join(attachments)[:1024],
                        inline=False
                    )
            
            # Send the log with limited info
            await logs_channel.send(embed=embed)
            
    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        """Log bulk message deletions using raw event"""
        # Ignore DM channels
        if not payload.guild_id:
            return
            
        # Get guild
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
            
        # Get the message logs channel
        logs_channel = self.get_message_logs_channel(guild)
        if not logs_channel:
            return
            
        # Get channel where messages were deleted
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return
            
        # Create embed for bulk deletion
        embed = nextcord.Embed(
            title="Bulk Message Deletion",
            description=f"{len(payload.message_ids)} messages were deleted in {channel.mention}",
            color=EmbedColors.ERROR,
            timestamp=datetime.datetime.now()
        )
        
        # Add the list of deleted message IDs
        embed.add_field(
            name="Deleted Message IDs",
            value=", ".join(str(msg_id) for msg_id in list(payload.message_ids)[:20]) + 
                  (f"\n... and {len(payload.message_ids) - 20} more" if len(payload.message_ids) > 20 else ""),
            inline=False
        )
        
        # Send the log
        await logs_channel.send(embed=embed)
        
        # Remove deleted messages from cache
        for message_id in payload.message_ids:
            if message_id in self.message_cache:
                del self.message_cache[message_id]
#=============================================================================================================================================================