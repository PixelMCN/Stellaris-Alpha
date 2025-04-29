import nextcord
import random
from nextcord.ext import commands
from nextcord import Interaction

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Check if error_handler exists, otherwise create a simple handler
        self.error_handler = getattr(bot, 'error_handler', None)

    # List of ban reasons
    ban_reasons = [
        "Breaking server rules",
        "Inappropriate behavior",
        "Spamming",
        "Harassment"
    ]
    # BAN COMMAND
    #=============================================================================================================================================================
    @nextcord.slash_command(name="ban", description="Ban a member from the server")
    async def ban(self, interaction: Interaction, member: nextcord.Member, reason: str = None, delete_messages: int = 0):
        try:
            # Check if the user has ban permissions
            if not interaction.user.guild_permissions.ban_members:
                await interaction.response.send_message("You don't have permission to ban members.", ephemeral=True)
                return
                
            # Check if the bot has ban permissions
            if not interaction.guild.me.guild_permissions.ban_members:
                await interaction.response.send_message("I don't have permission to ban members.", ephemeral=True)
                return
                
            # Check if the user is trying to ban someone with a higher role
            if interaction.user.top_role <= member.top_role and interaction.user.id != interaction.guild.owner_id:
                await interaction.response.send_message("You can't ban someone with a higher or equal role.", ephemeral=True)
                return
                
            # Check if the bot can ban the target member
            if interaction.guild.me.top_role <= member.top_role:
                await interaction.response.send_message("I can't ban someone with a higher or equal role than me.", ephemeral=True)
                return

            # Use a random reason if none is provided
            if reason is None:
                reason = random.choice(self.ban_reasons)

            # Convert delete_messages to seconds (1 day = 86400 seconds)
            delete_seconds = min(7, max(0, delete_messages)) * 86400
            
            # Ban the member
            await member.ban(reason=reason, delete_message_seconds=delete_seconds)
            
            # Send confirmation message
            await interaction.response.send_message(f'{member.mention} has been banned for: {reason}')
            
            # Try to DM the banned user
            try:
                await member.send(f"You have been banned from **{interaction.guild.name}** for: **{reason}**")
            except:
                # If DM fails, just continue
                pass
                
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban that member.", ephemeral=True)
        except Exception as e:
            # Handle errors even if error_handler is not available
            if self.error_handler:
                await self.error_handler.handle_command_error(interaction, e, "ban")
            else:
                # Basic error handling if no error_handler is available
                await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
    #=============================================================================================================================================================