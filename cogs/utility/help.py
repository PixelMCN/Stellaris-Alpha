import nextcord
from nextcord.ext import commands
from typing import Dict, List, Optional
import inspect

#=============================================================================================================================================================
class HelpView(nextcord.ui.View):
    def __init__(self, help_cog, is_slash: bool = True):
        super().__init__(timeout=180)
        self.help_cog = help_cog
        self.is_slash = is_slash
        
        # Add dropdown for category selection
        self.add_item(CategorySelect(help_cog, is_slash))

#=============================================================================================================================================================
class CategorySelect(nextcord.ui.Select):
    def __init__(self, help_cog, is_slash: bool = True):
        self.help_cog = help_cog
        self.is_slash = is_slash
        
        # Get categories from the help cog
        categories = help_cog.get_categories()
        
        options = [
            nextcord.SelectOption(
                label="Home", 
                description="Main help page",
                value="home"
            )
        ]
        
        for category in categories:
            options.append(
                nextcord.SelectOption(
                    label=category.title(),
                    description=f"View {category} commands",
                    value=category
                )
            )
        
        super().__init__(
            placeholder="Select a category",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: nextcord.Interaction):
        if self.values[0] == "home":
            embed = self.help_cog.get_main_help_embed(self.is_slash)
        else:
            embed = self.help_cog.get_category_embed(self.values[0], self.is_slash)
        
        await interaction.response.edit_message(embed=embed, view=self.view)

#=============================================================================================================================================================
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_prefix = bot.command_prefix
        
        # Color scheme
        self.embed_color = nextcord.Color.from_rgb(32, 34, 37)  # Discord dark theme color
        self.title_color = nextcord.Color.from_rgb(114, 137, 218)  # Discord blurple
        
        # Category display names
        self.category_icons = {
            "moderation": "Moderation",
            "admin": "Administration",
            "utility": "Utility"
        }
        
        # ANSI color codes for codeblocks
        self.ansi_colors = {
            "reset": "\u001b[0m",
            "bold": "\u001b[1m",
            "underline": "\u001b[4m",
            "blue": "\u001b[34m",
            "cyan": "\u001b[36m",
            "green": "\u001b[32m",
            "yellow": "\u001b[33m",
            "red": "\u001b[31m",
            "magenta": "\u001b[35m",
            "white": "\u001b[37m",
            "bright_blue": "\u001b[34;1m",
            "bright_cyan": "\u001b[36;1m",
            "bright_green": "\u001b[32;1m",
            "bright_yellow": "\u001b[33;1m",
            "bright_red": "\u001b[31;1m",
            "bright_magenta": "\u001b[35;1m",
            "bright_white": "\u001b[37;1m",
            "bg_black": "\u001b[40m",
            "bg_blue": "\u001b[44m",
            "bg_cyan": "\u001b[46m",
            "bg_green": "\u001b[42m",
        }
        
        # Category color assignments for visual distinction
        self.category_colors = {
            "moderation": self.ansi_colors["bright_blue"],
            "admin": self.ansi_colors["bright_red"],
            "utility": self.ansi_colors["bright_green"],
        }
    #-------------------------------------------------------------------------------------------------------------------------------------------------------------
    def get_categories(self) -> List[str]:
        """Get all command categories from loaded cogs"""
        categories = set()
        
        for cog in self.bot.cogs.values():
            # Skip the help cog itself
            if cog.__class__.__name__ == "Help":
                continue
                
            # Get category from the cog's directory name
            module_path = inspect.getmodule(cog).__file__
            if "cogs" in module_path:
                category = module_path.split("cogs\\")[1].split("\\")[0]
                categories.add(category)
            
        return sorted(list(categories))
    #-------------------------------------------------------------------------------------------------------------------------------------------------------------
    def get_commands_by_category(self, category: str) -> Dict[str, List]:
        """Get all commands belonging to a specific category"""
        slash_commands = []
        prefix_commands = []
        
        for cog_name, cog in self.bot.cogs.items():
            # Skip the help cog itself
            if cog_name == "Help":
                continue
                
            # Get category from the cog's directory name
            module_path = inspect.getmodule(cog).__file__
            if "cogs" in module_path:
                cog_category = module_path.split("cogs\\")[1].split("\\")[0]
                if cog_category.lower() != category.lower():
                    continue
                
                # Get slash commands
                for cmd in cog.application_commands:
                    slash_commands.append(cmd)
                    
                # Get prefix commands
                for cmd in cog.get_commands():
                    prefix_commands.append(cmd)
                
        return {
            "slash": slash_commands,
            "prefix": prefix_commands
        }
    #-------------------------------------------------------------------------------------------------------------------------------------------------------------
    def format_command_help(self, cmd, is_slash: bool = True) -> str:
        """Format command help text with ANSI colors"""
        prefix = '/' if is_slash else self.command_prefix
        
        cmd_color = self.ansi_colors["bright_cyan"]
        param_color = self.ansi_colors["yellow"]
        desc_color = self.ansi_colors["white"]
        reset = self.ansi_colors["reset"]
        
        if is_slash:
            # Get options if any
            options = ""
            if hasattr(cmd, "options"):
                if isinstance(cmd.options, list):
                    options = " " + " ".join([f"{param_color}<{opt.name}>{reset}" for opt in cmd.options if hasattr(opt, 'name')])
                elif isinstance(cmd.options, str):
                    options = f" {param_color}<{cmd.options}>{reset}"
        
            return f"{cmd_color}{prefix}{cmd.name}{reset}{options} - {desc_color}{cmd.description or 'No description'}{reset}"
        else:
            # Get params if any
            params = ""
            if cmd.params:
                # Skip first param (ctx/self)
                param_iter = iter(cmd.params.items())
                next(param_iter)
                params = " " + " ".join([f"{param_color}<{name}>{reset}" for name, _ in param_iter])
        
            return f"{cmd_color}{prefix}{cmd.name}{reset}{params} - {desc_color}{cmd.description or cmd.help or 'No description'}{reset}"
    #-------------------------------------------------------------------------------------------------------------------------------------------------------------
    def get_main_help_embed(self, is_slash: bool = True) -> nextcord.Embed:
        """Create the main help embed showing all categories with ANSI colors"""
        cmd_type = "Slash" if is_slash else "Prefix"
        embed = nextcord.Embed(
            title=f"Stellaris Utils Help ({cmd_type} Commands)",
            description="Select a category from the dropdown menu below to view commands",
            color=self.embed_color
        )
        
        # Add categories as fields
        for category in self.get_categories():
            commands = self.get_commands_by_category(category)
            cmd_list = commands["slash"] if is_slash else commands["prefix"]
            
            if not cmd_list:
                continue
                
            display_name = self.category_icons.get(category.lower(), category.title())
            category_color = self.category_colors.get(category.lower(), self.ansi_colors["bright_magenta"])
            
            # Create ANSI formatted text for the category
            ansi_text = f"```ansi\n{category_color}{self.ansi_colors['bold']}{len(cmd_list)} commands available{self.ansi_colors['reset']}\n```"
            
            embed.add_field(
                name=display_name,
                value=ansi_text,
                inline=True
            )
        
        # Set footer
        prefix_text = "Use /help for slash commands" if not is_slash else f"Use {self.command_prefix}help for prefix commands"
        embed.set_footer(text=prefix_text)
        
        return embed
    #-------------------------------------------------------------------------------------------------------------------------------------------------------------
    def get_category_embed(self, category: str, is_slash: bool = True) -> nextcord.Embed:
        """Create embed for a specific category with colored ANSI codeblocks"""
        cmd_type = "Slash" if is_slash else "Prefix"
        display_name = self.category_icons.get(category.lower(), category.title())
        
        embed = nextcord.Embed(
            title=f"{display_name} Commands",
            color=self.embed_color
        )
        
        # Get category color
        category_color = self.category_colors.get(category.lower(), self.ansi_colors["bright_magenta"])
        
        # Create colored header
        header = f"```ansi\n{category_color}{self.ansi_colors['bold']}{cmd_type} commands in the {display_name} category{self.ansi_colors['reset']}\n```"
        embed.description = header
        
        commands = self.get_commands_by_category(category)
        cmd_list = commands["slash"] if is_slash else commands["prefix"]
        
        # Sort commands alphabetically
        cmd_list.sort(key=lambda x: x.name)
        
        # Group commands by subcategories if applicable
        subcategories = {}
        for cmd in cmd_list:
            subcategory = getattr(cmd, "subcategory", "General")
            if subcategory not in subcategories:
                subcategories[subcategory] = []
            subcategories[subcategory].append(cmd)
        
        # Add fields for each subcategory
        for subcategory, subcmds in subcategories.items():
            if not subcmds:
                continue
            
            # Use ANSI colors for subcategory header
            header_color = self.ansi_colors["underline"] + self.ansi_colors["bright_white"]
            commands_text = "\n".join([self.format_command_help(cmd, is_slash) for cmd in subcmds])
            
            field_value = f"```ansi\n{header_color}{subcategory}{self.ansi_colors['reset']}\n{commands_text}\n```"
            
            embed.add_field(
                name=subcategory,
                value=field_value,
                inline=False
            )
        
        # Set footer
        prefix_text = "Use /help for slash commands" if not is_slash else f"Use {self.command_prefix}help for prefix commands"
        embed.set_footer(text=prefix_text)
        
        return embed
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="help", description="Get help with bot commands")
    async def help_slash(self, interaction: nextcord.Interaction, category: str = None):
        """Display help for commands using a clean, interactive interface"""
        if category:
            # Show specific category
            embed = self.get_category_embed(category, is_slash=True)
        else:
            # Show main help page
            embed = self.get_main_help_embed(is_slash=True)
        
        view = HelpView(self, is_slash=True)
        await interaction.response.send_message(embed=embed, view=view)
    #-------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Prefix command implementation
    @commands.command(name="help", description="Get help with bot commands")
    async def help_prefix(self, ctx, category: str = None):
        """Display help for prefix commands using a clean, interactive interface"""
        if category:
            # Show specific category
            embed = self.get_category_embed(category, is_slash=False)
        else:
            # Show main help page
            embed = self.get_main_help_embed(is_slash=False)
        
        view = HelpView(self, is_slash=False)
        await ctx.send(embed=embed, view=view)
    #=============================================================================================================================================================