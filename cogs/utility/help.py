import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
import logging
from datetime import datetime
#=============================================================================================================================================================
class HelpCommand(commands.Cog):
    """Clean and professional help command for displaying available bot commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('bot.Help')
        self.embed_color = 0x5865F2  # Discord Blurple
        self.categories = {
            "all": "All Commands",
            "admin": "Admin Commands",
            "moderation": "Moderation Commands", 
            "utility": "Utility Commands"
        }
#=============================================================================================================================================================        
    @nextcord.slash_command(
        name="help", 
        description="Display available commands with detailed information"
    )
    async def help(
        self, 
        interaction: Interaction,
        category: str = SlashOption(
            description="Command category to display",
            required=False,
            choices={"All": "all", "Admin": "admin", "Moderation": "moderation", "Utility": "utility"}
        ),
        command: str = SlashOption(
            description="Specific command to get help for",
            required=False
        )
    ):
        """
        Display all available commands or get help for a specific command
        
        Parameters
        ----------
        interaction : Interaction
            The interaction object containing the command context
        category : str, optional
            The command category to display. Defaults to "all"
        command : str, optional
            Specific command to get help for
        """
        try:
            await interaction.response.defer(ephemeral=False)
            
            # If a specific command was requested
            if command:
                command_info = self._find_command_info(command)
                if not command_info:
                    await interaction.followup.send(
                        f"Command `/{command}` not found. Use `/help` to see all available commands.",
                        ephemeral=True
                    )
                    return
                
                # Send command-specific help
                embed = self._create_command_info_embed(command, command_info)
                await interaction.followup.send(embed=embed)
                self.logger.info(f"Command info requested by {interaction.user} for /{command}")
                return
            
            # Default to showing all categories if none specified
            if not category:
                category = "all"
                
            # Create the help embed
            embed = self._create_help_embed(category, interaction.user)
            
            # Send the embed with pagination if needed
            if category == "all":
                # Create view with dropdown menu for category selection
                view = self._create_category_select_view(interaction.user)
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(embed=embed)
                
            self.logger.info(f"Help command used by {interaction.user} (ID: {interaction.user.id}) - category: {category}")
            
        except Exception as e:
            self.logger.error(f"Error in help command: {str(e)}", exc_info=True)
            await interaction.followup.send(
                "Sorry, I couldn't retrieve the command information. Please try again later.",
                ephemeral=True
            )
    
    def _create_category_select_view(self, user):
        """Create dropdown menu for category selection"""
        view = nextcord.ui.View(timeout=180)
        
        # Add dropdown for categories
        select = nextcord.ui.Select(
            placeholder="Select a category",
            options=[
                nextcord.SelectOption(label="All Commands", value="all", description="View all available commands"),
                nextcord.SelectOption(label="Admin Commands", value="admin", description="Server management commands"),
                nextcord.SelectOption(label="Moderation Commands", value="moderation", description="User moderation commands"),
                nextcord.SelectOption(label="Utility Commands", value="utility", description="Information and utility commands")
            ]
        )
        
        async def select_callback(interaction: Interaction):
            category = select.values[0]
            embed = self._create_help_embed(category, user)
            await interaction.response.edit_message(embed=embed, view=self._create_category_select_view(user))
        
        select.callback = select_callback
        view.add_item(select)
        
        return view
    
    def _create_help_embed(self, category, user):
        """Create a rich embed with command information"""
        if category == "all":
            title = "Bot Command Guide"
            description = "Here's a list of all available commands organized by category.\n\nUse the dropdown menu below to view specific categories or use `/help [category]` to see more details."
        else:
            title = f"{self.categories[category]}"
            description = f"Here's a list of all {category.lower()} commands and their usage"
        
        embed = nextcord.Embed(
            title=title,
            description=description,
            color=self.embed_color
        )
        
        # Set author with bot information
        embed.set_author(
            name=f"{self.bot.user.name} Help System",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        # Add commands based on category
        if category == "all":
            # Summary of all command categories
            admin_commands = self._get_admin_commands(as_list=True)
            mod_commands = self._get_moderation_commands(as_list=True)
            utility_commands = self._get_utility_commands(as_list=True)
            
            embed.add_field(
                name="Admin Commands",
                value=f"{len(admin_commands)} commands - Server management and configuration",
                inline=False
            )
            embed.add_field(
                name="Moderation Commands",
                value=f"{len(mod_commands)} commands - User moderation and channel management",
                inline=False
            )
            embed.add_field(
                name="Utility Commands",
                value=f"{len(utility_commands)} commands - Information and utility features",
                inline=False
            )
            
            # Add tips field
            embed.add_field(
                name="Tips",
                value="• Commands with subcommands will show additional options when selected\n"
                      "• Use `/help command:[command_name]` to see detailed information about a specific command\n"
                      "• Required parameters are marked with `*`",
                inline=False
            )
        else:
            # Add the requested category commands
            self._add_category_commands(embed, category)
        
        # Set footer and timestamp
        embed.set_footer(text=f"Requested by {user.name}")
        embed.timestamp = datetime.now()
        
        return embed
    
    def _add_category_commands(self, embed, category):
        """Add appropriate command list to an embed based on category"""
        if category == "admin":
            commands = self._get_admin_commands()
            description = "Commands for server configuration and management"
        elif category == "moderation":
            commands = self._get_moderation_commands()
            description = "Commands for moderating users and managing channels"
        elif category == "utility":
            commands = self._get_utility_commands()
            description = "Utility commands for information and server assistance"
        else:
            return
            
        embed.add_field(
            name=f"{self.categories[category]}",
            value=description,
            inline=False
        )
        
        # Split into multiple fields if needed for readability
        if len(commands) > 1024:
            parts = self._split_long_text(commands, 1024)
            for i, part in enumerate(parts):
                embed.add_field(
                    name=f"Commands {i+1}/{len(parts)}",
                    value=part,
                    inline=False
                )
        else:
            embed.add_field(
                name="Available Commands",
                value=commands,
                inline=False
            )
    
    def _split_long_text(self, text, max_length):
        """Split text into chunks that fit within Discord's embed field limits"""
        parts = []
        lines = text.split('\n')
        current_part = ""
        
        for line in lines:
            if len(current_part) + len(line) + 1 > max_length:
                parts.append(current_part)
                current_part = line
            else:
                if current_part:
                    current_part += "\n" + line
                else:
                    current_part = line
                    
        if current_part:
            parts.append(current_part)
            
        return parts
    
    def _get_admin_commands(self, as_list=False):
        """Get formatted list of admin commands"""
        commands = [
            "• `/role` - Manage server roles",
            "• `/role add` - Add a role to users with optional reason",
            "• `/role remove` - Remove a role from users with optional reason",
            "• `/role info` - Get detailed information about a role",
            "• `/logs` - Set up logging channels for moderation actions",
            "• `/logs set` - Configure which channel receives specific log events",
            "• `/logs status` - View current logging configuration",
            "• `/autorole` - Configure automatic role assignment for new members",
            "• `/autorole add` - Add a role to the autorole list",
            "• `/autorole remove` - Remove a role from the autorole list",
            "• `/autorole list` - View all autoroles"
        ]
        
        return commands if as_list else "\n".join(commands)
    
    def _get_moderation_commands(self, as_list=False):
        """Get formatted list of moderation commands"""
        commands = [
            "• `/ban` - Ban a user from the server with optional duration and reason",
            "• `/unban` - Unban a user from the server",
            "• `/baninfo` - Get information about a banned user",
            "• `/banlist` - View all banned users",
            "• `/kick` - Kick a user from the server with optional reason",
            "• `/softban` - Ban and immediately unban a user to delete their messages",
            "• `/mute` - Mute a user in text channels with optional duration",
            "• `/unmute` - Unmute a previously muted user",
            "• `/deafen` - Deafen a user in voice channels",
            "• `/undeafen` - Undeafen a user in voice channels",
            "• `/lock` - Lock a channel to prevent messages from specific roles",
            "• `/unlock` - Unlock a previously locked channel",
            "• `/slowmode` - Set slowmode cooldown in a channel",
            "• `/purge` - Delete multiple messages with filters",
            "• `/clear` - Clear all messages in a channel with confirmation"
        ]
        
        return commands if as_list else "\n".join(commands)
    
    def _get_utility_commands(self, as_list=False):
        """Get formatted list of utility commands"""
        commands = [
            "• `/serverinfo` - Get detailed information about the server",
            "• `/userinfo` - Get information about a user",
            "• `/avatar` - View a user's avatar in full size with download options",
            "• `/activity` - Set a custom status for the bot (admin only)",
            "• `/ping` - Check the bot's response time and API latency",
            "• `/debug` - Show detailed bot diagnostics (admin only)",
            "• `/help` - Display this help message with detailed command information"
        ]
        
        return commands if as_list else "\n".join(commands)
    
    def _find_command_info(self, command_name):
        """Find detailed information about a specific command"""
        # Remove leading slash if provided
        if command_name.startswith('/'):
            command_name = command_name[1:]
            
        # This would be dynamically generated in a real bot
        # Just showing a simplified example here
        command_details = {
            "ban": {
                "category": "moderation",
                "description": "Ban a user from the server",
                "usage": "/ban [user] <duration> <reason>",
                "examples": [
                    "/ban @User Breaking server rules",
                    "/ban @User 7d Repeated violations"
                ],
                "permissions": ["BAN_MEMBERS"],
                "parameters": [
                    {"name": "user", "description": "The user to ban", "required": True},
                    {"name": "duration", "description": "Duration of the ban (e.g. 1d, 1w)", "required": False},
                    {"name": "reason", "description": "Reason for the ban", "required": False}
                ]
            },
            "help": {
                "category": "utility",
                "description": "Display all available commands",
                "usage": "/help <category> <command>",
                "examples": [
                    "/help",
                    "/help category:moderation",
                    "/help command:ban"
                ],
                "permissions": [],
                "parameters": [
                    {"name": "category", "description": "Command category to display", "required": False},
                    {"name": "command", "description": "Specific command to get help for", "required": False}
                ]
            },
            # Add more commands as needed
        }
        
        return command_details.get(command_name.lower())
    
    def _create_command_info_embed(self, command_name, info):
        """Create a detailed embed for a specific command"""
        embed = nextcord.Embed(
            title=f"Command: /{command_name}",
            description=info["description"],
            color=self.embed_color
        )
        
        # Add usage information
        embed.add_field(
            name="Usage",
            value=f"`{info['usage']}`",
            inline=False
        )
        
        # Add examples
        if info["examples"]:
            embed.add_field(
                name="Examples",
                value="\n".join([f"`{example}`" for example in info["examples"]]),
                inline=False
            )
        
        # Add parameters
        if info["parameters"]:
            param_text = ""
            for param in info["parameters"]:
                required = "Required" if param["required"] else "Optional"
                param_text += f"• **{param['name']}** - {param['description']} ({required})\n"
                
            embed.add_field(
                name="Parameters",
                value=param_text,
                inline=False
            )
        
        # Add required permissions
        if info["permissions"]:
            perm_text = "\n".join([f"• {perm}" for perm in info["permissions"]])
            embed.add_field(
                name="Required Permissions",
                value=perm_text,
                inline=False
            )
        else:
            embed.add_field(
                name="Required Permissions",
                value="None - Anyone can use this command",
                inline=False
            )
            
        # Add category for reference
        embed.add_field(
            name="Category",
            value=info["category"].title(),
            inline=True
        )
        
        embed.set_footer(text="Type /help for a list of all commands")
        embed.timestamp = datetime.now()
        
        return embed
#=============================================================================================================================================================