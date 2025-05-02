import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
import os
import logging
from datetime import datetime
import asyncio

class HelpCommand(commands.Cog):
    """Enhanced command for displaying all available bot commands"""
    
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
        
    @nextcord.slash_command(
        name="help", 
        description="Display all available commands with detailed information"
    )
    async def help(
        self, 
        interaction: Interaction,
        category: str = SlashOption(
            description="Command category to display",
            required=False,
            choices={"All": "all", "Admin": "admin", "Moderation": "moderation", "Utility": "utility"}
        )
    ):
        """
        Display all available commands, optionally filtered by category
        
        Parameters
        ----------
        interaction : Interaction
            The interaction object containing the command context
        category : str, optional
            The command category to display. Defaults to "all"
        """
        try:
            # Defer response to allow time for processing
            await interaction.response.defer(ephemeral=False)
            
            # Default to showing all categories if none specified
            if not category:
                category = "all"
                
            # Create the main embed with pagination if necessary
            embed_pages = self._create_help_embeds(category, interaction.user)
            
            # If only one page, send it directly
            if len(embed_pages) == 1:
                await interaction.followup.send(embed=embed_pages[0])
                self.logger.info(f"Help command used by {interaction.user} (ID: {interaction.user.id}) - category: {category}")
                return
                
            # Otherwise, set up pagination
            current_page = 0
            message = await interaction.followup.send(
                embed=embed_pages[current_page],
                view=self._create_pagination_view(embed_pages, current_page)
            )
            
            self.logger.info(f"Help command with pagination used by {interaction.user} (ID: {interaction.user.id}) - category: {category}")
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Help command timed out for {interaction.user}")
            await interaction.followup.send("The help command timed out. Please try again.")
        except Exception as e:
            self.logger.error(f"Error in help command: {str(e)}", exc_info=True)
            await interaction.followup.send(
                "Sorry, I couldn't retrieve the command information. Please try again later or contact a server administrator.",
                ephemeral=True
            )
    
    def _create_pagination_view(self, pages, current_page):
        """Create navigation buttons for paginated embeds"""
        view = nextcord.ui.View(timeout=180)
        
        # Add the pagination buttons
        prev_button = nextcord.ui.Button(style=nextcord.ButtonStyle.secondary, emoji="⬅️", disabled=(current_page == 0))
        next_button = nextcord.ui.Button(style=nextcord.ButtonStyle.secondary, emoji="➡️", disabled=(current_page == len(pages) - 1))
        
        async def prev_callback(interaction: Interaction):
            nonlocal current_page
            current_page = max(0, current_page - 1)
            await interaction.response.edit_message(
                embed=pages[current_page],
                view=self._create_pagination_view(pages, current_page)
            )
            
        async def next_callback(interaction: Interaction):
            nonlocal current_page
            current_page = min(len(pages) - 1, current_page + 1)
            await interaction.response.edit_message(
                embed=pages[current_page],
                view=self._create_pagination_view(pages, current_page)
            )
            
        prev_button.callback = prev_callback
        next_button.callback = next_callback
        
        view.add_item(prev_button)
        view.add_item(next_button)
        
        return view
    
    def _create_help_embeds(self, category, user):
        """Create rich embeds with command information, potentially paginated"""
        embeds = []
        
        # Main embed with general information
        if category == "all":
            title = "📚 Bot Command Guide"
            description = "Here's a list of all available commands organized by category.\n\nUse `/help [category]` to see more detailed information about a specific category."
        else:
            title = f"📚 {self.categories[category]}"
            description = f"Here's a list of all {category.lower()} commands and their usage"
        
        main_embed = nextcord.Embed(
            title=title,
            description=description,
            color=self.embed_color
        )
        
        # Set author with bot information
        main_embed.set_author(
            name=f"{self.bot.user.name} Help System",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        # Add category commands
        if category == "all":
            # Create a summary page with command counts for each category
            admin_count = len(self._get_admin_commands(as_list=True))
            mod_count = len(self._get_moderation_commands(as_list=True))
            utility_count = len(self._get_utility_commands(as_list=True))
            
            main_embed.add_field(
                name="🛡️ Admin Commands",
                value=f"{admin_count} commands - Server management and configuration",
                inline=False
            )
            main_embed.add_field(
                name="🔨 Moderation Commands",
                value=f"{mod_count} commands - User moderation and channel management",
                inline=False
            )
            main_embed.add_field(
                name="🔧 Utility Commands",
                value=f"{utility_count} commands - Information and utility features",
                inline=False
            )
            
            # Add tips field
            main_embed.add_field(
                name="💡 Tips",
                value="• Commands with subcommands will show additional options when selected\n"
                      "• Most commands include detailed help information and examples\n"
                      "• Required parameters are marked with `*`",
                inline=False
            )
            
            embeds.append(main_embed)
            
            # Create individual category pages
            for cat in ["admin", "moderation", "utility"]:
                embeds.append(self._create_category_embed(cat, user))
                
        else:
            # Just add the requested category
            self._add_category_commands(main_embed, category)
            main_embed.set_footer(text=f"Requested by {user.name} • Page 1/1")
            main_embed.timestamp = datetime.now()
            embeds.append(main_embed)
        
        # Update footer for pagination
        for i, embed in enumerate(embeds):
            embed.set_footer(text=f"Requested by {user.name} • Page {i+1}/{len(embeds)}")
            embed.timestamp = datetime.now()
            
        return embeds
    
    def _create_category_embed(self, category, user):
        """Create an embed for a specific command category"""
        embed = nextcord.Embed(
            title=f"📚 {self.categories[category]}",
            description=f"Detailed list of {category.lower()} commands",
            color=self.embed_color
        )
        
        embed.set_author(
            name=f"{self.bot.user.name} Help System",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        self._add_category_commands(embed, category)
        
        return embed
        
    def _add_category_commands(self, embed, category):
        """Add appropriate command list to an embed based on category"""
        if category == "admin":
            commands = self._get_admin_commands()
            emoji = "🛡️"
            description = "Commands for server configuration and management"
        elif category == "moderation":
            commands = self._get_moderation_commands()
            emoji = "🔨"
            description = "Commands for moderating users and managing channels"
        elif category == "utility":
            commands = self._get_utility_commands()
            emoji = "🔧"
            description = "Utility commands for information and server assistance"
        else:
            return
            
        embed.add_field(
            name=f"{emoji} {self.categories[category]}",
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
            "• `/role info` - Get detailed information about a role (permissions, users, etc.)",
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
            "• `/mute` - Mute a user in text channels with optional duration and reason",
            "• `/unmute` - Unmute a previously muted user",
            "• `/deafen` - Deafen a user in voice channels",
            "• `/undeafen` - Undeafen a user in voice channels",
            "• `/lock` - Lock a channel to prevent messages from specific roles",
            "• `/unlock` - Unlock a previously locked channel",
            "• `/slowmode` - Set slowmode cooldown in a channel",
            "• `/purge` - Delete multiple messages with filters (user, contains, etc.)",
            "• `/clear` - Clear all messages in a channel with confirmation"
        ]
        
        return commands if as_list else "\n".join(commands)
    
    def _get_utility_commands(self, as_list=False):
        """Get formatted list of utility commands"""
        commands = [
            "• `/serverinfo` - Get detailed information about the server (roles, channels, etc.)",
            "• `/userinfo` - Get information about a user (roles, join date, etc.)",
            "• `/avatar` - View a user's avatar in full size with download options",
            "• `/activity` - Set a custom status for the bot (admin only)",
            "• `/ping` - Check the bot's response time and API latency",
            "• `/debug` - Show detailed bot diagnostics (admin only)",
            "• `/help` - Display this help message with detailed command information"
        ]
        
        return commands if as_list else "\n".join(commands)
    
    @nextcord.slash_command(
        name="command",
        description="Get detailed information about a specific command"
    )
    async def command_info(
        self,
        interaction: Interaction,
        command_name: str = SlashOption(
            description="The name of the command to look up",
            required=True
        )
    ):
        """
        Get detailed help for a specific command
        
        Parameters
        ----------
        interaction : Interaction
            The interaction object containing the command context
        command_name : str
            The name of the command to look up
        """
        try:
            await interaction.response.defer(ephemeral=False)
            
            # Remove leading slash if provided
            if command_name.startswith('/'):
                command_name = command_name[1:]
                
            # Find the command
            command_info = self._find_command_info(command_name)
            
            if not command_info:
                await interaction.followup.send(
                    f"Command `/{command_name}` not found. Use `/help` to see all available commands.",
                    ephemeral=True
                )
                return
                
            # Create and send the command info embed
            embed = self._create_command_info_embed(command_name, command_info)
            await interaction.followup.send(embed=embed)
            
            self.logger.info(f"Command info requested by {interaction.user} for /{command_name}")
            
        except Exception as e:
            self.logger.error(f"Error in command_info: {str(e)}", exc_info=True)
            await interaction.followup.send(
                "Sorry, I couldn't retrieve information for that command. Please try again later.",
                ephemeral=True
            )
    
    def _find_command_info(self, command_name):
        """Find detailed information about a specific command"""
        # This is a simplified example - in a real bot, you would
        # dynamically generate this from your command definitions
        
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
                "usage": "/help <category>",
                "examples": [
                    "/help",
                    "/help moderation"
                ],
                "permissions": [],
                "parameters": [
                    {"name": "category", "description": "Command category to display", "required": False}
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
            name="📝 Usage",
            value=f"`{info['usage']}`",
            inline=False
        )
        
        # Add examples
        if info["examples"]:
            embed.add_field(
                name="💡 Examples",
                value="\n".join([f"`{example}`" for example in info["examples"]]),
                inline=False
            )
        
        # Add parameters
        if info["parameters"]:
            param_text = ""
            for param in info["parameters"]:
                required = "✅ Required" if param["required"] else "❔ Optional"
                param_text += f"• **{param['name']}** - {param['description']} ({required})\n"
                
            embed.add_field(
                name="🔧 Parameters",
                value=param_text,
                inline=False
            )
        
        # Add required permissions
        if info["permissions"]:
            perm_text = "\n".join([f"• {perm}" for perm in info["permissions"]])
            embed.add_field(
                name="🔒 Required Permissions",
                value=perm_text,
                inline=False
            )
        else:
            embed.add_field(
                name="🔒 Required Permissions",
                value="None - Anyone can use this command",
                inline=False
            )
            
        # Add category for reference
        embed.add_field(
            name="📂 Category",
            value=info["category"].title(),
            inline=True
        )
        
        embed.set_footer(text=f"Type /help for a list of all commands")
        embed.timestamp = datetime.now()
        
        return embed