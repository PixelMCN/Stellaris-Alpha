import nextcord
from nextcord.ext import commands, tasks
import asyncio
import re
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional


class DeafenSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = getattr(bot, 'error_handler', None)
        # Dictionary to store temporary deafens: {guild_id: {member_id: expiry_timestamp}}
        self.temp_deafens: Dict[int, Dict[int, float]] = {}
        # Start the background task to check for expired deafens
        self.check_temp_deafens.start()
        
    def cog_unload(self):
        # Stop the background task when cog is unloaded
        self.check_temp_deafens.cancel()
        
    @tasks.loop(seconds=10)
    async def check_temp_deafens(self):
        """Background task to check for and remove expired temporary deafens"""
        current_time = time.time()
        
        # For each guild that has temporary deafens
        for guild_id in list(self.temp_deafens.keys()):
            guild = self.bot.get_guild(guild_id)
            if not guild:
                # Guild no longer accessible, remove it from tracking
                del self.temp_deafens[guild_id]
                continue
                
            # For each member with a temporary deafen in this guild
            for member_id, expiry_time in list(self.temp_deafens[guild_id].items()):
                if current_time >= expiry_time:
                    # Deafen has expired, attempt to undeafen
                    member = guild.get_member(member_id)
                    if member and member.voice and member.voice.deaf:
                        try:
                            await member.edit(deafen=False)
                            # Remove from tracking
                            del self.temp_deafens[guild_id][member_id]
                            
                            # Send notification to system channel if available
                            if guild.system_channel:
                                embed = nextcord.Embed(
                                    title="🔊 Temporary Deafen Expired",
                                    description=f"{member.mention}'s voice deafen has expired and has been automatically removed.",
                                    color=nextcord.Color.green()
                                )
                                embed.set_footer(text=f"Member ID: {member.id}")
                                await guild.system_channel.send(embed=embed)
                        except Exception:
                            # If we can't undeafen, we'll try again next cycle
                            pass
                    else:
                        # Member no longer in voice or no longer deafened, remove from tracking
                        if member_id in self.temp_deafens[guild_id]:
                            del self.temp_deafens[guild_id][member_id]
            
            # Clean up empty guild entries
            if not self.temp_deafens[guild_id]:
                del self.temp_deafens[guild_id]
    
    @check_temp_deafens.before_loop
    async def before_temp_deafens_check(self):
        """Wait until the bot is ready before starting the background task"""
        await self.bot.wait_until_ready()
        
    def parse_time(self, time_str: str) -> Optional[int]:
        """
        Parse a time string like "10s", "5m", "1h", "2d" into seconds
        Returns None if the format is invalid
        """
        if not time_str:
            return None
            
        # Regular expression to match a number followed by a time unit
        match = re.match(r'^(\d+)([smhd])$', time_str.lower())
        if not match:
            return None
            
        value, unit = match.groups()
        value = int(value)
        
        if unit == 's':
            return value
        elif unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
        elif unit == 'd':
            return value * 86400
        return None
        
    def format_time_remaining(self, expiry_time: float) -> str:
        """Format the remaining time until expiry in a human-readable way"""
        seconds_remaining = int(expiry_time - time.time())
        if seconds_remaining <= 0:
            return "0 seconds"
            
        days, remainder = divmod(seconds_remaining, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 and not parts:  # Only show seconds if there are no larger units
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
            
        return ", ".join(parts)

    #=============================================================================================================================================================
    # SERVER DEAFEN COMMAND
    @nextcord.slash_command(
        name="deafen", 
        description="Server deafen a member or all members in your voice channel"
    )
    async def deafen(
        self, 
        interaction: nextcord.Interaction, 
        member: nextcord.Member = nextcord.SlashOption(
            description="The member to deafen (leave empty to deafen everyone in your voice channel)",
            required=False
        ),
        duration: str = nextcord.SlashOption(
            description="Duration of the deafen (e.g., 30s, 5m, 1h, 1d)",
            required=False
        )
    ):
        """
        Server deafens a specific member or all members in the voice channel, with optional duration.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        member: Optional - The specific member to deafen. If not provided, deafens all members in the user's voice channel.
        duration: Optional - Duration for the deafen (e.g., 30s, 5m, 1h, 1d)
        """
        try:
            # Check if user has permission to deafen members
            if not interaction.user.guild_permissions.deafen_members:
                embed = nextcord.Embed(
                    title="⚠️ Missing Permissions",
                    description="You need the **Deafen Members** permission to use this command.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Parse duration if provided
            duration_seconds = None
            if duration:
                duration_seconds = self.parse_time(duration)
                if duration_seconds is None:
                    embed = nextcord.Embed(
                        title="⚠️ Invalid Duration",
                        description="Duration must be in the format: `<number><unit>` where unit is `s` (seconds), `m` (minutes), `h` (hours), or `d` (days).\nExample: `30s`, `5m`, `1h`, `1d`",
                        color=nextcord.Color.yellow()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                    
            # Case 1: Deafen a specific member
            if member:
                # Check if member is in a voice channel
                if not member.voice:
                    embed = nextcord.Embed(
                        title="❌ Action Failed",
                        description=f"{member.display_name} is not in a voice channel.",
                        color=nextcord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                # Check if the member is already deafened
                if member.voice.deaf:
                    embed = nextcord.Embed(
                        title="ℹ️ Already Deafened",
                        description=f"{member.display_name} is already server deafened.",
                        color=nextcord.Color.blue()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                    
                await member.edit(deafen=True)
                
                # If duration was provided, add to temp deafens
                duration_text = ""
                if duration_seconds:
                    expiry_time = time.time() + duration_seconds
                    
                    # Initialize guild dict if it doesn't exist
                    if interaction.guild.id not in self.temp_deafens:
                        self.temp_deafens[interaction.guild.id] = {}
                        
                    # Add member to temp deafens
                    self.temp_deafens[interaction.guild.id][member.id] = expiry_time
                    
                    # Format duration for display
                    duration_text = f" for {self.format_time_remaining(expiry_time)}"
                
                embed = nextcord.Embed(
                    title="🔇 Member Deafened",
                    description=f"{member.mention} has been server deafened{duration_text}.",
                    color=nextcord.Color.red()
                )
                embed.add_field(name="Member", value=f"{member.name} (`{member.id}`)", inline=True)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
                
                if duration_seconds:
                    expiry_time_str = datetime.fromtimestamp(time.time() + duration_seconds).strftime("%Y-%m-%d %H:%M:%S UTC")
                    embed.add_field(name="Expires", value=expiry_time_str, inline=False)
                
                # Add member avatar if available
                if member.avatar:
                    embed.set_thumbnail(url=member.avatar.url)
                    
                await interaction.response.send_message(embed=embed)
            
            # Case 2: Deafen all members in user's voice channel
            else:
                # Check if user is in a voice channel
                if not interaction.user.voice:
                    embed = nextcord.Embed(
                        title="❌ Action Failed",
                        description="You need to be in a voice channel to deafen all members.",
                        color=nextcord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                voice_channel = interaction.user.voice.channel
                deafened_count = 0
                already_deafened = 0
                
                # Deafen all members in the channel
                for channel_member in voice_channel.members:
                    if channel_member.id != interaction.user.id:  # Skip the command user
                        if not channel_member.voice.deaf:
                            await channel_member.edit(deafen=True)
                            deafened_count += 1
                            
                            # If duration was provided, add to temp deafens
                            if duration_seconds:
                                expiry_time = time.time() + duration_seconds
                                
                                # Initialize guild dict if it doesn't exist
                                if interaction.guild.id not in self.temp_deafens:
                                    self.temp_deafens[interaction.guild.id] = {}
                                    
                                # Add member to temp deafens
                                self.temp_deafens[interaction.guild.id][channel_member.id] = expiry_time
                        else:
                            already_deafened += 1
                
                # Duration text for display
                duration_text = ""
                if duration_seconds:
                    expiry_time = time.time() + duration_seconds
                    duration_text = f" for {self.format_time_remaining(expiry_time)}"
                
                # Provide feedback with counts
                if deafened_count > 0:
                    embed = nextcord.Embed(
                        title="🔇 Channel Deafened",
                        description=f"Voice channel {voice_channel.mention} has been server deafened{duration_text}.",
                        color=nextcord.Color.red()
                    )
                    embed.add_field(name="Channel", value=voice_channel.name, inline=True)
                    embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
                    embed.add_field(name="Members Deafened", value=f"{deafened_count} member{'s' if deafened_count != 1 else ''}", inline=True)
                    
                    if already_deafened > 0:
                        embed.add_field(
                            name="Note", 
                            value=f"{already_deafened} member{'s were' if already_deafened != 1 else ' was'} already deafened.",
                            inline=False
                        )
                        
                    if duration_seconds:
                        expiry_time_str = datetime.fromtimestamp(time.time() + duration_seconds).strftime("%Y-%m-%d %H:%M:%S UTC")
                        embed.add_field(name="Expires", value=expiry_time_str, inline=False)
                    
                    await interaction.response.send_message(embed=embed)
                else:
                    embed = nextcord.Embed(
                        title="ℹ️ Already Deafened",
                        description=f"All members in {voice_channel.name} were already server deafened.",
                        color=nextcord.Color.blue()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    
        except nextcord.Forbidden:
            embed = nextcord.Embed(
                title="❌ Action Failed",
                description="I don't have permission to deafen members. Please check my role permissions.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            # Handle errors even if error_handler is not available
            if self.error_handler:
                await self.error_handler.handle_command_error(interaction, e, "deafen")
            else:
                # Basic error handling if no error_handler is available
                embed = nextcord.Embed(
                    title="❌ Something Went Wrong",
                    description=f"There was an error while trying to deafen: `{str(e)}`",
                    color=nextcord.Color.red()
                )
                embed.add_field(name="Need help?", value="If this issue persists, please contact the bot developer.", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
    #=============================================================================================================================================================
    # UNDEAFEN COMMAND
    @nextcord.slash_command(
        name="undeafen", 
        description="Remove server deafen from a member or all members in your voice channel"
    )
    async def undeafen(
        self, 
        interaction: nextcord.Interaction, 
        member: nextcord.Member = nextcord.SlashOption(
            description="The member to undeafen (leave empty to undeafen everyone in your voice channel)",
            required=False
        )
    ):
        """
        Undeafens a specific member or all members in the voice channel.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        member: Optional - The specific member to undeafen. If not provided, undeafens all members in the user's voice channel.
        """
        try:
            # Check if user has permission to deafen members
            if not interaction.user.guild_permissions.deafen_members:
                embed = nextcord.Embed(
                    title="⚠️ Missing Permissions",
                    description="You need the **Deafen Members** permission to use this command.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Case 1: Undeafen a specific member
            if member:
                # Check if member is in a voice channel
                if not member.voice:
                    embed = nextcord.Embed(
                        title="❌ Action Failed",
                        description=f"{member.display_name} is not in a voice channel.",
                        color=nextcord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                # Check if the member is already undeafened
                if not member.voice.deaf:
                    embed = nextcord.Embed(
                        title="ℹ️ Already Undeafened",
                        description=f"{member.display_name} is not server deafened.",
                        color=nextcord.Color.blue()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                    
                await member.edit(deafen=False)
                
                # Remove from temp deafens if present
                if interaction.guild.id in self.temp_deafens and member.id in self.temp_deafens[interaction.guild.id]:
                    del self.temp_deafens[interaction.guild.id][member.id]
                    # Clean up empty guild entries
                    if not self.temp_deafens[interaction.guild.id]:
                        del self.temp_deafens[interaction.guild.id]
                
                embed = nextcord.Embed(
                    title="🔊 Member Undeafened",
                    description=f"{member.mention} has been server undeafened.",
                    color=nextcord.Color.green()
                )
                embed.add_field(name="Member", value=f"{member.name} (`{member.id}`)", inline=True)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
                
                # Add member avatar if available
                if member.avatar:
                    embed.set_thumbnail(url=member.avatar.url)
                    
                await interaction.response.send_message(embed=embed)
            
            # Case 2: Undeafen all members in user's voice channel
            else:
                # Check if user is in a voice channel
                if not interaction.user.voice:
                    embed = nextcord.Embed(
                        title="❌ Action Failed",
                        description="You need to be in a voice channel to undeafen all members.",
                        color=nextcord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                voice_channel = interaction.user.voice.channel
                undeafened_count = 0
                already_undeafened = 0
                
                # Undeafen all members in the channel
                for channel_member in voice_channel.members:
                    if channel_member.voice.deaf:
                        await channel_member.edit(deafen=False)
                        undeafened_count += 1
                        
                        # Remove from temp deafens if present
                        if interaction.guild.id in self.temp_deafens and channel_member.id in self.temp_deafens[interaction.guild.id]:
                            del self.temp_deafens[interaction.guild.id][channel_member.id]
                    else:
                        already_undeafened += 1
                
                # Clean up empty guild entries
                if interaction.guild.id in self.temp_deafens and not self.temp_deafens[interaction.guild.id]:
                    del self.temp_deafens[interaction.guild.id]
                
                # Provide feedback with counts
                if undeafened_count > 0:
                    embed = nextcord.Embed(
                        title="🔊 Channel Undeafened",
                        description=f"Voice channel {voice_channel.mention} has been server undeafened.",
                        color=nextcord.Color.green()
                    )
                    embed.add_field(name="Channel", value=voice_channel.name, inline=True)
                    embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
                    embed.add_field(name="Members Undeafened", value=f"{undeafened_count} member{'s' if undeafened_count != 1 else ''}", inline=True)
                    
                    if already_undeafened > 0:
                        embed.add_field(
                            name="Note", 
                            value=f"{already_undeafened} member{'s were' if already_undeafened != 1 else ' was'} already undeafened.",
                            inline=False
                        )
                    
                    await interaction.response.send_message(embed=embed)
                else:
                    embed = nextcord.Embed(
                        title="ℹ️ Already Undeafened",
                        description=f"All members in {voice_channel.name} were already undeafened.",
                        color=nextcord.Color.blue()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    
        except nextcord.Forbidden:
            embed = nextcord.Embed(
                title="❌ Action Failed",
                description="I don't have permission to undeafen members. Please check my role permissions.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            # Handle errors even if error_handler is not available
            if self.error_handler:
                await self.error_handler.handle_command_error(interaction, e, "undeafen")
            else:
                # Basic error handling if no error_handler is available
                embed = nextcord.Embed(
                    title="❌ Something Went Wrong",
                    description=f"There was an error while trying to undeafen: `{str(e)}`",
                    color=nextcord.Color.red()
                )
                embed.add_field(name="Need help?", value="If this issue persists, please contact the bot developer.", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
    #=============================================================================================================================================================
    # SOFTDEAFEN COMMAND (HEADPHONE DEAFEN)
    @nextcord.slash_command(
        name="softdeafen", 
        description="Deafen a member's headphones without server deafening them"
    )
    async def softdeafen(
        self, 
        interaction: nextcord.Interaction, 
        member: nextcord.Member = nextcord.SlashOption(
            description="The member whose headphones to deafen",
            required=True
        )
    ):
        """
        Deafens a member's headphones without server deafening them.
        This is a client-side deafen that only affects the current voice session.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        member: The member whose headphones to deafen
        """
        try:
            # Check if user has permission to deafen members
            if not interaction.user.guild_permissions.deafen_members:
                embed = nextcord.Embed(
                    title="⚠️ Missing Permissions",
                    description="You need the **Deafen Members** permission to use this command.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Check if member is in a voice channel
            if not member.voice:
                embed = nextcord.Embed(
                    title="❌ Action Failed",
                    description=f"{member.display_name} is not in a voice channel.",
                    color=nextcord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if the member is already softdeafened
            if member.voice.self_deaf:
                embed = nextcord.Embed(
                    title="ℹ️ Already Deafened",
                    description=f"{member.display_name}'s headphones are already deafened.",
                    color=nextcord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Deafen the member's headphones
            # Note: This is a client-side action and might not work for all users
            # as Discord does not provide a direct way to deafen someone's headphones server-side
            await member.edit(deafen=False, mute=False)
            
            # Send command to client to deafen headphones
            embed = nextcord.Embed(
                title="🎧 Headphones Deafened",
                description=f"{member.mention}'s headphones have been deafened. This is a client-side deafen that only affects the current voice session.",
                color=nextcord.Color.gold()
            )
            embed.add_field(name="Member", value=f"{member.name} (`{member.id}`)", inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(
                name="Note", 
                value="This deafen is client-side and temporary. The member can undeafen themselves, and the deafen will be removed if they leave and rejoin the voice channel.",
                inline=False
            )
            
            # Add member avatar if available
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
                
            await interaction.response.send_message(embed=embed)
                
        except nextcord.Forbidden:
            embed = nextcord.Embed(
                title="❌ Action Failed",
                description="I don't have permission to manage voice states. Please check my role permissions.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            # Handle errors even if error_handler is not available
            if self.error_handler:
                await self.error_handler.handle_command_error(interaction, e, "softdeafen")
            else:
                # Basic error handling if no error_handler is available
                embed = nextcord.Embed(
                    title="❌ Something Went Wrong",
                    description=f"There was an error while trying to softdeafen: `{str(e)}`",
                    color=nextcord.Color.red()
                )
                embed.add_field(name="Need help?", value="If this issue persists, please contact the bot developer.", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
    #=============================================================================================================================================================
    # COMMAND TO CHECK DEAFEN STATUS - ENHANCEMENT TO EXISTING STATUS COMMAND
    @nextcord.slash_command(
        name="deafenstatus", 
        description="Check if a member is deafened and for how long"
    )
    async def deafenstatus(
        self, 
        interaction: nextcord.Interaction, 
        member: nextcord.Member = nextcord.SlashOption(
            description="The member to check",
            required=True
        )
    ):
        """
        Checks if a member is deafened and for how long.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        member: The member to check
        """
        try:
            # Check if member is in a voice channel
            if not member.voice:
                embed = nextcord.Embed(
                    title="ℹ️ Not in Voice",
                    description=f"{member.display_name} is not in a voice channel.",
                    color=nextcord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Check deafen status
            embed = nextcord.Embed(
                title="🔊 Voice Status",
                description=f"Voice status for {member.mention}",
                color=nextcord.Color.blue()
            )
            
            # Add member info
            embed.add_field(name="Member", value=f"{member.name} (`{member.id}`)", inline=True)
            embed.add_field(name="Voice Channel", value=member.voice.channel.name, inline=True)
            
            # Check server deafen status
            if member.voice.deaf:
                embed.add_field(name="Server Deafened", value="Yes", inline=True)
                
                # Check if there's a temporary deafen
                if (interaction.guild.id in self.temp_deafens and 
                    member.id in self.temp_deafens[interaction.guild.id]):
                    expiry_time = self.temp_deafens[interaction.guild.id][member.id]
                    time_remaining = self.format_time_remaining(expiry_time)
                    expiry_time_str = datetime.fromtimestamp(expiry_time).strftime("%Y-%m-%d %H:%M:%S UTC")
                    
                    embed.add_field(name="Deafen Type", value="Temporary", inline=True)
                    embed.add_field(name="Time Remaining", value=time_remaining, inline=True)
                    embed.add_field(name="Expires At", value=expiry_time_str, inline=True)
                else:
                    embed.add_field(name="Deafen Type", value="Permanent", inline=True)
            else:
                embed.add_field(name="Server Deafened", value="No", inline=True)
                
            # Check self deafen status (headphones)
            embed.add_field(name="Headphones Deafened", value="Yes" if member.voice.self_deaf else "No", inline=True)
            
            # Check mute status
            embed.add_field(name="Server Muted", value="Yes" if member.voice.mute else "No", inline=True)
            embed.add_field(name="Self Muted", value="Yes" if member.voice.self_mute else "No", inline=True)
            
            # Add member avatar if available
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
                
            await interaction.response.send_message(embed=embed)
                
        except Exception as e:
            # Handle errors even if error_handler is not available
            if self.error_handler:
                await self.error_handler.handle_command_error(interaction, e, "deafenstatus")
            else:
                # Basic error handling if no error_handler is available
                embed = nextcord.Embed(
                    title="❌ Something Went Wrong",
                    description=f"There was an error while checking deafen status: `{str(e)}`",
                    color=nextcord.Color.red()
                )
                embed.add_field(name="Need help?", value="If this issue persists, please contact the bot developer.", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)