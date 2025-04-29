import nextcord
from nextcord.ext import commands


class Deafen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = bot.error_handler

    # DEAFEN COMMANDS
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="deafen", description="Deafen one or all members in a voice channel")
    async def deafened(self, interaction: nextcord.Interaction, member: nextcord.Member = nextcord.SlashOption(required=False)):
        try:
            if not interaction.user.guild_permissions.deafen_members:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return
                
            if member:
                # Check if member is in a voice channel
                if not member.voice:
                    await interaction.response.send_message("This user is not in a voice channel.", ephemeral=True)
                    return
                    
                await member.edit(deafen=True)
                await interaction.response.send_message(f"{member.mention} has been deafened.")
            else:
                if not interaction.user.voice:
                    await interaction.response.send_message("You need to be in a voice channel to deafen all members.", ephemeral=True)
                    return
                    
                for member in interaction.user.voice.channel.members:
                    await member.edit(deafen=True)
                await interaction.response.send_message("All members in the voice channel have been deafened.")
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to deafen members.", ephemeral=True)
        except Exception as e:
            # Let the global error handler handle other exceptions
            await self.error_handler.handle_command_error(interaction, e, "deafen")
    #=============================================================================================================================================================

