import nextcord
import random
from nextcord.ext import commands
from nextcord import Interaction


class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = bot.error_handler

    # List of kick reasons
    kick_reasons = [
        "Breaking server rules",
        "Disruptive behavior",
        "Repeated violations",
        "Spamming"
    ]
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="kick", description="Kick a member from the server")
    async def kick_slash(self, interaction: Interaction, member: nextcord.Member, reason: str = None):
        try:
            if not interaction.user.guild_permissions.kick_members:
                await interaction.response.send_message("This command requires `kick permission`", ephemeral=True)
                return

            if reason is None:
                reason = random.choice(self.kick_reasons)

            await member.kick(reason=reason)
            await interaction.response.send_message(f'{member.mention} has been kicked for: {reason}')

            # Send a direct message to the kicked member
            try:
                await member.send(f"You have been kicked 🦶 from **{interaction.guild.name}** for the **{reason}**")
            except nextcord.HTTPException:
                pass  # Silently fail if DM can't be sent
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to kick that member.", ephemeral=True)
        except Exception as e:
            # Let the global error handler handle other exceptions
            await self.error_handler.handle_command_error(interaction, e, "kick")
    #=============================================================================================================================================================


