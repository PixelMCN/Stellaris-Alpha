import nextcord
from nextcord.ext import commands

class RoleInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ROLEINFO COMMANDS
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="roleinfo", description="Get information about a role.")
    async def roleinfo(self, interaction: nextcord.Interaction, role: nextcord.Role):
        embed = nextcord.Embed(title=f"Role Information for {role.name}", color=nextcord.Color.blue())
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.add_field(name="Color", value=role.color, inline=True)
        embed.add_field(name="Hoisted", value=role.hoist, inline=True)
        embed.add_field(name="Mentionable", value=role.mentionable, inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.add_field(name="Created At", value=role.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_thumbnail(url=role.icon.url)
        await interaction.response.send_message(embed=embed)
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Prefix command implementation
    @commands.command(name="roleinfo", description="Get information about a role.")
    async def roleinfo_prefix(self, ctx, role: nextcord.Role):
        embed = nextcord.Embed(title=f"Role Information for {role.name}", color=nextcord.Color.blue())
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.add_field(name="Color", value=role.color, inline=True)
        embed.add_field(name="Hoisted", value=role.hoist, inline=True)
        embed.add_field(name="Mentionable", value=role.mentionable, inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.add_field(name="Created At", value=role.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_thumbnail(url=role.icon.url)
        await ctx.send(embed=embed)
    #=============================================================================================================================================================