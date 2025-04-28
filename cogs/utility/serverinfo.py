import nextcord
from nextcord.ext import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # SERVERINFO COMMANDS
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="serverinfo", description="Get information about the server.")
    async def serverinfo(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        guild = interaction.guild
        embed = nextcord.Embed(title=f"Server Information for {guild.name}", color=nextcord.Color.blue())
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner, inline=True)
        embed.add_field(name="Region", value=guild.region, inline=True)
        embed.add_field(name="Member Count", value=guild.member_count, inline=True)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_thumbnail(url=guild.icon.url)
        await interaction.followup.send(embed=embed)
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Prefix command implementation
    @commands.command(name="serverinfo", description="Get information about the server.")
    async def serverinfo_prefix(self, ctx):
        guild = ctx.guild
        embed = nextcord.Embed(title=f"Server Information for {guild.name}", color=nextcord.Color.blue())
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner, inline=True)
        embed.add_field(name="Region", value=guild.region, inline=True)
        embed.add_field(name="Member Count", value=guild.member_count, inline=True)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)
    #=============================================================================================================================================================