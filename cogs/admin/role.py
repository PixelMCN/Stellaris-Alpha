import nextcord
from nextcord import Interaction
from nextcord.ext import commands

class Role(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="role", description="Manage roles")
    async def role(self, interaction: Interaction):
        pass

    @role.subcommand(name="add", description="Add a role to a user or all users")
    async def add_role(self, interaction: Interaction, role: nextcord.Role, user: nextcord.Member = nextcord.SlashOption(required=False)):
        if user:
            await user.add_roles(role)
            embed = nextcord.Embed(title="Role Added", color=nextcord.Color.green())
            embed.add_field(name="User", value=user.mention, inline=True)
            embed.add_field(name="Role", value=role.mention, inline=True)
            await interaction.response.send_message(embed=embed)
        else:
            for member in interaction.guild.members:
                await member.add_roles(role)
            embed = nextcord.Embed(title="Role Added to All Users", color=nextcord.Color.green())
            embed.add_field(name="Role", value=role.mention, inline=True)
            await interaction.response.send_message(embed=embed)

    @role.subcommand(name="remove", description="Remove a role from a user or all users")
    async def remove_role(self, interaction: Interaction, role: nextcord.Role, user: nextcord.Member = nextcord.SlashOption(required=False)):
        if user:
            await user.remove_roles(role)
            embed = nextcord.Embed(title="Role Removed", color=nextcord.Color.red())
            embed.add_field(name="User", value=user.mention, inline=True)
            embed.add_field(name="Role", value=role.mention, inline=True)
            await interaction.response.send_message(embed=embed)
        else:
            for member in interaction.guild.members:
                await member.remove_roles(role)
            embed = nextcord.Embed(title="Role Removed from All Users", color=nextcord.Color.red())
            embed.add_field(name="Role", value=role.mention, inline=True)
            await interaction.response.send_message(embed=embed)
        

    @role.subcommand(name="list", description="List all roles in the server")
    async def list_roles(self, interaction: Interaction):
        roles = interaction.guild.roles
        embed = nextcord.Embed(title="Roles in the Server", color=nextcord.Color.blue())
        for role in roles:
            embed.add_field(name=role.name, value=role.id, inline=False)
        await interaction.response.send_message(embed=embed)
