import nextcord
import datetime
from nextcord.ext import commands

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Dictionary to store voice join timestamps
        self.voice_join_timestamps = {}


    # LOGS SETUP COMMAND - FIXED VERSION
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="logs", description="Creates logging channels in a Logs category for messages & server events")
    async def logs(self, ctx: nextcord.Interaction):
        if not ctx.user.guild_permissions.manage_channels:
            await ctx.response.send_message("This command requires `manage channels` permission", ephemeral=True)
            return

        # Acknowledge the interaction immediately to prevent timeout
        await ctx.response.defer(ephemeral=True)
        
        guild = ctx.guild

        # Create a category for logs if it doesn't exist
        admin_role = nextcord.utils.get(guild.roles, permissions=nextcord.Permissions(administrator=True))
        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(view_channel=False),
        }
        if admin_role:
            overwrites[admin_role] = nextcord.PermissionOverwrite(view_channel=True)
        else:
            # If no role with admin permission is found, allow only users with admin permission
            for role in guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = nextcord.PermissionOverwrite(view_channel=True)

        log_category = nextcord.utils.get(guild.categories, name="Logs")
        if not log_category:
            log_category = await guild.create_category("Logs", overwrites=overwrites)

        # Define channel names (added mod-logs)
        channel_names = {
            "message-logs": "Channel for message logging",
            "server-logs": "Channel for server updates logging",
            "voice-logs": "Channel for voice logging",
            "mod-logs": "Channel for moderation action logging"
        }

        created_channels = []
        for name, purpose in channel_names.items():
            existing_channel = nextcord.utils.get(guild.text_channels, name=name)
            if not existing_channel:
                channel = await guild.create_text_channel(name, category=log_category, topic=purpose)
                created_channels.append(channel.mention)
            else:
                created_channels.append(existing_channel.mention)

        await ctx.followup.send(
            f"Logging channels created or already exist:\n"
            f"Message Logs: {created_channels[0]}\n"
            f"Server Logs: {created_channels[1]}\n"
            f"Voice Logs: {created_channels[2]}\n"
            f"Mod Logs: {created_channels[3]}",
            ephemeral=True
        )
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Prefix command implementation
    @commands.command(name="logs", aliases=["logsetup"])
    async def logs_prefix(self, ctx):
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("This command requires `manage channels` permission")
            return

        # Acknowledge the command immediately to prevent timeout
        await ctx.send("Creating logging channels...")

        guild = ctx.guild

        # Create a category for logs if it doesn't exist
        admin_role = nextcord.utils.get(guild.roles, permissions=nextcord.Permissions(administrator=True))
        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(view_channel=False),
        }
        if admin_role:
            overwrites[admin_role] = nextcord.PermissionOverwrite(view_channel=True)
        else:
            # If no role with admin permission is found, allow only users with admin permission
            for role in guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = nextcord.PermissionOverwrite(view_channel=True)

        log_category = nextcord.utils.get(guild.categories, name="Logs")
        if not log_category:
            log_category = await guild.create_category("Logs", overwrites=overwrites)

        # Define channel names
        channel_names = {
            "message-logs": "Channel for message logging",
            "server-logs": "Channel for server updates logging",
            "voice-logs": "Channel for voice logging",
            "mod-logs": "Channel for moderation action logging"
        }
        created_channels = []
        for name, purpose in channel_names.items():
            existing_channel = nextcord.utils.get(guild.text_channels, name=name)
            if not existing_channel:
                channel = await guild.create_text_channel(name, category=log_category, topic=purpose)
                created_channels.append(channel.mention)
            else:
                created_channels.append(existing_channel.mention)

        await ctx.send(
            f"Logging channels created or already exist:\n"
            f"Message Logs: {created_channels[0]}\n"
            f"Server Logs: {created_channels[1]}\n"
            f"Voice Logs: {created_channels[2]}\n"
            f"Mod Logs: {created_channels[3]}",
            ephemeral=True
        )
    #=============================================================================================================================================================

    # MESSAGE DELETE
    #=============================================================================================================================================================
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        logs_channel = nextcord.utils.get(message.guild.channels, name="message-logs")
        if logs_channel:
            timestamp = datetime.datetime.now()
            embed = nextcord.Embed(
                title="Message Deleted",
                description=f"A message by {message.author.display_name} was deleted",
                color=0xFF5555,
                timestamp=timestamp
            )
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.add_field(name="Author", value=message.author.mention, inline=True)
            embed.add_field(name="Channel", value=message.channel.mention, inline=True)
            embed.add_field(name="Content", value=message.content if message.content else "*No text content*", inline=False)
            
            # Handle attachments if any
            if message.attachments:
                attachment_list = "\n".join([f"[{attachment.filename}]({attachment.proxy_url})" for attachment in message.attachments])
                embed.add_field(name="Attachments", value=attachment_list, inline=False)
                
            embed.set_footer(text=f"User ID: {message.author.id} | Message ID: {message.id}")
            await logs_channel.send(embed=embed)
    #=============================================================================================================================================================


    # MESSAGE EDIT
    #=============================================================================================================================================================
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return

        logs_channel = nextcord.utils.get(before.guild.channels, name="message-logs")
        if logs_channel:
            timestamp = datetime.datetime.now()
            embed = nextcord.Embed(
                title="Message Edited",
                description=f"A message by {before.author.display_name} was edited in {before.channel.mention}",
                color=0xFFAA00,
                timestamp=timestamp
            )
            embed.set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url)
            embed.add_field(name="Author", value=before.author.mention, inline=True)
            embed.add_field(name="Channel", value=before.channel.mention, inline=True)
            embed.add_field(name="Jump to Message", value=f"[Click Here]({after.jump_url})", inline=True)
            embed.add_field(name="Before", value=before.content if before.content else "*No text content*", inline=True)
            embed.add_field(name="After", value=after.content if after.content else "*No text content*", inline=True)
            embed.set_footer(text=f"User ID: {before.author.id} | Message ID: {before.id}")
            await logs_channel.send(embed=embed)
    #=============================================================================================================================================================


    # CHANNEL CREATE
    #=============================================================================================================================================================
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if not isinstance(channel, nextcord.abc.GuildChannel):
            return
            
        logs_channel = nextcord.utils.get(channel.guild.channels, name="server-logs")
        if not logs_channel:
            return
            
        timestamp = datetime.datetime.now()
        moderator = None
        
        if channel.guild.me.guild_permissions.view_audit_log:
            async for entry in channel.guild.audit_logs(limit=1, action=nextcord.AuditLogAction.channel_create):
                if entry.target.id == channel.id:
                    moderator = entry.user
                    break
        
        embed = nextcord.Embed(
            title="Channel Created",
            description=f"A new channel was created",
            color=0x55FF55,
            timestamp=timestamp
        )
        
        if moderator:
            embed.set_author(name=moderator.display_name, icon_url=moderator.display_avatar.url)
            embed.add_field(name="Created By", value=moderator.mention, inline=True)
        
        channel_type = str(channel.type).replace('_', ' ').title()
        embed.add_field(name="Channel", value=channel.mention if hasattr(channel, "mention") else channel.name, inline=True)
        embed.add_field(name="Type", value=channel_type, inline=True)
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
        embed.set_footer(text=f"Channel ID: {channel.id}")
        await logs_channel.send(embed=embed)
    #=============================================================================================================================================================


    # CHANNEL DELETE
    #=============================================================================================================================================================
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if not isinstance(channel, nextcord.abc.GuildChannel):
            return
            
        logs_channel = nextcord.utils.get(channel.guild.channels, name="server-logs")
        if not logs_channel:
            return
            
        timestamp = datetime.datetime.now()
        moderator = None
        
        if channel.guild.me.guild_permissions.view_audit_log:
            async for entry in channel.guild.audit_logs(limit=1, action=nextcord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    moderator = entry.user
                    break
        
        embed = nextcord.Embed(
            title="Channel Deleted",
            description=f"A channel was deleted",
            color=0xFF5555,
            timestamp=timestamp
        )
        
        if moderator:
            embed.set_author(name=moderator.display_name, icon_url=moderator.display_avatar.url)
            embed.add_field(name="Deleted By", value=moderator.mention, inline=True)
        
        channel_type = str(channel.type).replace('_', ' ').title()
        embed.add_field(name="Channel", value=channel.name, inline=True)
        embed.add_field(name="Type", value=channel_type, inline=True)
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
        embed.set_footer(text=f"Channel ID: {channel.id}")
        await logs_channel.send(embed=embed)
    #=============================================================================================================================================================


    # CHANNEL UPDATE
    #=============================================================================================================================================================
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if not isinstance(before, nextcord.abc.GuildChannel):
            return
            
        logs_channel = nextcord.utils.get(before.guild.channels, name="server-logs")
        if not logs_channel:
            return
            
        # Check if anything significant changed
        if (before.name == after.name and 
            before.position == after.position and 
            before.category == after.category):
            return  # No significant changes
            
        timestamp = datetime.datetime.now()
        moderator = None
        
        if before.guild.me.guild_permissions.view_audit_log:
            async for entry in before.guild.audit_logs(limit=1, action=nextcord.AuditLogAction.channel_update):
                if entry.target.id == before.id:
                    moderator = entry.user
                    break
        
        embed = nextcord.Embed(
            title="Channel Updated",
            description=f"A channel was modified",
            color=0xFFAA00,
            timestamp=timestamp
        )
        
        if moderator:
            embed.set_author(name=moderator.display_name, icon_url=moderator.display_avatar.url)
            embed.add_field(name="Updated By", value=moderator.mention, inline=True)
        
        embed.add_field(name="Channel", value=after.mention if hasattr(after, "mention") else after.name, inline=True)
        
        # Track specific changes
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Name:** {before.name} → {after.name}")
            
        if before.position != after.position:
            changes.append(f"**Position:** {before.position} → {after.position}")
            
        if before.category != after.category:
            before_category = before.category.name if before.category else "None"
            after_category = after.category.name if after.category else "None"
            changes.append(f"**Category:** {before_category} → {after_category}")
        
        if hasattr(before, "topic") and hasattr(after, "topic") and before.topic != after.topic:
            before_topic = before.topic or "None"
            after_topic = after.topic or "None"
            if len(before_topic) > 100:
                before_topic = before_topic[:97] + "..."
            if len(after_topic) > 100:
                after_topic = after_topic[:97] + "..."
            changes.append(f"**Topic:** {before_topic} → {after_topic}")
            
        if changes:
            embed.add_field(name="Changes", value="\n".join(changes), inline=False)
        
        embed.set_footer(text=f"Channel ID: {before.id}")
        await logs_channel.send(embed=embed)
    #=============================================================================================================================================================


    # VOICE CHANNEL EVENTS
    #=============================================================================================================================================================
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        logs_channel = nextcord.utils.get(member.guild.channels, name="voice-logs")
        if not logs_channel:
            return
            
        timestamp = datetime.datetime.now()
        member_key = f"{member.guild.id}-{member.id}"
        
        # Handle different voice state changes
        if before.channel and not after.channel:
            # User left a voice channel
            embed = nextcord.Embed(
                title="Voice Channel Left",
                description=f"{member.display_name} left a voice channel",
                color=0xFF5555,
                timestamp=timestamp
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Channel", value=before.channel.mention, inline=True)
            
            # Check if user was in voice for a trackable amount of time
            if member_key in self.voice_join_timestamps:
                join_time = self.voice_join_timestamps[member_key]
                duration = timestamp - join_time
                minutes, seconds = divmod(duration.total_seconds(), 60)
                hours, minutes = divmod(minutes, 60)
                time_string = f"{int(hours)}h {int(minutes)}m {int(seconds)}s" if hours else f"{int(minutes)}m {int(seconds)}s"
                embed.add_field(name="Duration", value=time_string, inline=True)
                # Remove the timestamp since they've left
                del self.voice_join_timestamps[member_key]
                
        elif not before.channel and after.channel:
            # User joined a voice channel
            embed = nextcord.Embed(
                title="Voice Channel Joined",
                description=f"{member.display_name} joined a voice channel",
                color=0x55FF55,
                timestamp=timestamp
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Channel", value=after.channel.mention, inline=True)
            
            # Store join timestamp for duration tracking
            self.voice_join_timestamps[member_key] = timestamp
            
        elif before.channel and after.channel and before.channel != after.channel:
            # User moved between voice channels
            embed = nextcord.Embed(
                title="Voice Channel Moved",
                description=f"{member.display_name} moved between voice channels",
                color=0x5555FF,
                timestamp=timestamp
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="From", value=before.channel.mention, inline=True)
            embed.add_field(name="To", value=after.channel.mention, inline=True)
            
        elif before.self_mute != after.self_mute:
            # User muted or unmuted themselves
            status = "muted" if after.self_mute else "unmuted"
            embed = nextcord.Embed(
                title=f"User {status.capitalize()} Themselves",
                description=f"{member.display_name} {status} themselves in {after.channel.mention}",
                color=0xAAAAFF,
                timestamp=timestamp
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Channel", value=after.channel.mention, inline=True)
            
        elif before.self_deaf != after.self_deaf:
            # User deafened or undeafened themselves
            status = "deafened" if after.self_deaf else "undeafened"
            embed = nextcord.Embed(
                title=f"User {status.capitalize()} Themselves",
                description=f"{member.display_name} {status} themselves in {after.channel.mention}",
                color=0xAAAAFF,
                timestamp=timestamp
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Channel", value=after.channel.mention, inline=True)
            
        elif before.mute != after.mute:
            # User was server muted or unmuted
            status = "muted" if after.mute else "unmuted"
            embed = nextcord.Embed(
                title=f"User Server {status.capitalize()}",
                description=f"{member.display_name} was server {status} in {after.channel.mention}",
                color=0xFFAAAA,
                timestamp=timestamp
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Channel", value=after.channel.mention, inline=True)
            
            # Try to find who did the action
            if member.guild.me.guild_permissions.view_audit_log:
                async for entry in member.guild.audit_logs(limit=1, action=nextcord.AuditLogAction.member_update):
                    if entry.target.id == member.id:
                        embed.add_field(name="Moderator", value=entry.user.mention, inline=True)
                        break
            
        elif before.deaf != after.deaf:
            # User was server deafened or undeafened
            status = "deafened" if after.deaf else "undeafened"
            embed = nextcord.Embed(
                title=f"User Server {status.capitalize()}",
                description=f"{member.display_name} was server {status} in {after.channel.mention}",
                color=0xFFAAAA,
                timestamp=timestamp
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Channel", value=after.channel.mention, inline=True)
            
            # Try to find who did the action
            if member.guild.me.guild_permissions.view_audit_log:
                async for entry in member.guild.audit_logs(limit=1, action=nextcord.AuditLogAction.member_update):
                    if entry.target.id == member.id:
                        embed.add_field(name="Moderator", value=entry.user.mention, inline=True)
                        break
        else:
            # Other voice state changes we don't need to track
            return
            
        embed.set_footer(text=f"User ID: {member.id}")
        await logs_channel.send(embed=embed)
    #=============================================================================================================================================================


    # MODERATION ACTIONS (NEW)
    #=============================================================================================================================================================
    # Member ban event
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        logs_channel = nextcord.utils.get(guild.channels, name="mod-logs")
        if not logs_channel:
            return
            
        timestamp = datetime.datetime.now()
        moderator = None
        reason = "No reason provided"
        
        # Get moderator and reason from audit logs
        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=1, action=nextcord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    if entry.reason:
                        reason = entry.reason
                    break
        
        embed = nextcord.Embed(
            title="Member Banned",
            description=f"{user.display_name} was banned from the server",
            color=0xDC143C,  # Crimson red
            timestamp=timestamp
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User", value=f"{user.mention} ({user.name})", inline=True)
        
        if moderator:
            embed.add_field(name="Banned By", value=moderator.mention, inline=True)
        
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"User ID: {user.id}")
        
        await logs_channel.send(embed=embed)
    
    # Member unban event
    #=============================================================================================================================================================
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        logs_channel = nextcord.utils.get(guild.channels, name="mod-logs")
        if not logs_channel:
            return
            
        timestamp = datetime.datetime.now()
        moderator = None
        
        # Get moderator from audit logs
        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=1, action=nextcord.AuditLogAction.unban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    break
        
        embed = nextcord.Embed(
            title="Member Unbanned",
            description=f"{user.display_name} was unbanned from the server",
            color=0x32CD32,  # Lime green
            timestamp=timestamp
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User", value=f"{user.name} ({user.id})", inline=True)
        
        if moderator:
            embed.add_field(name="Unbanned By", value=moderator.mention, inline=True)
            
        embed.set_footer(text=f"User ID: {user.id}")
        
        await logs_channel.send(embed=embed)
    
    # Member kick event
    #=============================================================================================================================================================
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        logs_channel = nextcord.utils.get(guild.channels, name="mod-logs")
        if not logs_channel:
            return
            
        # Check if this was a kick (we need to check the audit logs)
        if not guild.me.guild_permissions.view_audit_log:
            return
            
        # Look for a kick entry in audit logs
        was_kicked = False
        moderator = None
        reason = "No reason provided"
        
        async for entry in guild.audit_logs(limit=5, action=nextcord.AuditLogAction.kick):
            if entry.target.id == member.id and (datetime.datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds() < 10:
                was_kicked = True
                moderator = entry.user
                if entry.reason:
                    reason = entry.reason
                break
                
        # If it wasn't a kick, don't log it here (will likely be caught by other events)
        if not was_kicked:
            return
            
        timestamp = datetime.datetime.now()
        
        embed = nextcord.Embed(
            title="Member Kicked",
            description=f"{member.display_name} was kicked from the server",
            color=0xFF8C00,  # Dark orange
            timestamp=timestamp
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User", value=f"{member.mention} ({member.name})", inline=True)
        
        if moderator:
            embed.add_field(name="Kicked By", value=moderator.mention, inline=True)
            
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        
        await logs_channel.send(embed=embed)
    
    # Timeout (Communication Disable) Event 
    #=============================================================================================================================================================
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.guild is None:
            return
            
        logs_channel = nextcord.utils.get(before.guild.channels, name="mod-logs")
        if not logs_channel:
            return
            
        # Check if timeout state changed
        before_timeout = before.communication_disabled_until
        after_timeout = after.communication_disabled_until
        
        if before_timeout == after_timeout:
            return  # No change in timeout state
            
        timestamp = datetime.datetime.now()
        moderator = None
        reason = "No reason provided"
        
        # Get moderator from audit logs
        if before.guild.me.guild_permissions.view_audit_log:
            async for entry in before.guild.audit_logs(limit=1, action=nextcord.AuditLogAction.member_update):
                if entry.target.id == before.id:
                    moderator = entry.user
                    if entry.reason:
                        reason = entry.reason
                    break
        
        # Timeout added
        if (before_timeout is None or before_timeout < datetime.datetime.now(datetime.timezone.utc)) and after_timeout is not None and after_timeout > datetime.datetime.now(datetime.timezone.utc):
            # Calculate duration
            now = datetime.datetime.now(datetime.timezone.utc)
            duration = after_timeout - now
            minutes = duration.total_seconds() // 60
            hours = minutes // 60
            days = hours // 24
            
            if days >= 1:
                duration_str = f"{int(days)} day(s)"
            elif hours >= 1:
                duration_str = f"{int(hours)} hour(s)"
            else:
                duration_str = f"{int(minutes)} minute(s)"
                
            embed = nextcord.Embed(
                title="Member Timed Out",
                description=f"{after.display_name} was timed out",
                color=0xFFA500,  # Orange
                timestamp=timestamp
            )
            
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.add_field(name="User", value=after.mention, inline=True)
            embed.add_field(name="Duration", value=duration_str, inline=True)
            
            if moderator and moderator.id != after.id:  # Ensure moderator is not the same as user
                embed.add_field(name="Moderator", value=moderator.mention, inline=True)
                
            embed.add_field(name="Expires", value=f"<t:{int(after_timeout.timestamp())}:R>", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
        # Timeout removed
        elif before_timeout is not None and before_timeout > datetime.datetime.now(datetime.timezone.utc) and (after_timeout is None or after_timeout < datetime.datetime.now(datetime.timezone.utc)):
            embed = nextcord.Embed(
                title="Timeout Removed",
                description=f"{after.display_name}'s timeout was removed",
                color=0x3CB371,  # Medium sea green
                timestamp=timestamp
            )
            
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.add_field(name="User", value=after.mention, inline=True)
            
            if moderator and moderator.id != after.id:
                embed.add_field(name="Moderator", value=moderator.mention, inline=True)
                
            embed.add_field(name="Reason", value=reason, inline=False)
        else:
            # No relevant timeout change
            return
            
        embed.set_footer(text=f"User ID: {after.id}")
        await logs_channel.send(embed=embed)
    
    # Bulk message delete event
    #=============================================================================================================================================================
    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages:
            return
            
        # Get the first message to extract guild and channel info
        message = messages[0]
        logs_channel = nextcord.utils.get(message.guild.channels, name="mod-logs")
        if not logs_channel:
            return
            
        timestamp = datetime.datetime.now()
        
        # Try to find who deleted the messages
        moderator = None
        if message.guild.me.guild_permissions.view_audit_log:
            async for entry in message.guild.audit_logs(limit=1, action=nextcord.AuditLogAction.message_bulk_delete):
                # The audit log entry for bulk message delete doesn't have a count attribute
                # Instead, check if the channel matches
                if hasattr(entry.extra, 'channel') and entry.extra.channel.id == message.channel.id:
                    moderator = entry.user
                    break
        
        embed = nextcord.Embed(
            title="Bulk Messages Deleted",
            description=f"{len(messages)} messages were deleted in {message.channel.mention}",
            color=0x800080,  # Purple
            timestamp=timestamp
        )
        
        if moderator:
            embed.add_field(name="Deleted By", value=moderator.mention, inline=True)
            
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Message Count", value=str(len(messages)), inline=True)
        
        # Try to extract some authors info
        authors = {}
        for msg in messages:
            if not msg.author.bot:  # Skip bot messages
                author_id = msg.author.id
                if author_id in authors:
                    authors[author_id] += 1
                else:
                    authors[author_id] = 1
        
        if authors:
            author_list = []
            for author_id, count in authors.items():
                author = message.guild.get_member(author_id)
                if author:
                    author_list.append(f"{author.mention}: {count} message(s)")
            
            if author_list:
                embed.add_field(name="Authors Affected", value="\n".join(author_list[:10]), inline=False)
                if len(author_list) > 10:
                    embed.add_field(name="Note", value=f"And {len(author_list) - 10} more authors...", inline=False)
        
        embed.set_footer(text=f"Channel ID: {message.channel.id}")
        await logs_channel.send(embed=embed)
    #=============================================================================================================================================================