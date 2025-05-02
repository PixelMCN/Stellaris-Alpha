import nextcord
from nextcord.ext import commands
import asyncio
from utils.embed_helper import EmbedHelper
from utils.error_handler import ErrorHandler
from utils.embed_helper import EmbedColors
#=============================================================================================================================================================
class LogsCommands(commands.Cog):
    """Commands for setting up logging channels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.error_handler = ErrorHandler(bot)
        
    @nextcord.slash_command(
        name="logs",
        description="Set up logging channels for moderation actions"
    )
    async def logs(
        self, 
        interaction: nextcord.Interaction,
        category_name: str = nextcord.SlashOption(
            description="Name for the logs category (defaults to 'Logs')",
            required=False,
            default="Logs"
        )
    ):
        """Set up logging channels for moderation actions"""
        # Check if the user has permission to manage channels
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Channels"),
                ephemeral=True
            )
            return
            
        # Check if the bot has permission to manage channels
        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Manage Channels"),
                ephemeral=True
            )
            return
            
        # Defer response since channel creation might take time
        await interaction.response.defer(ephemeral=False)
        
        # Check if log channels already exist
        existing_channels = []
        mod_logs = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
        if mod_logs:
            existing_channels.append("mod-logs")
            
        error_logs = nextcord.utils.get(interaction.guild.channels, name="error-logs")
        if error_logs:
            existing_channels.append("error-logs")
            
        if existing_channels:
            # Create confirmation view
            view = LogsConfirmationView(self.bot, interaction, category_name, existing_channels)
            
            # Create embed for confirmation
            confirm_embed = EmbedHelper.warning_embed(
                "Logs Channels Already Exist",
                f"The following log channels already exist: **{', '.join(existing_channels)}**\n\n"
                f"Would you like to recreate them? This will delete the existing channels and create new ones."
            )
            
            await interaction.followup.send(embed=confirm_embed, view=view)
            return
            
        # If no existing channels, create them directly
        await self.create_log_channels(interaction, category_name)
        
    async def create_log_channels(self, interaction, category_name):
        """Create the logging channels"""
        try:
            # Find or create the logs category
            category = nextcord.utils.get(interaction.guild.categories, name=category_name)
            if not category:
                category = await interaction.guild.create_category(
                    name=category_name,
                    reason=f"Logs category created by {interaction.user}"
                )
                
            # Create permission overwrites for the category
            # Only staff should be able to see these channels
            overwrites = {
                interaction.guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: nextcord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Add overwrites for roles with moderation permissions
            for role in interaction.guild.roles:
                if role.permissions.ban_members or role.permissions.kick_members or role.permissions.manage_messages:
                    overwrites[role] = nextcord.PermissionOverwrite(read_messages=True)
                    
            # Update category permissions
            await category.edit(overwrites=overwrites)
            
            # Create mod-logs channel
            mod_logs = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
            if mod_logs:
                await mod_logs.delete(reason=f"Recreating mod-logs channel by {interaction.user}")
                
            mod_logs = await interaction.guild.create_text_channel(
                name="mod-logs",
                category=category,
                topic="Logs for moderation actions",
                reason=f"Mod logs channel created by {interaction.user}",
                overwrites=overwrites
            )
            
            # Create error-logs channel
            error_logs = nextcord.utils.get(interaction.guild.channels, name="error-logs")
            if error_logs:
                await error_logs.delete(reason=f"Recreating error-logs channel by {interaction.user}")
                
            error_logs = await interaction.guild.create_text_channel(
                name="error-logs",
                category=category,
                topic="Logs for bot errors",
                reason=f"Error logs channel created by {interaction.user}",
                overwrites=overwrites
            )
            
            # Create success embed
            success_embed = EmbedHelper.success_embed(
                "Logging Channels Created",
                f"Successfully created the following logging channels:\n"
                f"• {mod_logs.mention} - For moderation actions\n"
                f"• {error_logs.mention} - For bot errors\n\n"
                f"These channels are only visible to staff members with moderation permissions."
            )
            
            await interaction.followup.send(embed=success_embed)
            
            # Send a welcome message to each channel
            mod_welcome = nextcord.Embed(
                title="📝 Moderation Logs Channel",
                description="This channel will log all moderation actions performed by staff members.",
                color=EmbedColors.MODERATION
            )
            mod_welcome.add_field(
                name="Logged Actions",
                value="• Bans and Unbans\n• Mutes and Unmutes\n• Channel Locks\n• Slowmode Changes\n• Voice Deafens",
                inline=False
            )
            await mod_logs.send(embed=mod_welcome)
            
            error_welcome = nextcord.Embed(
                title="⚠️ Error Logs Channel",
                description="This channel will log all errors encountered by the bot.",
                color=EmbedColors.ERROR
            )
            error_welcome.add_field(
                name="Information",
                value="Error logs include details about the command, user, and error traceback to help with debugging.",
                inline=False
            )
            await error_logs.send(embed=error_welcome)
            
        except Exception as e:
            await self.error_handler.handle_command_error(interaction, e, "logs", True)
#=============================================================================================================================================================
class LogsConfirmationView(nextcord.ui.View):
    """View for confirming recreation of log channels"""
    
    def __init__(self, bot, interaction, category_name, existing_channels):
        super().__init__(timeout=60)
        self.bot = bot
        self.interaction = interaction
        self.category_name = category_name
        self.existing_channels = existing_channels
        self.error_handler = ErrorHandler(bot)
    #=============================================================================================================================================================
    @nextcord.ui.button(label="Yes, recreate channels", style=nextcord.ButtonStyle.danger)
    async def confirm_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Confirm button to recreate the channels"""
        # Disable all buttons
        for child in self.children:
            child.disabled = True
            
        await interaction.response.edit_message(view=self)
        
        # Get the logs command instance
        logs_cog = self.bot.get_cog("LogsCommands")
        if logs_cog:
            await logs_cog.create_log_channels(self.interaction, self.category_name)
        else:
            await interaction.followup.send(
                embed=EmbedHelper.error_embed(
                    "Error",
                    "Could not find the logs command. Please try again later."
                )
            )
    #=============================================================================================================================================================
    @nextcord.ui.button(label="No, keep existing channels", style=nextcord.ButtonStyle.secondary)
    async def cancel_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Cancel button to keep existing channels"""
        # Disable all buttons
        for child in self.children:
            child.disabled = True
            
        await interaction.response.edit_message(view=self)
        
        # Send cancellation message
        await interaction.followup.send(
            embed=EmbedHelper.info_embed(
                "Operation Cancelled",
                f"Keeping existing log channels: **{', '.join(self.existing_channels)}**"
            )
        )
        
    async def on_timeout(self):
        """Handle timeout"""
        # Disable all buttons
        for child in self.children:
            child.disabled = True
            
        try:
            await self.interaction.edit_original_message(view=self)
        except:
            pass


#=============================================================================================================================================================