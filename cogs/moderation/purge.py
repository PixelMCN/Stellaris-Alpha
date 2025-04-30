from nextcord.ext import commands
import nextcord
from typing import Optional, List, Union
import random
import asyncio


class Purge(commands.Cog):
    """A cog for message purging functionality with advanced filters"""
    
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = bot.error_handler
        
        # List of purge reasons
        self.purge_reasons = [
            "Channel cleanup",
            "Removing spam",
            "Moderator request",
            "Organizing discussion"
        ]

    #=============================================================================================================================================================
    # Slash command Implementation
    @nextcord.slash_command(
        name="purge",
        description="Bulk delete messages from the current channel with filters"
    )
    async def purge(
        self,
        interaction: nextcord.Interaction,
        amount: int = nextcord.SlashOption(
            description="Number of messages to delete (1-100)",
            required=True,
            min_value=1,
            max_value=100
        ),
        filter: str = nextcord.SlashOption(
            description="Type of messages to filter",
            required=False,
            choices=["all", "user", "bot", "attachments", "links", "embeds"],
            default="all"
        ),
        user: nextcord.Member = nextcord.SlashOption(
            description="Filter messages from a specific user (only used with user filter)",
            required=False
        ),
        reason: str = nextcord.SlashOption(
            description="Reason for purging messages (optional)",
            required=False
        )
    ):
        """
        Purge messages from the current channel with filtering options
        Parameters:
            interaction (nextcord.Interaction): The interaction object
            amount (int): Number of messages to delete (1-100)
            filter (str): Type of messages to filter (all, user, bot, attachments, links, embeds)
            user (nextcord.Member): Optional user to filter messages from
            reason (str): Optional reason for the purge
        """
        try:
            # Check if user has manage messages permissions
            if not interaction.user.guild_permissions.manage_messages:
                embed = nextcord.Embed(
                    title="⚠️ Missing Permissions",
                    description="You need the **Manage Messages** permission to use this command.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Check if bot has manage messages permissions
            if not interaction.guild.me.guild_permissions.manage_messages:
                embed = nextcord.Embed(
                    title="⚠️ Bot Missing Permissions",
                    description="I need the **Manage Messages** permission to perform this action.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Check if user is provided when using user filter
            if filter == "user" and user is None:
                embed = nextcord.Embed(
                    title="⚠️ Missing Parameter",
                    description="You must specify a user when using the user filter.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Use a random reason if none is provided
            if reason is None:
                reason = random.choice(self.purge_reasons)
                full_reason = f"{reason} (Auto-generated reason)"
            else:
                full_reason = reason

            # Defer response since purging might take time
            await interaction.response.defer(ephemeral=True)
            
            # Create the appropriate check function based on filter
            check = None
            filter_description = "messages"
            
            if filter == "user" and user:
                check = lambda m: m.author.id == user.id
                filter_description = f"messages from {user.display_name}"
            elif filter == "bot":
                check = lambda m: m.author.bot
                filter_description = "bot messages"
            elif filter == "attachments":
                check = lambda m: len(m.attachments) > 0
                filter_description = "messages with attachments"
            elif filter == "links":
                check = lambda m: "http://" in m.content or "https://" in m.content
                filter_description = "messages containing links"
            elif filter == "embeds":
                check = lambda m: len(m.embeds) > 0
                filter_description = "messages with embeds"
            
            # Execute purge with or without check function
            if check is not None:
                deleted = await interaction.channel.purge(limit=amount, check=check)
            else:
                # For "all" type, don't provide a check function
                deleted = await interaction.channel.purge(limit=amount)
            
            # Create a detailed embed for the purge
            embed = nextcord.Embed(
                title="🧹 Messages Purged",
                description=f"{len(deleted)} {filter_description} have been deleted from {interaction.channel.mention}.",
                color=nextcord.Color.blue()
            )
            
            embed.add_field(name="Amount", value=f"{len(deleted)} messages", inline=True)
            embed.add_field(name="Filter", value=filter.capitalize(), inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Reason", value=full_reason, inline=False)
            
            if filter == "user" and user and user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
            
            # Send confirmation message without auto-delete
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # If you want to send a non-ephemeral message that auto-deletes, use a separate channel message
            # This is safer than using delete_after with interaction followups
            try:
                temp_msg = await interaction.channel.send(embed=embed)
                await asyncio.sleep(5)
                await temp_msg.delete()
            except Exception:
                # If this fails, we already have the ephemeral message as backup
                pass

        except nextcord.errors.Forbidden:
            embed = nextcord.Embed(
                title="❌ Permission Error",
                description="I don't have the required permissions to delete messages in this channel.",
                color=nextcord.Color.red()
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except nextcord.HTTPException as e:
            embed = nextcord.Embed(
                title="❌ Error",
                description=f"Failed to purge messages: {str(e)}",
                color=nextcord.Color.red()
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            # Let the global error handler handle other exceptions
            await self.error_handler.handle_command_error(interaction, e, "purge", is_followup=True)
    #=============================================================================================================================================================