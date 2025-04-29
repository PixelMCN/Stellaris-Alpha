import nextcord
from nextcord.ext import commands


class LockUnlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = bot.error_handler

    # LOCK CHANNEL COMMAND
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="lock", description="Lock a channel")
    async def lock(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        try:
            if not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message("You don't have permission to manage channels.", ephemeral=True)
                return

            await channel.set_permissions(interaction.guild.default_role, send_messages=False)
            await interaction.response.send_message(f"Channel {channel.mention} has been locked.")
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to manage channel permissions.", ephemeral=True)
        except Exception as e:
            # Let the global error handler handle other exceptions
            await self.error_handler.handle_command_error(interaction, e, "lock")
    # UNLOCK CHANNEL COMMAND
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="unlock", description="Unlock a channel")
    async def unlock(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        try:
            if not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message("You don't have permission to manage channels.", ephemeral=True)
                return

            await channel.set_permissions(interaction.guild.default_role, send_messages=True)
            await interaction.response.send_message(f"Channel {channel.mention} has been unlocked.")
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to manage channel permissions.", ephemeral=True)
        except Exception as e:
            # Let the global error handler handle other exceptions
            await self.error_handler.handle_command_error(interaction, e, "unlock")
    #=============================================================================================================================================================