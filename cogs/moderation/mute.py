import nextcord
from nextcord.ext import commands


class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="mute", description="Mute one or all members in a voice channel")
    async def mute(self, interaction: nextcord.Interaction, member: nextcord.Member = nextcord.SlashOption(required=False)):
        if interaction.user.guild_permissions.mute_members:
            if member:
                await member.edit(mute=True)
                await interaction.response.send_message(f"{member.mention} has been muted.")
            else:
                for member in interaction.user.voice.channel.members:
                    await member.edit(mute=True)
                await interaction.response.send_message("All members in the voice channel have been muted.")
        else:
            await interaction.response.send_message("You do not have permission to use this command.")
    #-------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Prefix command implementation
    @commands.command(name="mute", description="Mute one or all members in a voice channel")
    async def mute_prefix(self, ctx, member: nextcord.Member = None):
        if ctx.author.guild_permissions.mute_members:
            if member:
                await member.edit(mute=True)
                await ctx.send(f"{member.mention} has been muted.")
            else:
                for member in ctx.author.voice.channel.members:
                    await member.edit(mute=True)
                await ctx.send("All members in the voice channel have been muted.")
        else:
            await ctx.send("You do not have permission to use this command.")
    #=============================================================================================================================================================
            