import nextcord
from nextcord.ext import commands, tasks
import asyncio
import re
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional


class MuteSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = getattr(bot, 'error_handler', None)
        # Dictionary to store temporary mutes: {guild_id: {member_id: expiry_timestamp}}
        self.temp_mutes: Dict[int, Dict[int, float]] = {}
        # Start the background task to check for expired mutes
        self.check_temp_mutes.start()
        
    def cog_unload(self):
        # Stop the background task when cog is unloaded
        self.check_temp_mutes.cancel()
        
    @tasks.loop(seconds=10)
    async def check_temp_mutes(self):
        """Background task to check for and remove expired temporary mutes"""
        current_time = time.time()
        
        # For each guild that has temporary mutes
        for guild_id in list(self.temp_mutes.keys()):
            guild = self.bot.get_guild(guild_id)
            if not guild:
                # Guild no longer accessible, remove it from tracking
                del self.temp_mutes[guild_id]
                continue
                
            # For each member with a temporary mute in this guild
            for member_id, expiry_time in list(self.temp_mutes[guild_id].items()):
                if current_time >= expiry_time:
                    # Mute has expired, attempt to unmute
                    member = guild.get_member(member_id)
                    if member and member.voice and member.voice.mute:
                        try:
                            await member.edit(mute=False)
                            # Remove from tracking
                            del self.temp_mutes[guild_id][member_id]
                            
                            # Send notification to system channel if available
                            if guild.system_channel:
                                embed = nextcord.Embed(
                                    title="🔊 Temporary Mute Expired",
                                    description=f"{member.mention}'s voice mute has expired and has been automatically removed.",
                                    color=nextcord.Color.green()
                                )
                                embed.set_footer(text=f"Member ID: {member.id}")
                                await guild.system_channel.send(embed=embed)
                        except Exception:
                            # If we can't unmute, we'll try again next cycle
                            pass
                    else:
                        # Member no longer in voice or no longer muted, remove from tracking
                        if member_id in self.temp_mutes[guild_id]:
                            del self.temp_mutes[guild_id][member_id]
            
            # Clean up empty guild entries
            if not self.temp_mutes[guild_id]:
                del self.temp_mutes[guild_id]
    
    @check_temp_mutes.before_loop
    async def before_temp_mutes_check(self):
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
    # SERVER MUTE COMMAND
    @nextcord.slash_command(
        name="mute", 
        description="Server mute a member or all members in your voice channel"
    )
    async def mute(
        self, 
        interaction: nextcord.Interaction, 
        member: nextcord.Member = nextcord.SlashOption(
            description="The member to mute (leave empty to mute everyone in your voice channel)",
            required=False
        ),
        duration: str = nextcord.SlashOption(
            description="Duration of the mute (e.g., 30s, 5m, 1h, 1d)",
            required=False
        )
    ):
        """
        Server mutes a specific member or all members in the voice channel, with optional duration.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        member: Optional - The specific member to mute. If not provided, mutes all members in the user's voice channel.
        duration: Optional - Duration for the mute (e.g., 30s, 5m, 1h, 1d)
        """
        try:
            # Check if user has permission to mute members
            if not interaction.user.guild_permissions.mute_members:
                embed = nextcord.Embed(
                    title="⚠️ Missing Permissions",
                    description="You need the **Mute Members** permission to use this command.",
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
                    
            # Case 1: Mute a specific member
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
                
                # Check if the member is already muted
                if member.voice.mute:
                    embed = nextcord.Embed(
                        title="ℹ️ Already Muted",
                        description=f"{member.display_name} is already server muted.",
                        color=nextcord.Color.blue()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                    
                await member.edit(mute=True)
                
                # If duration was provided, add to temp mutes
                duration_text = ""
                if duration_seconds:
                    expiry_time = time.time() + duration_seconds
                    
                    # Initialize guild dict if it doesn't exist
                    if interaction.guild.id not in self.temp_mutes:
                        self.temp_mutes[interaction.guild.id] = {}
                        
                    # Add member to temp mutes
                    self.temp_mutes[interaction.guild.id][member.id] = expiry_time
                    
                    # Format duration for display
                    duration_text = f" for {self.format_time_remaining(expiry_time)}"
                
                embed = nextcord.Embed(
                    title="🔇 Member Muted",
                    description=f"{member.mention} has been server muted{duration_text}.",
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
            
            # Case 2: Mute all members in user's voice channel
            else:
                # Check if user is in a voice channel
                if not interaction.user.voice:
                    embed = nextcord.Embed(
                        title="❌ Action Failed",
                        description="You need to be in a voice channel to mute all members.",
                        color=nextcord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                voice_channel = interaction.user.voice.channel
                muted_count = 0
                already_muted = 0
                
                # Mute all members in the channel
                for channel_member in voice_channel.members:
                    if channel_member.id != interaction.user.id:  # Skip the command user
                        if not channel_member.voice.mute:
                            await channel_member.edit(mute=True)
                            muted_count += 1
                            
                            # If duration was provided, add to temp mutes
                            if duration_seconds:
                                expiry_time = time.time() + duration_seconds
                                
                                # Initialize guild dict if it doesn't exist
                                if interaction.guild.id not in self.temp_mutes:
                                    self.temp_mutes[interaction.guild.id] = {}
                                    
                                # Add member to temp mutes
                                self.temp_mutes[interaction.guild.id][channel_member.id] = expiry_time
                        else:
                            already_muted += 1
                
                # Duration text for display
                duration_text = ""
                if duration_seconds:
                    expiry_time = time.time() + duration_seconds
                    duration_text = f" for {self.format_time_remaining(expiry_time)}"
                
                # Provide feedback with counts
                if muted_count > 0:
                    embed = nextcord.Embed(
                        title="🔇 Channel Muted",
                        description=f"Voice channel {voice_channel.mention} has been server muted{duration_text}.",
                        color=nextcord.Color.red()
                    )
                    embed.add_field(name="Channel", value=voice_channel.name, inline=True)
                    embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
                    embed.add_field(name="Members Muted", value=f"{muted_count} member{'s' if muted_count != 1 else ''}", inline=True)
                    
                    if already_muted > 0:
                        embed.add_field(
                            name="Note", 
                            value=f"{already_muted} member{'s were' if already_muted != 1 else ' was'} already muted.",
                            inline=False
                        )
                        
                    if duration_seconds:
                        expiry_time_str = datetime.fromtimestamp(time.time() + duration_seconds).strftime("%Y-%m-%d %H:%M:%S UTC")
                        embed.add_field(name="Expires", value=expiry_time_str, inline=False)
                    
                    await interaction.response.send_message(embed=embed)
                else:
                    embed = nextcord.Embed(
                        title="ℹ️ Already Muted",
                        description=f"All members in {voice_channel.name} were already server muted.",
                        color=nextcord.Color.blue()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    
        except nextcord.Forbidden:
            embed = nextcord.Embed(
                title="❌ Action Failed",
                description="I don't have permission to mute members. Please check my role permissions.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            # Handle errors even if error_handler is not available
            if self.error_handler:
                await self.error_handler.handle_command_error(interaction, e, "mute")
            else:
                # Basic error handling if no error_handler is available
                embed = nextcord.Embed(
                    title="❌ Something Went Wrong",
                    description=f"There was an error while trying to mute: `{str(e)}`",
                    color=nextcord.Color.red()
                )
                embed.add_field(name="Need help?", value="If this issue persists, please contact the bot developer.", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
    #=============================================================================================================================================================
    # UNMUTE COMMAND
    @nextcord.slash_command(
        name="unmute", 
        description="Remove server mute from a member or all members in your voice channel"
    )
    async def unmute(
        self, 
        interaction: nextcord.Interaction, 
        member: nextcord.Member = nextcord.SlashOption(
            description="The member to unmute (leave empty to unmute everyone in your voice channel)",
            required=False
        )
    ):
        """
        Unmutes a specific member or all members in the voice channel.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        member: Optional - The specific member to unmute. If not provided, unmutes all members in the user's voice channel.
        """
        try:
            # Check if user has permission to mute members
            if not interaction.user.guild_permissions.mute_members:
                embed = nextcord.Embed(
                    title="⚠️ Missing Permissions",
                    description="You need the **Mute Members** permission to use this command.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Case 1: Unmute a specific member
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
                
                # Check if the member is already unmuted
                if not member.voice.mute:
                    embed = nextcord.Embed(
                        title="ℹ️ Already Unmuted",
                        description=f"{member.display_name} is not server muted.",
                        color=nextcord.Color.blue()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                    
                await member.edit(mute=False)
                
                # Remove from temp mutes if present
                if interaction.guild.id in self.temp_mutes and member.id in self.temp_mutes[interaction.guild.id]:
                    del self.temp_mutes[interaction.guild.id][member.id]
                    # Clean up empty guild entries
                    if not self.temp_mutes[interaction.guild.id]:
                        del self.temp_mutes[interaction.guild.id]
                
                embed = nextcord.Embed(
                    title="🔊 Member Unmuted",
                    description=f"{member.mention} has been server unmuted.",
                    color=nextcord.Color.green()
                )
                embed.add_field(name="Member", value=f"{member.name} (`{member.id}`)", inline=True)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
                
                # Add member avatar if available
                if member.avatar:
                    embed.set_thumbnail(url=member.avatar.url)
                    
                await interaction.response.send_message(embed=embed)
            
            # Case 2: Unmute all members in user's voice channel
            else:
                # Check if user is in a voice channel
                if not interaction.user.voice:
                    embed = nextcord.Embed(
                        title="❌ Action Failed",
                        description="You need to be in a voice channel to unmute all members.",
                        color=nextcord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                voice_channel = interaction.user.voice.channel
                unmuted_count = 0
                already_unmuted = 0
                
                # Unmute all members in the channel
                for channel_member in voice_channel.members:
                    if channel_member.voice.mute:
                        await channel_member.edit(mute=False)
                        unmuted_count += 1
                        
                        # Remove from temp mutes if present
                        if interaction.guild.id in self.temp_mutes and channel_member.id in self.temp_mutes[interaction.guild.id]:
                            del self.temp_mutes[interaction.guild.id][channel_member.id]
                    else:
                        already_unmuted += 1
                
                # Clean up empty guild entries
                if interaction.guild.id in self.temp_mutes and not self.temp_mutes[interaction.guild.id]:
                    del self.temp_mutes[interaction.guild.id]
                
                # Provide feedback with counts
                if unmuted_count > 0:
                    embed = nextcord.Embed(
                        title="🔊 Channel Unmuted",
                        description=f"Voice channel {voice_channel.mention} has been server unmuted.",
                        color=nextcord.Color.green()
                    )
                    embed.add_field(name="Channel", value=voice_channel.name, inline=True)
                    embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
                    embed.add_field(name="Members Unmuted", value=f"{unmuted_count} member{'s' if unmuted_count != 1 else ''}", inline=True)
                    
                    if already_unmuted > 0:
                        embed.add_field(
                            name="Note", 
                            value=f"{already_unmuted} member{'s were' if already_unmuted != 1 else ' was'} already unmuted.",
                            inline=False
                        )
                    
                    await interaction.response.send_message(embed=embed)
                else:
                    embed = nextcord.Embed(
                        title="ℹ️ Already Unmuted",
                        description=f"All members in {voice_channel.name} were already unmuted.",
                        color=nextcord.Color.blue()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    
        except nextcord.Forbidden:
            embed = nextcord.Embed(
                title="❌ Action Failed",
                description="I don't have permission to unmute members. Please check my role permissions.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            # Handle errors even if error_handler is not available
            if self.error_handler:
                await self.error_handler.handle_command_error(interaction, e, "unmute")
            else:
                # Basic error handling if no error_handler is available
                embed = nextcord.Embed(
                    title="❌ Something Went Wrong",
                    description=f"There was an error while trying to unmute: `{str(e)}`",
                    color=nextcord.Color.red()
                )
                embed.add_field(name="Need help?", value="If this issue persists, please contact the bot developer.", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
    #=============================================================================================================================================================
    # SOFTMUTE COMMAND (MICROPHONE MUTE)
    @nextcord.slash_command(
        name="softmute", 
        description="Mute a member's microphone without server muting them"
    )
    async def softmute(
        self, 
        interaction: nextcord.Interaction, 
        member: nextcord.Member = nextcord.SlashOption(
            description="The member whose microphone to mute",
            required=True
        )
    ):
        """
        Mutes a member's microphone without server muting them.
        This is a client-side mute that only affects the current voice session.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        member: The member whose microphone to mute
        """
        try:
            # Check if user has permission to mute members
            if not interaction.user.guild_permissions.mute_members:
                embed = nextcord.Embed(
                    title="⚠️ Missing Permissions",
                    description="You need the **Mute Members** permission to use this command.",
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
            
            # Check if the member is already softmuted
            if member.voice.self_mute:
                embed = nextcord.Embed(
                    title="ℹ️ Already Muted",
                    description=f"{member.display_name}'s microphone is already muted.",
                    color=nextcord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Mute the member's microphone
            # Note: This is a client-side action and might not work for all users
            # as Discord does not provide a direct way to mute someone's microphone server-side
            await member.edit(mute=False, deafen=False)
            
            # Send command to client to mute microphone
            embed = nextcord.Embed(
                title="🎙️ Microphone Muted",
                description=f"{member.mention}'s microphone has been muted. This is a client-side mute that only affects the current voice session.",
                color=nextcord.Color.gold()
            )
            embed.add_field(name="Member", value=f"{member.name} (`{member.id}`)", inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(
                name="Note", 
                value="This mute is client-side and temporary. The member can unmute themselves, and the mute will be removed if they leave and rejoin the voice channel.",
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
                await self.error_handler.handle_command_error(interaction, e, "softmute")
            else:
                # Basic error handling if no error_handler is available
                embed = nextcord.Embed(
                    title="❌ Something Went Wrong",
                    description=f"There was an error while trying to softmute: `{str(e)}`",
                    color=nextcord.Color.red()
                )
                embed.add_field(name="Need help?", value="If this issue persists, please contact the bot developer.", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
    #=============================================================================================================================================================
    # COMMAND TO CHECK MUTE STATUS
    @nextcord.slash_command(
        name="mutestatus", 
        description="Check if a member is muted and for how long"
    )
    async def mutestatus(
        self, 
        interaction: nextcord.Interaction, 
        member: nextcord.Member = nextcord.SlashOption(
            description="The member to check",
            required=True
        )
    ):
        """
        Checks if a member is muted and for how long.
        
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
                
            # Check mute status
            embed = nextcord.Embed(
                title="🔊 Voice Status",
                description=f"Voice status for {member.mention}",
                color=nextcord.Color.blue()
            )
            
            # Add member info
            embed.add_field(name="Member", value=f"{member.name} (`{member.id}`)", inline=True)
            embed.add_field(name="Voice Channel", value=member.voice.channel.name, inline=True)
            
            # Check server mute status
            if member.voice.mute:
                embed.add_field(name="Server Muted", value="Yes", inline=True)
                
                # Check if there's a temporary mute
                if (interaction.guild.id in self.temp_mutes and 
                    member.id in self.temp_mutes[interaction.guild.id]):
                    expiry_time = self.temp_mutes[interaction.guild.id][member.id]
                    time_remaining = self.format_time_remaining(expiry_time)
                    expiry_time_str = datetime.fromtimestamp(expiry_time).strftime("%Y-%m-%d %H:%M:%S UTC")
                    
                    embed.add_field(name="Mute Type", value="Temporary", inline=True)
                    embed.add_field(name="Time Remaining", value=time_remaining, inline=True)
                    embed.add_field(name="Expires At", value=expiry_time_str, inline=True)
                else:
                    embed.add_field(name="Mute Type", value="Permanent", inline=True)
            else:
                embed.add_field(name="Server Muted", value="No", inline=True)
                
            # Check self mute status (microphone)
            embed.add_field(name="Microphone Muted", value="Yes" if member.voice.self_mute else "No", inline=True)
            
            # Check deaf status
            embed.add_field(name="Server Deafened", value="Yes" if member.voice.deaf else "No", inline=True)
            embed.add_field(name="Self Deafened", value="Yes" if member.voice.self_deaf else "No", inline=True)
            
            # Add member avatar if available
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
                
            await interaction.response.send_message(embed=embed)
                
        except Exception as e:
            # Handle errors even if error_handler is not available
            if self.error_handler:
                await self.error_handler.handle_command_error(interaction, e, "mutestatus")
            else:
                # Basic error handling if no error_handler is available
                embed = nextcord.Embed(
                    title="❌ Something Went Wrong",
                    description=f"There was an error while checking mute status: `{str(e)}`",
                    color=nextcord.Color.red()
                )
                embed.add_field(name="Need help?", value="If this issue persists, please contact the bot developer.", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
    #=============================================================================================================================================================