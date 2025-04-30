import nextcord
from nextcord.ext import commands


class LockUnlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = bot.error_handler

    # LOCK CHANNEL COMMAND
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="lock", description="Prevent members from sending messages in a channel")
    async def lock(
        self, 
        interaction: nextcord.Interaction, 
        channel: nextcord.TextChannel = nextcord.SlashOption(
            description="The channel to lock (defaults to current channel if not specified)",
            required=False
        ),
        reason: str = nextcord.SlashOption(
            description="Reason for locking the channel (optional)",
            required=False
        )
    ):
        try:
            # Use current channel if none specified
            if not channel:
                channel = interaction.channel
                
            # Permission check for user
            if not interaction.user.guild_permissions.manage_channels:
                embed = nextcord.Embed(
                    title="⚠️ Missing Permissions",
                    description="You need the **Manage Channels** permission to use this command.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Permission check for bot
            if not interaction.guild.me.guild_permissions.manage_channels:
                embed = nextcord.Embed(
                    title="⚠️ Bot Missing Permissions",
                    description="I need the **Manage Channels** permission to lock channels.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Check if channel is already locked
            current_perms = channel.permissions_for(interaction.guild.default_role)
            if not current_perms.send_messages:
                embed = nextcord.Embed(
                    title="ℹ️ Channel Already Locked",
                    description=f"{channel.mention} is already locked for regular members.",
                    color=nextcord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Process the reason
            audit_reason = f"Locked by {interaction.user} ({interaction.user.id})"
            if reason:
                audit_reason += f": {reason}"
                display_reason = reason
            else:
                display_reason = "No reason provided"
                
            # Lock the channel
            await interaction.response.defer(ephemeral=False)
            await channel.set_permissions(
                interaction.guild.default_role, 
                send_messages=False, 
                reason=audit_reason
            )
            
            # Create confirmation embed
            embed = nextcord.Embed(
                title="🔒 Channel Locked",
                description=f"{channel.mention} has been locked. Members cannot send messages until it is unlocked.",
                color=nextcord.Color.red()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Reason", value=display_reason, inline=True)
            embed.add_field(
                name="Unlock Command", 
                value=f"Use `/unlock {channel.mention}` to restore messaging permissions.", 
                inline=False
            )
            
            # Send confirmation
            await interaction.followup.send(embed=embed)
            
            # Optional: Send a message to the locked channel if it's not the current channel
            if channel.id != interaction.channel.id:
                channel_notice = nextcord.Embed(
                    title="🔒 Channel Locked",
                    description=f"This channel has been locked by {interaction.user.mention}.\nMembers cannot send messages until a moderator unlocks it.",
                    color=nextcord.Color.red()
                )
                if reason:
                    channel_notice.add_field(name="Reason", value=reason, inline=False)
                    
                await channel.send(embed=channel_notice)
                
        except nextcord.Forbidden:
            embed = nextcord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to manage this channel's permissions. Please check my role settings.",
                color=nextcord.Color.red()
            )
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            # Let the global error handler handle other exceptions
            if not interaction.response.is_done():
                await self.error_handler.handle_command_error(interaction, e, "lock")
            else:
                await self.error_handler.handle_command_error(interaction, e, "lock", is_followup=True)
    
    # UNLOCK CHANNEL COMMAND
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="unlock", description="Allow members to send messages in a locked channel")
    async def unlock(
        self, 
        interaction: nextcord.Interaction, 
        channel: nextcord.TextChannel = nextcord.SlashOption(
            description="The channel to unlock (defaults to current channel if not specified)",
            required=False
        ),
        reason: str = nextcord.SlashOption(
            description="Reason for unlocking the channel (optional)",
            required=False
        )
    ):
        try:
            # Use current channel if none specified
            if not channel:
                channel = interaction.channel
                
            # Permission check for user
            if not interaction.user.guild_permissions.manage_channels:
                embed = nextcord.Embed(
                    title="⚠️ Missing Permissions",
                    description="You need the **Manage Channels** permission to use this command.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Permission check for bot
            if not interaction.guild.me.guild_permissions.manage_channels:
                embed = nextcord.Embed(
                    title="⚠️ Bot Missing Permissions",
                    description="I need the **Manage Channels** permission to unlock channels.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Check if channel is already unlocked
            current_perms = channel.permissions_for(interaction.guild.default_role)
            if current_perms.send_messages:
                embed = nextcord.Embed(
                    title="ℹ️ Channel Already Unlocked",
                    description=f"{channel.mention} is already unlocked for regular members.",
                    color=nextcord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Process the reason
            audit_reason = f"Unlocked by {interaction.user} ({interaction.user.id})"
            if reason:
                audit_reason += f": {reason}"
                display_reason = reason
            else:
                display_reason = "No reason provided"
                
            # Unlock the channel
            await interaction.response.defer(ephemeral=False)
            await channel.set_permissions(
                interaction.guild.default_role, 
                send_messages=True, 
                reason=audit_reason
            )
            
            # Create confirmation embed
            embed = nextcord.Embed(
                title="🔓 Channel Unlocked",
                description=f"{channel.mention} has been unlocked. Members can now send messages again.",
                color=nextcord.Color.green()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Reason", value=display_reason, inline=True)
            
            # Send confirmation
            await interaction.followup.send(embed=embed)
            
            # Optional: Send a message to the unlocked channel if it's not the current channel
            if channel.id != interaction.channel.id:
                channel_notice = nextcord.Embed(
                    title="🔓 Channel Unlocked",
                    description=f"This channel has been unlocked by {interaction.user.mention}.\nYou can now send messages again.",
                    color=nextcord.Color.green()
                )
                if reason:
                    channel_notice.add_field(name="Reason", value=reason, inline=False)
                    
                await channel.send(embed=channel_notice)
                
        except nextcord.Forbidden:
            embed = nextcord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to manage this channel's permissions. Please check my role settings.",
                color=nextcord.Color.red()
            )
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            # Let the global error handler handle other exceptions
            if not interaction.response.is_done():
                await self.error_handler.handle_command_error(interaction, e, "unlock")
            else:
                await self.error_handler.handle_command_error(interaction, e, "unlock", is_followup=True)
    #=============================================================================================================================================================