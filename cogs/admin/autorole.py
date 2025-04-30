import nextcord
from nextcord.ext import commands
from nextcord import Interaction, ui
import json
import os
from typing import Optional, List

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
    os.makedirs(os.path.dirname(ROLE_FILE), exist_ok=True)
    with open(ROLE_FILE, "w") as f:
        json.dump(data, f)

autorole_settings = load_roles()

# AUTOROLE SETUP WIZARD
#=============================================================================================================================================================
class RoleSelectView(ui.View):
    def __init__(self, roles: List[nextcord.Role], timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.selected_role = None
        
        # Create a select menu with roles
        self.role_select = ui.Select(
            placeholder="Choose a role to automatically assign to new members...",
            min_values=1,
            max_values=1,
            options=[
                nextcord.SelectOption(
                    label=role.name[:25],  # Discord limits option labels to 25 chars
                    value=str(role.id),
                    description=f"Assign {role.name} to new members",
                    emoji="🏷️"
                ) for role in roles[:25]  # Discord limits to 25 options
            ]
        )
        
        self.role_select.callback = self.role_selected
        self.add_item(self.role_select)
        
    async def role_selected(self, interaction: Interaction):
        self.selected_role = interaction.guild.get_role(int(self.role_select.values[0]))
        self.stop()
        
class ConfirmView(ui.View):
    def __init__(self, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.value = None
        
    @ui.button(label="Confirm", style=nextcord.ButtonStyle.green, emoji="✅")
    async def confirm(self, button: ui.Button, interaction: Interaction):
        self.value = True
        self.stop()
        
    @ui.button(label="Cancel", style=nextcord.ButtonStyle.grey, emoji="❌")
    async def cancel(self, button: ui.Button, interaction: Interaction):
        self.value = False
        self.stop()

class AutoRoleManagementView(ui.View):
    def __init__(self, bot, current_role: Optional[nextcord.Role] = None, timeout: float = 300.0):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.current_role = current_role
        
    @ui.button(label="Set Auto Role", style=nextcord.ButtonStyle.primary, emoji="⚙️", row=0)
    async def set_autorole(self, button: ui.Button, interaction: Interaction):
        # Check permissions
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message(
                "You need the **Manage Roles** permission to configure automatic role assignments.",
                ephemeral=True
            )
            
        # Get assignable roles (roles below the bot's highest role)
        assignable_roles = [
            role for role in interaction.guild.roles 
            if role < interaction.guild.me.top_role and not role.is_default()
        ]
        
        if not assignable_roles:
            return await interaction.response.send_message(
                "There are no roles I can assign. Please create a role below my highest role.",
                ephemeral=True
            )
            
        # Show role selection menu
        view = RoleSelectView(assignable_roles)
        await interaction.response.send_message(
            "Please select a role to automatically assign to new members:",
            view=view,
            ephemeral=True
        )
        
        # Wait for role selection
        timed_out = await view.wait()
        if timed_out or not view.selected_role:
            return await interaction.edit_original_message(
                content="Role selection timed out or was cancelled.",
                view=None
            )
            
        selected_role = view.selected_role
        
        # Confirm the selection
        confirm_embed = nextcord.Embed(
            title="Confirm Auto Role Setup",
            description=f"New members will automatically receive the {selected_role.mention} role when they join the server.",
            color=nextcord.Color.blue()
        )
        confirm_view = ConfirmView()
        
        await interaction.edit_original_message(
            content=None,
            embed=confirm_embed,
            view=confirm_view
        )
        
        # Wait for confirmation
        timed_out = await confirm_view.wait()
        if timed_out or not confirm_view.value:
            return await interaction.edit_original_message(
                content="Auto role setup was cancelled.",
                embed=None,
                view=None
            )
            
        # Save the role setting
        autorole_settings[str(interaction.guild.id)] = selected_role.id
        save_roles(autorole_settings)
        
        success_embed = nextcord.Embed(
            title="✅ Automatic Role Setup Complete",
            description=f"New members will now automatically receive the {selected_role.mention} role when they join.",
            color=nextcord.Color.green()
        )
        
        await interaction.edit_original_message(
            content=None,
            embed=success_embed,
            view=None
        )
        
    @ui.button(label="Remove Auto Role", style=nextcord.ButtonStyle.danger, emoji="🚫", row=0)
    async def remove_autorole(self, button: ui.Button, interaction: Interaction):
        # Check permissions
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message(
                "You need the **Manage Roles** permission to configure automatic role assignments.",
                ephemeral=True
            )
            
        guild_id = str(interaction.guild.id)
        if guild_id not in autorole_settings:
            return await interaction.response.send_message(
                "There's no automatic role currently configured for this server.",
                ephemeral=True
            )
            
        # Get the current role for reference
        role_id = autorole_settings[guild_id]
        role = interaction.guild.get_role(role_id)
        role_mention = role.mention if role else "the previously set role"
        
        # Confirm removal
        confirm_embed = nextcord.Embed(
            title="Confirm Auto Role Removal",
            description=f"Are you sure you want to stop automatically assigning {role_mention} to new members?",
            color=nextcord.Color.orange()
        )
        confirm_view = ConfirmView()
        
        await interaction.response.send_message(
            embed=confirm_embed,
            view=confirm_view,
            ephemeral=True
        )
        
        # Wait for confirmation
        timed_out = await confirm_view.wait()
        if timed_out or not confirm_view.value:
            return await interaction.edit_original_message(
                content="Auto role removal was cancelled.",
                embed=None,
                view=None
            )
            
        # Remove the autorole setting
        del autorole_settings[guild_id]
        save_roles(autorole_settings)
        
        success_embed = nextcord.Embed(
            title="🚫 Automatic Role Disabled",
            description=f"New members will no longer receive {role_mention} when they join.",
            color=nextcord.Color.red()
        )
        
        await interaction.edit_original_message(
            content=None,
            embed=success_embed,
            view=None
        )
        
    @ui.button(label="View Current Setting", style=nextcord.ButtonStyle.secondary, emoji="🔍", row=1)
    async def view_autorole(self, button: ui.Button, interaction: Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id in autorole_settings:
            role_id = autorole_settings[guild_id]
            role = interaction.guild.get_role(role_id)
            
            if role:
                embed = nextcord.Embed(
                    title="🔍 Current Automatic Role",
                    description=f"New members who join this server will automatically receive the {role.mention} role.",
                    color=nextcord.Color.blue()
                )
            else:
                embed = nextcord.Embed(
                    title="⚠️ Configured Role Not Found",
                    description="The previously configured role no longer exists in this server. Please set a new automatic role.",
                    color=nextcord.Color.orange()
                )
                
                # Clean up the invalid role
                del autorole_settings[guild_id]
                save_roles(autorole_settings)
        else:
            embed = nextcord.Embed(
                title="ℹ️ No Automatic Role Configured",
                description="There's currently no automatic role set up for new members in this server.",
                color=nextcord.Color.blue()
            )
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # AUTOROLE MAIN COMMAND
    #=============================================================================================================================================================
    @nextcord.slash_command(
        name="autorole", 
        description="Manage automatic role assignments for new members",
        default_member_permissions=nextcord.Permissions(manage_roles=True)
    )
    async def autorole(self, interaction: Interaction):
        """Interactive menu to manage automatic role assignments for new members"""
        # Check if user has manage roles permission
        if not interaction.user.guild_permissions.manage_roles:
            embed = nextcord.Embed(
                title="⚠️ Permission Required",
                description="You need the **Manage Roles** permission to configure automatic role assignments.",
                color=nextcord.Color.yellow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Check if bot has manage roles permission
        if not interaction.guild.me.guild_permissions.manage_roles:
            embed = nextcord.Embed(
                title="⚠️ Bot Permission Required",
                description="I need the **Manage Roles** permission to assign roles to new members.",
                color=nextcord.Color.yellow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        # Get current autorole if set
        guild_id = str(interaction.guild.id)
        current_role = None
        if guild_id in autorole_settings:
            role_id = autorole_settings[guild_id]
            current_role = interaction.guild.get_role(role_id)
        
        # Create welcome embed
        embed = nextcord.Embed(
            title="🤖 Auto Role Management",
            description="Configure automatic role assignments for new members who join your server.",
            color=nextcord.Color.blue()
        )
        
        if current_role:
            embed.add_field(
                name="Current Setting",
                value=f"New members currently receive the {current_role.mention} role automatically.",
                inline=False
            )
        else:
            embed.add_field(
                name="Current Setting",
                value="No automatic role is currently configured.",
                inline=False
            )
            
        embed.add_field(
            name="How It Works",
            value="When enabled, I'll automatically assign the selected role to new members when they join.",
            inline=False
        )
        
        # Create and send the management view
        view = AutoRoleManagementView(self.bot, current_role)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    # AUTO ROLE ON JOIN 
    #=============================================================================================================================================================
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        role_id = autorole_settings.get(guild_id)
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Automatic role assignment for new member")
                except nextcord.Forbidden:
                    # Attempt to notify server admins about the permission issue
                    try:
                        # Try to find a system channel or default channel to notify about the issue
                        channel = member.guild.system_channel
                        if channel and channel.permissions_for(member.guild.me).send_messages:
                            error_embed = nextcord.Embed(
                                title="⚠️ Automatic Role Assignment Failed",
                                description=f"I couldn't assign the configured role to {member.mention} because I don't have sufficient permissions. Please check my role permissions and position in the role hierarchy.",
                                color=nextcord.Color.red()
                            )
                            await channel.send(embed=error_embed)
                    except:
                        # If we can't send a notification, silently fail
                        pass
    #=============================================================================================================================================================