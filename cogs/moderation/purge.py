import nextcord
from nextcord.ext import commands
import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, List
from utils.embed_helper import EmbedHelper
from utils.error_handler import ErrorHandler
#=============================================================================================================================================================
class PurgeCommands(commands.Cog):
    """Commands for bulk message deletion"""
    
    def __init__(self, bot):
        self.bot = bot
        self.error_handler = ErrorHandler(bot)
    #=============================================================================================================================================================    
    @nextcord.slash_command(
        name="purge",
        description="Delete multiple messages at once with filters"
    )
    async def purge(
        self, 
        interaction: nextcord.Interaction,
        amount: int = nextcord.SlashOption(
            description="Number of messages to delete (1-100)",
            min_value=1,
            max_value=100
        ),
        user: nextcord.Member = nextcord.SlashOption(
            description="Only delete messages from this user",
            required=False
        ),
        contains: str = nextcord.SlashOption(
            description="Only delete messages containing this text",
            required=False
        ),
        attachments: bool = nextcord.SlashOption(
            description="Only delete messages with attachments",
            required=False,
            default=False
        ),
        embeds: bool = nextcord.SlashOption(
            description="Only delete messages with embeds",
            required=False,
            default=False
        ),
        links: bool = nextcord.SlashOption(
            description="Only delete messages containing links",
            required=False,
            default=False
        ),
        invites: bool = nextcord.SlashOption(
            description="Only delete messages containing Discord invites",
            required=False,
            default=False
        ),
        bots: bool = nextcord.SlashOption(
            description="Only delete messages from bots",
            required=False,
            default=False
        )
    ):
        """Delete multiple messages at once with various filters"""
        # Check for permissions
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Messages"),
                ephemeral=True
            )
            return
            
        if not interaction.guild.me.guild_permissions.manage_messages:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Manage Messages"),
                ephemeral=True
            )
            return
            
        # Defer response since purging might take time
        await interaction.response.defer(ephemeral=True)
        
        # Compile regex patterns for links and invites if needed
        link_pattern = re.compile(r'https?://\S+') if links else None
        invite_pattern = re.compile(r'discord(?:\.gg|app\.com/invite)/\S+') if invites else None
        
        # Define the check function for message filtering
        def message_check(message):
            # Skip the interaction message itself
            if message.id == interaction.id:
                return False
                
            # Filter by user if specified
            if user and message.author.id != user.id:
                return False
                
            # Filter by content if specified
            if contains and contains.lower() not in message.content.lower():
                return False
                
            # Filter by attachments if specified
            if attachments and not message.attachments:
                return False
                
            # Filter by embeds if specified
            if embeds and not message.embeds:
                return False
                
            # Filter by links if specified
            if links and not link_pattern.search(message.content):
                return False
                
            # Filter by invites if specified
            if invites and not invite_pattern.search(message.content):
                return False
                
            # Filter by bots if specified
            if bots and not message.author.bot:
                return False
                
            return True
            
        try:
            # Get messages to delete
            messages = []
            async for message in interaction.channel.history(limit=amount + 50):  # Get extra to account for filtered messages
                if message_check(message):
                    messages.append(message)
                    if len(messages) >= amount:
                        break
                        
            # Check if we found any messages to delete
            if not messages:
                await interaction.followup.send(
                    embed=EmbedHelper.warning_embed(
                        "No Messages Found",
                        "No messages matched your filter criteria."
                    ),
                    ephemeral=True
                )
                return
                
            # Check for messages older than 14 days (Discord limitation)
            two_weeks_ago = datetime.now(timezone.utc) - timedelta(days=14)
            
            # Split messages into those newer and older than 14 days
            recent_messages = [msg for msg in messages if msg.created_at.replace(tzinfo=timezone.utc) > two_weeks_ago]
            old_messages = [msg for msg in messages if msg.created_at.replace(tzinfo=timezone.utc) <= two_weeks_ago]
            
            # Delete recent messages in bulk if possible
            deleted_count = 0
            if recent_messages:
                await interaction.channel.delete_messages(recent_messages)
                deleted_count += len(recent_messages)
                
            # Delete older messages individually
            for message in old_messages:
                try:
                    await message.delete()
                    deleted_count += 1
                    await asyncio.sleep(0.5)  # Add small delay to avoid rate limits
                except:
                    pass
                    
            # Create success embed
            success_embed = EmbedHelper.success_embed(
                "Messages Purged",
                f"Successfully deleted **{deleted_count}** message{'s' if deleted_count != 1 else ''}."
            )
            
            # Add filter information
            filter_parts = []
            if user:
                filter_parts.append(f"User: {user.mention}")
            if contains:
                filter_parts.append(f"Contains: '{contains}'")
            if attachments:
                filter_parts.append("Has attachments")
            if embeds:
                filter_parts.append("Has embeds")
            if links:
                filter_parts.append("Contains links")
            if invites:
                filter_parts.append("Contains invites")
            if bots:
                filter_parts.append("From bots")
                
            if filter_parts:
                success_embed.add_field(name="Filters Applied", value="\n".join(f"• {part}" for part in filter_parts), inline=False)
                
            # Send success message
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
            # Send a temporary notification in the channel
            notification = await interaction.channel.send(
                embed=EmbedHelper.moderation_embed(
                    "Messages Purged",
                    f"**{deleted_count}** message{'s' if deleted_count != 1 else ''} {'were' if deleted_count != 1 else 'was'} deleted.",
                    emoji="🧹",
                    moderator=interaction.user
                )
            )
            
            # Delete the notification after a few seconds
            await asyncio.sleep(5)
            try:
                await notification.delete()
            except:
                pass
                
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    log_embed = EmbedHelper.moderation_embed(
                        "Messages Purged",
                        f"**{deleted_count}** message{'s' if deleted_count != 1 else ''} {'were' if deleted_count != 1 else 'was'} deleted in {interaction.channel.mention}.",
                        emoji="🧹",
                        moderator=interaction.user
                    )
                    
                    if filter_parts:
                        log_embed.add_field(name="Filters Applied", value="\n".join(f"• {part}" for part in filter_parts), inline=False)
                        
                    await log_channel.send(embed=log_embed)
            except:
                pass
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "purge", True)
    #=============================================================================================================================================================        
    @nextcord.slash_command(
        name="clear",
        description="Clear all messages in a channel"
    )
    async def clear(
        self, 
        interaction: nextcord.Interaction
    ):
        """Clear all messages in a channel"""
        # Check for permissions
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Messages"),
                ephemeral=True
            )
            return
            
        if not interaction.guild.me.guild_permissions.manage_messages:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Manage Messages"),
                ephemeral=True
            )
            return
        
        # We need Administrator permission to clone and delete a channel
        if not interaction.guild.me.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Administrator"),
                ephemeral=True
            )
            return
            
        # Confirm deletion
        confirmation_embed = EmbedHelper.warning_embed(
            "Confirm Clear",
            f"Are you sure you want to clear **ALL** messages in {interaction.channel.mention}? This cannot be undone."
        )
        
        # Create confirmation buttons
        class ConfirmView(nextcord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.value = None
                
            @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.danger)
            async def confirm(self, button: nextcord.ui.Button, i: nextcord.Interaction):
                if i.user.id != interaction.user.id:
                    await i.response.send_message("You cannot use this button.", ephemeral=True)
                    return
                    
                self.value = True
                for child in self.children:
                    child.disabled = True
                await i.response.edit_message(view=self)
                self.stop()
                
            @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.secondary)
            async def cancel(self, button: nextcord.ui.Button, i: nextcord.Interaction):
                if i.user.id != interaction.user.id:
                    await i.response.send_message("You cannot use this button.", ephemeral=True)
                    return
                    
                self.value = False
                for child in self.children:
                    child.disabled = True
                await i.response.edit_message(view=self)
                self.stop()
                
            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True
                try:
                    await self.message.edit(view=self)
                except:
                    pass
        
        # Send confirmation message
        view = ConfirmView()
        await interaction.response.send_message(embed=confirmation_embed, view=view, ephemeral=True)
        
        # Wait for response
        await view.wait()
        
        if not view.value:
            cancel_embed = EmbedHelper.info_embed("Action Cancelled", "Channel clearing has been cancelled.")
            await interaction.followup.send(embed=cancel_embed, ephemeral=True)
            return
            
        # Proceed with clearing the channel
        try:
            # Get the channel information for recreation
            channel = interaction.channel
            channel_name = channel.name
            channel_topic = getattr(channel, "topic", None)
            channel_position = channel.position
            channel_category = channel.category
            channel_overwrites = channel.overwrites
            
            # Create the new channel with same settings
            new_channel = await channel.clone(
                name=channel_name,
                reason=f"Channel cleared by {interaction.user}"
            )
            
            # Reorder the new channel to be in the same position
            try:
                await new_channel.edit(position=channel_position)
            except:
                pass
                
            # Delete the original channel
            await channel.delete(reason=f"Channel cleared by {interaction.user}")
            
            # Send a notification in the new channel
            notification = await new_channel.send(
                embed=EmbedHelper.moderation_embed(
                    "Channel Cleared",
                    "This channel has been cleared of all messages.",
                    emoji="🧹",
                    moderator=interaction.user
                )
            )
            
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    log_embed = EmbedHelper.moderation_embed(
                        "Channel Cleared",
                        f"Channel {new_channel.mention} (previously {channel_name}) was cleared of all messages.",
                        emoji="🧹",
                        moderator=interaction.user
                    )
                        
                    await log_channel.send(embed=log_embed)
            except:
                pass
                
            # DM the user since we can't send an ephemeral follow-up after the channel is deleted
            try:
                success_embed = EmbedHelper.success_embed(
                    "Channel Cleared",
                    f"Successfully cleared all messages from #{channel_name} in {interaction.guild.name}."
                )
                await interaction.user.send(embed=success_embed)
            except:
                pass
                
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "clear", True)
#=============================================================================================================================================================