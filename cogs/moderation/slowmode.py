import nextcord
from nextcord.ext import commands


class Slowmode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = bot.error_handler

    # SLOWMODE COMMANDS with seconds & hours
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(
        name="slowmode", 
        description="Set the slowmode delay for the current channel"
    )
    async def slowmode(
        self, 
        interaction: nextcord.Interaction, 
        seconds: int = nextcord.SlashOption(
            description="Slowmode delay in seconds (0-21600, 0 to disable)",
            required=False,
            min_value=0,
            max_value=21600
        ), 
        hours: int = nextcord.SlashOption(
            description="Slowmode delay in hours (0-6, 0 to disable)",
            required=False,
            min_value=0,
            max_value=6
        )
    ):
        """
        Sets the slowmode delay for the current channel.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        seconds: Optional - Slowmode delay in seconds (0-21600, 0 to disable)
        hours: Optional - Slowmode delay in hours (0-6, 0 to disable)
        
        Note: You can specify either seconds OR hours, not both.
        """
        try:
            # Check if user has permission to manage channels
            if not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message(
                    "❌ You don't have permission to modify channel settings.", 
                    ephemeral=True
                )
                return
            
            # Validate input parameters
            if seconds is None and hours is None:
                # Show current slowmode if no parameters provided
                current_slowmode = interaction.channel.slowmode_delay
                if current_slowmode == 0:
                    await interaction.response.send_message(
                        f"ℹ️ Slowmode is currently disabled in #{interaction.channel.name}.",
                        ephemeral=True
                    )
                else:
                    # Format time for better readability
                    if current_slowmode >= 3600:
                        hours_val = current_slowmode // 3600
                        remaining_seconds = current_slowmode % 3600
                        if remaining_seconds == 0:
                            time_str = f"{hours_val} hour{'s' if hours_val > 1 else ''}"
                        else:
                            time_str = f"{hours_val} hour{'s' if hours_val > 1 else ''} and {remaining_seconds} second{'s' if remaining_seconds > 1 else ''}"
                    else:
                        time_str = f"{current_slowmode} second{'s' if current_slowmode > 1 else ''}"
                    
                    await interaction.response.send_message(
                        f"ℹ️ Current slowmode in #{interaction.channel.name} is set to {time_str}.\n"\
                        "To change it, specify either seconds or hours.",
                        ephemeral=True
                    )
                return

            if seconds is not None and hours is not None:
                await interaction.response.send_message(
                    "❌ Please specify either seconds OR hours, not both.", 
                    ephemeral=True
                )
                return

            # Calculate slowmode delay
            slowmode_delay = 0
            if hours is not None:
                slowmode_delay = hours * 3600
                time_str = f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                slowmode_delay = seconds
                time_str = f"{seconds} second{'s' if seconds != 1 else ''}"
            
            # Apply the slowmode delay
            await interaction.channel.edit(slowmode_delay=slowmode_delay)
            
            # Create appropriate feedback message
            if slowmode_delay == 0:
                await interaction.response.send_message(
                    f"⏱️ Slowmode has been disabled in #{interaction.channel.name}.",
                    ephemeral=False
                )
            else:
                await interaction.response.send_message(
                    f"⏱️ Slowmode in #{interaction.channel.name} has been set to {time_str}.",
                    ephemeral=False
                )
                
        except nextcord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to edit channel settings. Please check my role permissions.", 
                ephemeral=True
            )
        except nextcord.HTTPException as e:
            if e.code == 50035:  # Invalid Form Body error
                await interaction.response.send_message(
                    "❌ The slowmode value is invalid. Please use a value between 0 and 21600 seconds (6 hours).",
                    ephemeral=True
                )
            else:
                await self.error_handler.handle_command_error(interaction, e, "slowmode")
        except Exception as e:
            # Let the global error handler handle other exceptions
            await self.error_handler.handle_command_error(interaction, e, "slowmode")
    #=============================================================================================================================================================
