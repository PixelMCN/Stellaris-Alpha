import nextcord
from nextcord.ext import commands


class LockUnlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # LOCK CHANNEL COMMAND
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="lock", description="Lock a channel")
    async def lock(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.respond("You don't have permission to manage channels.", ephemeral=True)
            return

        await channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message(f"Channel {channel.mention} has been locked.")
    # UNLOCK CHANNEL COMMAND
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="unlock", description="Unlock a channel")
    async def unlock(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.respond("You don't have permission to manage channels.", ephemeral=True)
            return

        await channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message(f"Channel {channel.mention} has been unlocked.")
    #=============================================================================================================================================================