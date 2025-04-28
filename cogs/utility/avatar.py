import nextcord
from nextcord.ext import commands
from nextcord import Interaction


class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # AVATAR COMMANDS
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="avatar", description="Get the avatar of a user")
    async def avatar(self, interaction: Interaction, member: nextcord.Member = nextcord.SlashOption(required=False)):
        await interaction.response.defer()
        if member is None:
            member = interaction.user
        avatar_url = member.avatar.url
        embed = nextcord.Embed(title=f"{member.name}'s Avatar", color=nextcord.Color.blue())
        embed.set_image(url=avatar_url)
        await interaction.followup.send(embed=embed)
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Prefix command implementation
    @commands.command(name="avatar", aliases=["av"])
    async def avatar_prefix(self, ctx, member: nextcord.Member = None):
        if member is None:
            member = ctx.author
        avatar_url = member.avatar.url
        embed = nextcord.Embed(title=f"{member.name}'s Avatar", color=nextcord.Color.blue())
        embed.set_image(url=avatar_url)
        await ctx.send(embed=embed)
    #=============================================================================================================================================================
        