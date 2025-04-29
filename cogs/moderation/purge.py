from nextcord.ext import commands
import nextcord
from typing import Optional, List, Union


class Purge(commands.Cog):
    """A cog for message purging functionality with advanced filters"""
    
    def __init__(self, bot):
        self.bot = bot

    async def check_permissions(self, interaction: nextcord.Interaction) -> tuple[bool, Optional[str]]:
        """Check both bot and user permissions"""
        if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
            return False, "I need the `Manage Messages` permission to use this command."
        
        if not interaction.user.guild_permissions.manage_messages:
            return False, "You need the `Manage Messages` permission to use this command."
            
        return True, None

    #=============================================================================================================================================================
    # Slash command Implementation
    @nextcord.slash_command(
        name="purge",
        description="Bulk delete messages from the current channel with filters",
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
            choices=["all", "member", "bot", "attachments"],
            default="all"
        ),
        member: nextcord.Member = nextcord.SlashOption(
            description="Filter messages from a specific member (only used with member filter)",
            required=False
        )
    ):
        """
        Purge messages from the current channel with filtering options
        Parameters:
            interaction (nextcord.Interaction): The interaction object
            amount (int): Number of messages to delete (1-100)
            filter_type (str): Type of messages to filter (all, member, bot, attachments)
            member (nextcord.Member): Optional member to filter messages from
        """
        try:
            # Check permissions first
            has_perms, error_msg = await self.check_permissions(interaction)
            if not has_perms:
                await interaction.response.send_message(error_msg, ephemeral=True)
                return

            # Check if member is provided when using member filter
            if filter == "member" and member is None:
                await interaction.response.send_message(
                    "❌ You must specify a member when using the member filter.",
                    ephemeral=True
                )
                return

            # Defer response since purging might take time
            await interaction.response.defer(ephemeral=True)
            
            # Create the appropriate check function based on filter_type
            check = None
            filter_description = "messages"
            
            if filter == "member" and member:
                check = lambda m: m.author.id == member.id
                filter_description = f"messages from {member.display_name}"
            elif filter == "bot":
                check = lambda m: m.author.bot
                filter_description = "bot messages"
            elif filter == "attachments":
                check = lambda m: len(m.attachments) > 0
                filter_description = "messages with attachments"
            
            # Execute purge with or without check function
            if check is not None:
                deleted = await interaction.channel.purge(limit=amount, check=check)
            else:
                # For "all" type, don't provide a check function
                deleted = await interaction.channel.purge(limit=amount)
            
            # Send success message
            await interaction.followup.send(
                f"✨ Successfully purged {len(deleted)} {filter_description}.",
                ephemeral=True
            )

        except nextcord.errors.Forbidden:
            await interaction.followup.send(
                "❌ I don't have the required permissions to delete messages.",
                ephemeral=True
            )
        except nextcord.HTTPException as e:
            await interaction.followup.send(
                f"❌ Failed to purge messages: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ An unexpected error occurred: {str(e)}",
                ephemeral=True
            )
    #============================================================================================================================================================="