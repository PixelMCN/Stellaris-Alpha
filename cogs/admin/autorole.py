import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import json
import os

# Using a JSON file to store role IDs.
# Only for demonstration & development purposes, not for production use.
# The production version will use MongoDB for persistent storage. 
ROLE_FILE = os.path.join("data", "roles.json")

def load_roles():
    if os.path.exists(ROLE_FILE):
        with open(ROLE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_roles(data):
    with open(ROLE_FILE, "w") as f:
        json.dump(data, f)

autorole_settings = load_roles()

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command group
    @nextcord.slash_command(name="autorole", description="Manage autorole settings for the server")
    async def autorole(self, interaction: Interaction):
        pass
    
    # AUTO ROLE SET COMMANDS
    #=============================================================================================================================================================
    # Slash command implementation
    @autorole.subcommand(name="set", description="Set the autorole for the server")
    async def autorole_set_slash(self, interaction: Interaction, role: nextcord.Role):
        # Permission check
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You need the Manage Roles permission to use this command.", ephemeral=True)
            return

        # Role hierarchy check
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I can't assign a role higher than or equal to my highest role.", ephemeral=True)
            return

        # Save autorole setting
        autorole_settings[str(interaction.guild.id)] = role.id
        save_roles(autorole_settings)
        
        embed = nextcord.Embed(
            title="Autorole Set",
            description=f"New members will now automatically receive the {role.mention} role.",
            color=nextcord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
    # AUTO ROLE REMOVE COMMANDS
    #=============================================================================================================================================================
    # Slash command implementation
    @autorole.subcommand(name="remove", description="Remove the autorole for the server")
    async def autorole_remove_slash(self, interaction: Interaction):
        # Permission check
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You need the Manage Roles permission to use this command.", ephemeral=True)
            return

        guild_id = str(interaction.guild.id)
        if guild_id in autorole_settings:
            del autorole_settings[guild_id]
            save_roles(autorole_settings)
            embed = nextcord.Embed(
                title="Autorole Removed",
                description="New members will no longer receive an automatic role.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("No autorole is currently set for this server.", ephemeral=True)
    # AUTO ROLE VIEW COMMANDS
    #=============================================================================================================================================================
    # Slash command implementation
    @autorole.subcommand(name="view", description="View the current autorole for the server")
    async def autorole_view_slash(self, interaction: Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id in autorole_settings:
            role_id = autorole_settings[guild_id]
            role = interaction.guild.get_role(role_id)
            
            if role:
                embed = nextcord.Embed(
                    title="Current Autorole",
                    description=f"New members will receive the {role.mention} role.",
                    color=nextcord.Color.blue()
                )
            else:
                embed = nextcord.Embed(
                    title="Autorole Error",
                    description="The configured role no longer exists. Please set a new autorole.",
                    color=nextcord.Color.orange()
                )
                # Clean up the invalid role
                del autorole_settings[guild_id]
                save_roles(autorole_settings)
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("No autorole is currently set for this server.", ephemeral=True)
    # AUTO ROLE ON JOIN 
    #=============================================================================================================================================================
    @commands.Cog.listener()
    async def on_member_join(self, member):
        role_id = autorole_settings.get(str(member.guild.id))
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Autorole on join")
                except nextcord.Forbidden:
                    # Optionally log or notify about missing permissions
                    pass
    #=============================================================================================================================================================

