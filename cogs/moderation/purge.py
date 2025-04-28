from nextcord.ext import commands
import nextcord
from typing import Optional


class Purge(commands.Cog):
    """A cog for message purging functionality"""
    
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
        description="Bulk delete messages from the current channel",
    )
    async def purge(
        self,
        interaction: nextcord.Interaction,
        amount: int = nextcord.SlashOption(
            description="Number of messages to delete (1-100)",
            required=True,
            min_value=1,
            max_value=100
        )
    ):
        """
        Purge messages from the current channel
        Parameters:
            interaction (nextcord.Interaction): The interaction object
            amount (int): Number of messages to delete (1-100)
        """
        try:
            # Check permissions first
            has_perms, error_msg = await self.check_permissions(interaction)
            if not has_perms:
                await interaction.response.send_message(error_msg, ephemeral=True)
                return

            # Defer response since purging might take time
            await interaction.response.defer(ephemeral=True)

            # Purge messages
            deleted = await interaction.channel.purge(limit=amount)  # +1 to account for command message
            
            # Send success message
            await interaction.followup.send(
                f"✨ Successfully purged {len(deleted)} messages.",
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
    #-------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Prefix command Implementation
    @commands.command(name="purge", description="Bulk delete messages from the current channel")
    @commands.has_permissions(manage_messages=True)
    async def purge_prefix(self, ctx, amount: int = 10):
        """
        Purge messages from the current channel
        Parameters:
            ctx (commands.Context): The context object
            amount (int): Number of messages to delete (1-100)
        """
        try:
            # Defer response since purging might take time
            await ctx.message.delete()
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to account for command message
            await ctx.send(f"✨ Successfully purged {len(deleted)} messages.", delete_after=5)

        except nextcord.errors.Forbidden:
            await ctx.send("❌ I don't have the required permissions to delete messages.", delete_after=5)
        except nextcord.HTTPException as e:
            await ctx.send(f"❌ Failed to purge messages: {str(e)}", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ An unexpected error occurred: {str(e)}", delete_after=5)
    #=============================================================================================================================================================