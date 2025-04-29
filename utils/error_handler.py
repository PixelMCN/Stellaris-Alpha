import nextcord
import traceback
import sys
import datetime
from typing import Optional, Union, Callable, Coroutine, Any

class ErrorHandler:
    def __init__(self, bot):
        self.bot = bot
        
    async def handle_command_error(self, interaction: nextcord.Interaction, error: Exception, command_name: str = None):
        """Handle errors from slash commands and send formatted error messages"""
        error_type = type(error).__name__
        error_trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        
        # Get command name if not provided
        if command_name is None and hasattr(interaction, 'application_command'):
            command_name = interaction.application_command.name
        elif command_name is None:
            command_name = "Unknown Command"
            
        # Print to terminal with formatting
        print(f"\n{'='*50}")
        print(f"Error in command: {command_name}")
        print(f"Error type: {error_type}")
        print(f"User: {interaction.user} (ID: {interaction.user.id})")
        print(f"Guild: {interaction.guild.name if interaction.guild else 'DM'} (ID: {interaction.guild.id if interaction.guild else 'N/A'})")
        print(f"Error: {str(error)}")
        print(f"Traceback:\n{error_trace}")
        print(f"{'='*50}\n")
        
        # Create user-friendly error message
        embed = nextcord.Embed(
            title=f"Error in /{command_name}",
            color=0xFF0000,
            timestamp=datetime.datetime.now()
        )
        
        # Add user-friendly error message based on error type
        if isinstance(error, nextcord.errors.Forbidden):
            if "50013" in str(error):  # Missing Permissions error code
                embed.description = "I don't have the required permissions to perform this action."
                embed.add_field(name="Required Permission", value="Make sure I have the appropriate role and permissions.")
            else:
                embed.description = "I don't have permission to do that."
        elif isinstance(error, nextcord.errors.NotFound):
            embed.description = "The requested resource was not found."
        elif isinstance(error, nextcord.errors.HTTPException):
            embed.description = "There was an error communicating with Discord."
        else:
            embed.description = f"An unexpected error occurred: `{str(error)}`"
        
        # Add error details
        embed.add_field(name="Error Type", value=f"`{error_type}`", inline=True)
        embed.add_field(name="Command", value=f"`/{command_name}`", inline=True)
        
        # Add footer with error ID
        embed.set_footer(text=f"Error ID: {interaction.id}")
        
        # Try to send to the user
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
        except nextcord.errors.HTTPException:
            # If we can't respond to the interaction, try to send a message to the channel
            try:
                await interaction.channel.send(embed=embed)
            except:
                pass
                
        # Try to send to error logs channel if it exists
        try:
            error_channel = nextcord.utils.get(interaction.guild.channels, name="error-logs")
            if error_channel:
                # Add more detailed information for the error logs
                embed.add_field(name="User", value=f"{interaction.user.mention} ({interaction.user.id})", inline=True)
                embed.add_field(name="Channel", value=f"{interaction.channel.mention} ({interaction.channel.id})", inline=True)
                
                # Add truncated traceback
                trace_lines = error_trace.split('\n')
                if len(trace_lines) > 15:
                    trace_lines = trace_lines[:15] + ["..."]
                
                trace_text = '\n'.join(trace_lines)
                if len(trace_text) > 1024:
                    trace_text = trace_text[:1021] + "..."
                    
                embed.add_field(name="Traceback", value=f"```py\n{trace_text}\n```", inline=False)
                
                await error_channel.send(embed=embed)
        except:
            # If we can't send to the error logs channel, just continue
            pass
            
    def register_error_handlers(self):
        """Register the global error handler for application commands"""
        @self.bot.event
        async def on_application_command_error(interaction: nextcord.Interaction, error: Exception):
            await self.handle_command_error(interaction, error)