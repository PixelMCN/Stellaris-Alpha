import nextcord
from nextcord.ext import commands

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # USERINFO COMMANDS
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="userinfo", description="Get information about a user.")
    async def userinfo(self, interaction: nextcord.Interaction, member: nextcord.Member = nextcord.SlashOption(required=False)):
        await interaction.response.defer()
        if member is None:
            member = interaction.user
        embed = nextcord.Embed(title=f"User Information for {member.name}", color=nextcord.Color.blue())
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Nickname", value=member.display_name, inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Joined Discord", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_thumbnail(url=member.avatar.url)
        await interaction.followup.send(embed=embed)
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Prefix command implementation
    @commands.command(name="userinfo", description="Get information about a user.")
    async def userinfo_prefix(self, ctx, member: nextcord.Member = None):
        if member is None:
            member = ctx.author
        embed = nextcord.Embed(title=f"User Information for {member.name}", color=nextcord.Color.blue())
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Nickname", value=member.display_name, inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Joined Discord", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)
    #=============================================================================================================================================================