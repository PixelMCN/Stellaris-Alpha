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
        embed.add_field(name="Owner", value=str(guild.owner), inline=True)  # Convert owner to string
        embed.add_field(name="Member Count", value=guild.member_count, inline=True)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await interaction.followup.send(embed=embed)
    #=============================================================================================================================================================
