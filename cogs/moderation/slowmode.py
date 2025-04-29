import nextcord
from nextcord.ext import commands


class Slowmode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = bot.error_handler

    # SLOWMODE COMMANDS with seconds & hours
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="slowmode", description="Set the slowmode for a channel.")
    async def slowmode(self, interaction: nextcord.Interaction, seconds: int = None, hours: int = None):
        try:
            if seconds is None and hours is None:
                await interaction.response.send_message("Please specify either seconds or hours for slowmode.", ephemeral=True)
                return

            if seconds is not None and hours is not None:
                await interaction.response.send_message("Please specify either seconds or hours, not both.", ephemeral=True)
                return

            if hours is not None:
                seconds = hours * 3600

            await interaction.channel.edit(slowmode_delay=seconds)
            await interaction.response.send_message(f"Slowmode set to {seconds} seconds.", ephemeral=True)
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to edit channel settings.", ephemeral=True)
        except Exception as e:
            # Let the global error handler handle other exceptions
            await self.error_handler.handle_command_error(interaction, e, "slowmode")
    #=============================================================================================================================================================