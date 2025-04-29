import nextcord
from nextcord.ext import commands


class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = bot.error_handler
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="mute", description="Mute one or all members in a voice channel")
    async def mute(self, interaction: nextcord.Interaction, member: nextcord.Member = nextcord.SlashOption(required=False)):
        try:
            if not interaction.user.guild_permissions.mute_members:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return
                
            if member:
                # Check if member is in a voice channel
                if not member.voice:
                    await interaction.response.send_message("This user is not in a voice channel.", ephemeral=True)
                    return
                    
                await member.edit(mute=True)
                await interaction.response.send_message(f"{member.mention} has been muted.")
            else:
                if not interaction.user.voice:
                    await interaction.response.send_message("You need to be in a voice channel to mute all members.", ephemeral=True)
                    return
                    
                for member in interaction.user.voice.channel.members:
                    await member.edit(mute=True)
                await interaction.response.send_message("All members in the voice channel have been muted.")
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to mute members.", ephemeral=True)
        except Exception as e:
            # Let the global error handler handle other exceptions
            await self.error_handler.handle_command_error(interaction, e, "mute")
    #=============================================================================================================================================================
            