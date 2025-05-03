import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
import json
import os
import time
from typing import List, Dict, Optional, Union
import asyncio
import logging

from utils.embed_helper import EmbedHelper
from utils.error_handler import ErrorHandler
from utils.time_helper import TimeHelper

# File to store autorole configuration
AUTOROLE_CONFIG_FILE = "./data/autorole.json"

# Set up logging
logger = logging.getLogger('autorole')

class AutoroleView(nextcord.ui.View):
    """Interactive confirmation view for autorole actions"""
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
        self.value = None
    
    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: Interaction):
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red)
    async def cancel(self, button: nextcord.ui.Button, interaction: Interaction):
        self.value = False
        self.stop()
        await interaction.response.defer()

class Autorole(commands.Cog):
    """Cog for automatically assigning roles to new members and bots"""
    def __init__(self, bot):
        self.bot = bot
        self.autorole_config = {}
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(AUTOROLE_CONFIG_FILE), exist_ok=True)
        
        self.load_config()
    
    def load_config(self):
        """Load autorole configuration from file"""
        try:
            if os.path.exists(AUTOROLE_CONFIG_FILE):
                with open(AUTOROLE_CONFIG_FILE, 'r') as f:
                    self.autorole_config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading autorole config: {e}")
            self.autorole_config = {}
    
    def save_config(self):
        """Save autorole configuration to file"""
        try:
            with open(AUTOROLE_CONFIG_FILE, 'w') as f:
                json.dump(self.autorole_config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving autorole config: {e}")
    
    def _check_permissions(self, interaction: Interaction) -> bool:
        """Check if the user has the required permissions"""
        if not interaction.user.guild_permissions.manage_roles:
            return False
        return True
    
    def _format_delay_text(self, delay_seconds: Optional[int]) -> str:
        """Format delay text for display"""
        if not delay_seconds:
            return ""
        
        return f" with a {TimeHelper.format_time_remaining(time.time() + delay_seconds)} delay"
    
    def _initialize_guild_config(self, guild_id: str):
        """Initialize guild configuration if it doesn't exist"""
        if guild_id not in self.autorole_config:
            self.autorole_config[guild_id] = {
                "member_roles": [],
                "bot_roles": []
            }
    
    @nextcord.slash_command(
        name="autorole", 
        description="Configure automatic role assignment for new members and bots"
    )
    async def autorole(self, interaction: Interaction):
        """Base command for autorole configuration"""
        pass
    
    @autorole.subcommand(
        name="add-member",
        description="Add a role to be automatically assigned to new human members"
    )
    async def autorole_add_member(
        self, 
        interaction: Interaction, 
        role: nextcord.Role = SlashOption(
            description="Role to automatically assign to new human members",
            required=True
        ),
        delay: str = SlashOption(
            description="Optional delay before assigning role (e.g. 10s, 5m, 1h, 2d)",
            required=False,
            default=None
        )
    ):
        """Add a role to be automatically assigned to new human members"""
        # Check if user has manage roles permission
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return
        
        # Check if bot has permission to manage this role
        if role.position >= interaction.guild.me.top_role.position:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Cannot Configure Role",
                    f"I cannot assign {role.mention} because it's positioned higher than or equal to my highest role. Please move my role above it in the server settings."
                ),
                ephemeral=True
            )
            return
        
        # Parse delay if provided
        delay_seconds = None
        if delay:
            try:
                delay_seconds = TimeHelper.parse_time(delay)
                if delay_seconds is None or delay_seconds < 0:
                    raise ValueError("Invalid time format")
            except Exception:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Invalid Delay Format",
                        "Please use a valid format like `10s`, `5m`, `1h`, or `2d`."
                    ),
                    ephemeral=True
                )
                return
        
        # Initialize guild config if it doesn't exist
        guild_id = str(interaction.guild.id)
        self._initialize_guild_config(guild_id)
        
        # Check if role is already in member autorole config
        for role_config in self.autorole_config[guild_id]["member_roles"]:
            if role_config["id"] == role.id:
                # Update existing role config
                role_config["delay"] = delay_seconds
                self.save_config()
                
                delay_text = self._format_delay_text(delay_seconds)
                await interaction.response.send_message(
                    embed=EmbedHelper.success_embed(
                        "Member Autorole Updated",
                        f"The role {role.mention} will be automatically assigned to new human members{delay_text}."
                    )
                )
                return
        
        # Add new role to config
        self.autorole_config[guild_id]["member_roles"].append({
            "id": role.id,
            "delay": delay_seconds
        })
        self.save_config()
        
        # Send success message
        delay_text = self._format_delay_text(delay_seconds)
        await interaction.response.send_message(
            embed=EmbedHelper.success_embed(
                "Member Autorole Added",
                f"The role {role.mention} will be automatically assigned to new human members{delay_text}."
            )
        )
    
    @autorole.subcommand(
        name="add-bot",
        description="Add a role to be automatically assigned to new bots"
    )
    async def autorole_add_bot(
        self, 
        interaction: Interaction, 
        role: nextcord.Role = SlashOption(
            description="Role to automatically assign to new bots",
            required=True
        ),
        delay: str = SlashOption(
            description="Optional delay before assigning role (e.g. 10s, 5m, 1h, 2d)",
            required=False,
            default=None
        )
    ):
        """Add a role to be automatically assigned to new bots"""
        # Check if user has manage roles permission
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return
        
        # Check if bot has permission to manage this role
        if role.position >= interaction.guild.me.top_role.position:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Cannot Configure Role",
                    f"I cannot assign {role.mention} because it's positioned higher than or equal to my highest role. Please move my role above it in the server settings."
                ),
                ephemeral=True
            )
            return
        
        # Parse delay if provided
        delay_seconds = None
        if delay:
            try:
                delay_seconds = TimeHelper.parse_time(delay)
                if delay_seconds is None or delay_seconds < 0:
                    raise ValueError("Invalid time format")
            except Exception:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Invalid Delay Format",
                        "Please use a valid format like `10s`, `5m`, `1h`, or `2d`."
                    ),
                    ephemeral=True
                )
                return
        
        # Initialize guild config if it doesn't exist
        guild_id = str(interaction.guild.id)
        self._initialize_guild_config(guild_id)
        
        # Check if role is already in bot autorole config
        for role_config in self.autorole_config[guild_id]["bot_roles"]:
            if role_config["id"] == role.id:
                # Update existing role config
                role_config["delay"] = delay_seconds
                self.save_config()
                
                delay_text = self._format_delay_text(delay_seconds)
                await interaction.response.send_message(
                    embed=EmbedHelper.success_embed(
                        "Bot Autorole Updated",
                        f"The role {role.mention} will be automatically assigned to new bots{delay_text}."
                    )
                )
                return
        
        # Add new role to config
        self.autorole_config[guild_id]["bot_roles"].append({
            "id": role.id,
            "delay": delay_seconds
        })
        self.save_config()
        
        # Send success message
        delay_text = self._format_delay_text(delay_seconds)
        await interaction.response.send_message(
            embed=EmbedHelper.success_embed(
                "Bot Autorole Added",
                f"The role {role.mention} will be automatically assigned to new bots{delay_text}."
            )
        )
    
    @autorole.subcommand(
        name="remove-member",
        description="Remove a role from automatic assignment for human members"
    )
    async def autorole_remove_member(
        self, 
        interaction: Interaction, 
        role: nextcord.Role = SlashOption(
            description="Role to remove from automatic assignment for human members",
            required=True
        )
    ):
        """Remove a role from automatic assignment for human members"""
        # Check if user has manage roles permission
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return
        
        # Check if guild has any member autoroles configured
        guild_id = str(interaction.guild.id)
        if (guild_id not in self.autorole_config or 
            "member_roles" not in self.autorole_config[guild_id] or 
            not self.autorole_config[guild_id]["member_roles"]):
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "No Member Autoroles Configured",
                    "There are no autoroles configured for human members in this server."
                ),
                ephemeral=True
            )
            return
        
        # Check if role is in member autorole config
        role_found = False
        for i, role_config in enumerate(self.autorole_config[guild_id]["member_roles"]):
            if role_config["id"] == role.id:
                # Remove role from config
                self.autorole_config[guild_id]["member_roles"].pop(i)
                role_found = True
                break
        
        if not role_found:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Role Not Found",
                    f"The role {role.mention} is not configured for automatic assignment to human members."
                ),
                ephemeral=True
            )
            return
        
        # Save config and send success message
        self.save_config()
        await interaction.response.send_message(
            embed=EmbedHelper.success_embed(
                "Member Autorole Removed",
                f"The role {role.mention} will no longer be automatically assigned to new human members."
            )
        )
    
    @autorole.subcommand(
        name="remove-bot",
        description="Remove a role from automatic assignment for bots"
    )
    async def autorole_remove_bot(
        self, 
        interaction: Interaction, 
        role: nextcord.Role = SlashOption(
            description="Role to remove from automatic assignment for bots",
            required=True
        )
    ):
        """Remove a role from automatic assignment for bots"""
        # Check if user has manage roles permission
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return
        
        # Check if guild has any bot autoroles configured
        guild_id = str(interaction.guild.id)
        if (guild_id not in self.autorole_config or 
            "bot_roles" not in self.autorole_config[guild_id] or 
            not self.autorole_config[guild_id]["bot_roles"]):
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "No Bot Autoroles Configured",
                    "There are no autoroles configured for bots in this server."
                ),
                ephemeral=True
            )
            return
        
        # Check if role is in bot autorole config
        role_found = False
        for i, role_config in enumerate(self.autorole_config[guild_id]["bot_roles"]):
            if role_config["id"] == role.id:
                # Remove role from config
                self.autorole_config[guild_id]["bot_roles"].pop(i)
                role_found = True
                break
        
        if not role_found:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Role Not Found",
                    f"The role {role.mention} is not configured for automatic assignment to bots."
                ),
                ephemeral=True
            )
            return
        
        # Save config and send success message
        self.save_config()
        await interaction.response.send_message(
            embed=EmbedHelper.success_embed(
                "Bot Autorole Removed",
                f"The role {role.mention} will no longer be automatically assigned to new bots."
            )
        )
    
    @autorole.subcommand(
        name="list",
        description="List all roles configured for automatic assignment"
    )
    async def autorole_list(self, interaction: Interaction):
        """List all roles configured for automatic assignment"""
        # Check if guild has any autoroles configured
        guild_id = str(interaction.guild.id)
        if (guild_id not in self.autorole_config or 
            (not self.autorole_config[guild_id].get("member_roles", []) and 
             not self.autorole_config[guild_id].get("bot_roles", []))):
            await interaction.response.send_message(
                embed=EmbedHelper.info_embed(
                    "No Autoroles Configured",
                    "There are no autoroles configured for this server."
                )
            )
            return
        
        # Create embed with list of autoroles
        embed = nextcord.Embed(
            title="Autorole Configuration",
            description="Current automatic role assignment configuration:",
            color=0x3498db
        )
        
        # Add member roles to the embed
        removed_roles = {"member_roles": [], "bot_roles": []}
        
        if "member_roles" in self.autorole_config[guild_id] and self.autorole_config[guild_id]["member_roles"]:
            embed.add_field(
                name="Human Member Roles",
                value="The following roles will be assigned to new human members:",
                inline=False
            )
            
            for i, role_config in enumerate(self.autorole_config[guild_id]["member_roles"]):
                role_id = role_config["id"]
                role = interaction.guild.get_role(role_id)
                
                if role:
                    delay = role_config.get("delay")
                    delay_text = self._format_delay_text(delay)
                    
                    embed.add_field(
                        name=f"Member Role #{i+1}",
                        value=f"{role.mention}{delay_text}",
                        inline=True
                    )
                else:
                    # Mark role for removal as it no longer exists
                    removed_roles["member_roles"].append(i)
        
        # Add bot roles to the embed
        if "bot_roles" in self.autorole_config[guild_id] and self.autorole_config[guild_id]["bot_roles"]:
            embed.add_field(
                name="Bot Roles",
                value="The following roles will be assigned to new bots:",
                inline=False
            )
            
            for i, role_config in enumerate(self.autorole_config[guild_id]["bot_roles"]):
                role_id = role_config["id"]
                role = interaction.guild.get_role(role_id)
                
                if role:
                    delay = role_config.get("delay")
                    delay_text = self._format_delay_text(delay)
                    
                    embed.add_field(
                        name=f"Bot Role #{i+1}",
                        value=f"{role.mention}{delay_text}",
                        inline=True
                    )
                else:
                    # Mark role for removal as it no longer exists
                    removed_roles["bot_roles"].append(i)
        
        # Remove non-existent roles from config (in reverse order to not mess up indices)
        config_updated = False
        for role_type in ["member_roles", "bot_roles"]:
            if role_type in self.autorole_config[guild_id] and removed_roles[role_type]:
                for i in sorted(removed_roles[role_type], reverse=True):
                    self.autorole_config[guild_id][role_type].pop(i)
                config_updated = True
        
        if config_updated:
            self.save_config()
            if (not self.autorole_config[guild_id].get("member_roles", []) and 
                not self.autorole_config[guild_id].get("bot_roles", [])):
                await interaction.response.send_message(
                    embed=EmbedHelper.info_embed(
                        "No Valid Autoroles",
                        "All previously configured autoroles have been removed because they no longer exist in the server."
                    )
                )
                return
        
        # Count total roles
        total_member_roles = len(self.autorole_config[guild_id].get("member_roles", []))
        total_bot_roles = len(self.autorole_config[guild_id].get("bot_roles", []))
        total_roles = total_member_roles + total_bot_roles
        
        embed.set_footer(text=f"Total autoroles: {total_roles} ({total_member_roles} for members, {total_bot_roles} for bots)")
        await interaction.response.send_message(embed=embed)
    
    @autorole.subcommand(
        name="clear-member",
        description="Remove all autoroles for human members from this server"
    )
    async def autorole_clear_member(self, interaction: Interaction):
        """Remove all autoroles for human members from this server"""
        # Check if user has manage roles permission
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return
        
        # Check if guild has any member autoroles configured
        guild_id = str(interaction.guild.id)
        if (guild_id not in self.autorole_config or 
            "member_roles" not in self.autorole_config[guild_id] or 
            not self.autorole_config[guild_id]["member_roles"]):
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "No Member Autoroles Configured",
                    "There are no autoroles configured for human members in this server."
                ),
                ephemeral=True
            )
            return
        
        # Ask for confirmation
        view = AutoroleView()
        await interaction.response.send_message(
            embed=EmbedHelper.warning_embed(
                "Confirmation Required",
                "Are you sure you want to remove all autoroles for human members from this server? This action cannot be undone."
            ),
            view=view
        )
        
        # Wait for the view to timeout or for a button to be pressed
        await view.wait()
        
        # If the user didn't confirm, abort
        if not view.value:
            await interaction.edit_original_message(
                embed=EmbedHelper.info_embed(
                    "Operation Cancelled",
                    "Member autorole clear operation was cancelled."
                ),
                view=None
            )
            return
        
        # Clear member autoroles and save config
        self.autorole_config[guild_id]["member_roles"] = []
        self.save_config()
        
        await interaction.edit_original_message(
            embed=EmbedHelper.success_embed(
                "Member Autoroles Cleared",
                "All autoroles for human members have been removed from this server."
            ),
            view=None
        )
    
    @autorole.subcommand(
        name="clear-bot",
        description="Remove all autoroles for bots from this server"
    )
    async def autorole_clear_bot(self, interaction: Interaction):
        """Remove all autoroles for bots from this server"""
        # Check if user has manage roles permission
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return
        
        # Check if guild has any bot autoroles configured
        guild_id = str(interaction.guild.id)
        if (guild_id not in self.autorole_config or 
            "bot_roles" not in self.autorole_config[guild_id] or 
            not self.autorole_config[guild_id]["bot_roles"]):
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "No Bot Autoroles Configured",
                    "There are no autoroles configured for bots in this server."
                ),
                ephemeral=True
            )
            return
        
        # Ask for confirmation
        view = AutoroleView()
        await interaction.response.send_message(
            embed=EmbedHelper.warning_embed(
                "Confirmation Required",
                "Are you sure you want to remove all autoroles for bots from this server? This action cannot be undone."
            ),
            view=view
        )
        
        # Wait for the view to timeout or for a button to be pressed
        await view.wait()
        
        # If the user didn't confirm, abort
        if not view.value:
            await interaction.edit_original_message(
                embed=EmbedHelper.info_embed(
                    "Operation Cancelled",
                    "Bot autorole clear operation was cancelled."
                ),
                view=None
            )
            return
        
        # Clear bot autoroles and save config
        self.autorole_config[guild_id]["bot_roles"] = []
        self.save_config()
        
        await interaction.edit_original_message(
            embed=EmbedHelper.success_embed(
                "Bot Autoroles Cleared",
                "All autoroles for bots have been removed from this server."
            ),
            view=None
        )
    
    @autorole.subcommand(
        name="clear-all",
        description="Remove all autoroles from this server (both member and bot roles)"
    )
    async def autorole_clear_all(self, interaction: Interaction):
        """Remove all autoroles from this server (both member and bot roles)"""
        # Check if user has manage roles permission
        if not self._check_permissions(interaction):
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return
        
        # Check if guild has any autoroles configured
        guild_id = str(interaction.guild.id)
        if (guild_id not in self.autorole_config or 
            (not self.autorole_config[guild_id].get("member_roles", []) and 
             not self.autorole_config[guild_id].get("bot_roles", []))):
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "No Autoroles Configured",
                    "There are no autoroles configured for this server."
                ),
                ephemeral=True
            )
            return
        
        # Ask for confirmation
        view = AutoroleView()
        await interaction.response.send_message(
            embed=EmbedHelper.warning_embed(
                "Confirmation Required",
                "Are you sure you want to remove all autoroles from this server (both member and bot roles)? This action cannot be undone."
            ),
            view=view
        )
        
        # Wait for the view to timeout or for a button to be pressed
        await view.wait()
        
        # If the user didn't confirm, abort
        if not view.value:
            await interaction.edit_original_message(
                embed=EmbedHelper.info_embed(
                    "Operation Cancelled",
                    "Autorole clear operation was cancelled."
                ),
                view=None
            )
            return
        
        # Clear all autoroles and save config
        self.autorole_config[guild_id] = {
            "member_roles": [],
            "bot_roles": []
        }
        self.save_config()
        
        await interaction.edit_original_message(
            embed=EmbedHelper.success_embed(
                "All Autoroles Cleared",
                "All autoroles (both member and bot roles) have been removed from this server."
            ),
            view=None
        )
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Event listener for when a member joins the server"""
        # Check if guild has any autoroles configured
        guild_id = str(member.guild.id)
        if guild_id not in self.autorole_config:
            return
        
        # Determine if the new member is a bot or human
        if member.bot:
            role_list = self.autorole_config[guild_id].get("bot_roles", [])
            member_type = "bot"
        else:
            role_list = self.autorole_config[guild_id].get("member_roles", [])
            member_type = "human member"
        
        # If no roles configured for this type, return
        if not role_list:
            return
        
        # Assign roles to the new member/bot
        for role_config in role_list:
            role_id = role_config["id"]
            role = member.guild.get_role(role_id)
            
            if not role:
                continue
                
            delay = role_config.get("delay")
            
            if delay:
                # Schedule delayed role assignment
                await asyncio.sleep(delay)
            
            try:
                # Check if member is still in the server
                if member in member.guild.members:
                    await member.add_roles(role)
                    logger.info(f"Assigned autorole {role.name} to {member_type} {member.name} in {member.guild.name}")
            except nextcord.Forbidden:
                logger.error(f"Missing permissions to assign autorole {role.name} to {member_type} {member.name} in {member.guild.name}")
            except Exception as e:
                logger.error(f"Error assigning autorole: {e}")