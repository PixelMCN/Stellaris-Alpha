import nextcord
import traceback
import sys
import datetime
from .embed_helper import EmbedHelper

class ErrorHandler:
    def __init__(self, bot):
        self.bot = bot
        
    async def handle_command_error(self, interaction: nextcord.Interaction, error: Exception, command_name: str = None, is_followup: bool = False):
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
        
        # Create user-friendly error message based on error type
        if isinstance(error, nextcord.errors.Forbidden):
            embed = EmbedHelper.error_embed(
                "Action Failed",
                "I don't have permission to do that."
            )
        elif isinstance(error, nextcord.errors.NotFound):
            embed = EmbedHelper.error_embed(
                "Not Found",
                "I couldn't find what you're looking for."
            )
        elif isinstance(error, nextcord.errors.HTTPException):
            if "40032" in str(error):  # User not in voice channel
                embed = EmbedHelper.error_embed(
                    "Voice Channel Required",
                    "The user needs to be in a voice channel for this command."
                )
            else:
                embed = EmbedHelper.error_embed(
                    "Discord Error",
                    "There was a problem with Discord. Please try again later."
                )
        elif "is not connected to voice" in str(error):
            embed = EmbedHelper.error_embed(
                "Voice Channel Required",
                "The user needs to be in a voice channel for this command."
            )
        else:
            embed = EmbedHelper.error_embed(
                "Something Went Wrong",
                "An unexpected error occurred. Please try again later."
            )
        
        # Add footer with error ID
        embed.set_footer(text=f"Error ID: {interaction.id}")
        
        # Try to send to the user
        try:
            if not interaction.response.is_done() and not is_followup:
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
                # Create a more detailed embed for the error logs
                log_embed = nextcord.Embed(
                    title=f"Command Error: /{command_name}",
                    description=f"**Error Type:** `{error_type}`\n**Error Message:** `{str(error)}`",
                    color=0xFF0000,
                    timestamp=datetime.datetime.now()
                )
                
                log_embed.add_field(name="User", value=f"{interaction.user.mention} ({interaction.user.id})", inline=True)
                log_embed.add_field(name="Channel", value=f"{interaction.channel.mention} ({interaction.channel.id})", inline=True)
                
                # Add truncated traceback
                trace_lines = error_trace.split('\n')
                if len(trace_lines) > 15:
                    trace_lines = trace_lines[:15] + ["..."]
                
                trace_text = '\n'.join(trace_lines)
                if len(trace_text) > 1024:
                    trace_text = trace_text[:1021] + "..."
                    
                log_embed.add_field(name="Traceback", value=f"```py\n{trace_text}\n```", inline=False)
                log_embed.set_footer(text=f"Error ID: {interaction.id}")
                
                await error_channel.send(embed=log_embed)
        except:
            # If we can't send to the error logs channel, just continue
            pass
            
    def register_error_handlers(self):
        """Register the global error handler for application commands"""
        @self.bot.event
        async def on_application_command_error(interaction: nextcord.Interaction, error: Exception):
            await self.handle_command_error(interaction, error)