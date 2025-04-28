import nextcord
import random
from nextcord.ext import commands
from nextcord import Interaction
from datetime import timedelta
from enum import Enum


class DurationType(str, Enum):
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"


class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TIMEOUT COMMANDS
    #=============================================================================================================================================================
    @nextcord.slash_command(name="timeout", description="Manage member timeouts")
    async def timeout(self, interaction: Interaction):
        pass
    
    # TIMEOUT ADD COMMAND
    #=============================================================================================================================================================
    @timeout.subcommand(name="add", description="Timeout a member")
    async def timeout_add(self, interaction: Interaction, 
                         member: nextcord.Member, 
                         duration: str = nextcord.SlashOption(
                             description="Duration (e.g., 1s, 5m, 2h, 3d)", required=True),
                         reason: str = nextcord.SlashOption(description="Reason for timeout", required=False)):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("This command requires ``moderate members permission``", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # List of timeout reasons
        timeout_reasons = [
            "Breaking server rules",
            "Spamming",
            "Disruptive behavior",
            "Toxicity"
        ]

        # Select a random reason if reason is not provided
        if reason is None:
            reason = random.choice(timeout_reasons)

        # Parse duration string (e.g., 1s, 5m, 2h, 3d)
        import re
        match = re.fullmatch(r"(\d+)([smhd])", duration.strip().lower())
        if not match:
            await interaction.followup.send("Invalid duration format. Use like 1s, 5m, 2h, 3d.", ephemeral=True)
            return

        value, unit = int(match.group(1)), match.group(2)
        if unit == "s":
            time_delta = timedelta(seconds=value)
            duration_text = f"{value} seconds"
        elif unit == "m":
            time_delta = timedelta(minutes=value)
            duration_text = f"{value} minutes"
        elif unit == "h":
            time_delta = timedelta(hours=value)
            duration_text = f"{value} hours"
        elif unit == "d":
            time_delta = timedelta(days=value)
            duration_text = f"{value} days"
        else:
            await interaction.followup.send("Invalid duration unit. Use s, m, h, or d.", ephemeral=True)
            return

        # Apply timeout 
        try:
            await member.timeout(time_delta, reason=reason)
            
            embed = nextcord.Embed(title="Member Timed Out", color=nextcord.Color.orange())
            embed.add_field(name="Member", value=member.mention, inline=True)
            embed.add_field(name="Duration", value=duration_text, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.followup.send(embed=embed)
            
            # Send a direct message to the timed out member
            try:
                await member.send(f"You have been timed out in **{interaction.guild.name}** for {duration_text}. Reason: {reason}")
            except nextcord.HTTPException:
                await interaction.followup.send("Failed to send a direct message to the timed out member.", ephemeral=True)
                
        except nextcord.Forbidden:
            await interaction.followup.send("I don't have permission to timeout this member.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Prefix command implementation
    @commands.command(name="timeout-add")
    async def timeout_add_prefix(self, ctx, member: nextcord.Member = None, duration: str = None, reason: str = None):
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.send("This command requires ``moderate members permission``", ephemeral=True)
            return

        if member is None:
            await ctx.send("Please mention a member to timeout.", ephemeral=True)
            return

        if duration is None:
            await ctx.send("Please provide a duration for the timeout (e.g., 1s, 5m, 2h, 3d).", ephemeral=True)
            return

        if reason is None:
            reason = "Timeout by moderator"

        # Parse duration string (e.g., 1s, 5m, 2h, 3d)
        import re
        match = re.fullmatch(r"(\d+)([smhd])", duration.strip().lower())
        if not match:
            await ctx.send("Invalid duration format. Use like 1s, 5m, 2h, 3d.", ephemeral=True)
            return

        value, unit = int(match.group(1)), match.group(2)
        if unit == "s":
            time_delta = timedelta(seconds=value)
            duration_text = f"{value} seconds"
        elif unit == "m":
            time_delta = timedelta(minutes=value)
            duration_text = f"{value} minutes"
        elif unit == "h":
            time_delta = timedelta(hours=value)
            duration_text = f"{value} hours"
        elif unit == "d":
            time_delta = timedelta(days=value)
            duration_text = f"{value} days"
        else:
            await ctx.send("Invalid duration unit. Use s, m, h, or d.", ephemeral=True)
            return

        # Apply timeout
        try:
            await member.timeout(time_delta, reason=reason)

            embed = nextcord.Embed(title="Member Timed Out", color=nextcord.Color.orange())
            embed.add_field(name="Member", value=member.mention, inline=True)
            embed.add_field(name="Duration", value=duration_text, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)

            await ctx.send(embed=embed)

            # Send a direct message to the timed out member
            try:
                await member.send(f"You have been timed out in **{ctx.guild.name}** for {duration_text}. Reason: {reason}")
            except nextcord.HTTPException:
                await ctx.send("Failed to send a direct message to the timed out member.", ephemeral=True)

        except nextcord.Forbidden:
            await ctx.send("I don't have permission to timeout this member.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
    #=============================================================================================================================================================

    
    # TIMEOUT REMOVE COMMAND
    #=============================================================================================================================================================
    # Slash command implementation
    @timeout.subcommand(name="remove", description="Remove timeout from a member")
    async def timeout_remove(self, interaction: Interaction, member: nextcord.Member, reason: str = nextcord.SlashOption(description="Reason for removing timeout", required=False)):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("This command requires ``moderate members permission``", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        if reason is None:
            reason = "Timeout removed by moderator"

        # Remove timeout
        try:
            await member.timeout(None, reason=reason)
            
            embed = nextcord.Embed(title="Timeout Removed", color=nextcord.Color.green())
            embed.add_field(name="Member", value=member.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.followup.send(embed=embed)
            
            # Send a direct message to the member
            try:
                await member.send(f"Your timeout in **{interaction.guild.name}** has been removed. Reason: {reason}")
            except nextcord.HTTPException:
                await interaction.followup.send("Failed to send a direct message to the member.", ephemeral=True)
                
        except nextcord.Forbidden:
            await interaction.followup.send("I don't have permission to remove timeout from this member.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Prefix command implementation
    @commands.command(name="timeout-remove")
    async def timeout_remove_prefix(self, ctx, member: nextcord.Member = None, reason: str = None):
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.send("This command requires ``moderate members permission``", ephemeral=True)
            return

        if member is None:
            await ctx.send("Please mention a member to remove timeout from.", ephemeral=True)
            return

        if reason is None:
            reason = "Timeout removed by moderator"

        # Remove timeout
        try:
            await member.timeout(None, reason=reason)

            embed = nextcord.Embed(title="Timeout Removed", color=nextcord.Color.green())
            embed.add_field(name="Member", value=member.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)

            await ctx.send(embed=embed)

            # Send a direct message to the member
            try:
                await member.send(f"Your timeout in **{ctx.guild.name}** has been removed. Reason: {reason}")
            except nextcord.HTTPException:
                await ctx.send("Failed to send a direct message to the member.", ephemeral=True)

        except nextcord.Forbidden:
            await ctx.send("I don't have permission to remove timeout from this member.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
    #=============================================================================================================================================================