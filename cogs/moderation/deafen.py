import nextcord
from nextcord.ext import commands


class Deafen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # DEAFEN COMMANDS
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="deafen", description="Deafen one or all members in a voice channel")
    async def deafened(self, interaction: nextcord.Interaction, member: nextcord.Member = nextcord.SlashOption(required=False)):
        if interaction.user.guild_permissions.deafen_members:
            if member:
                await member.edit(deafen=True)
                await interaction.response.send_message(f"{member.mention} has been deafened.")
            else:
                for member in interaction.user.voice.channel.members:
                    await member.edit(deafen=True)
                await interaction.response.send_message("All members in the voice channel have been deafened.")
        else:
            await interaction.response.send_message("You do not have permission to use this command.") 
    #=============================================================================================================================================================

