import nextcord
import random
from nextcord.ext import commands
from nextcord import Interaction


class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = bot.error_handler

    # List of kick reasons
    kick_reasons = [
        "Breaking server rules",
        "Disruptive behavior",
        "Repeated violations",
        "Spamming"
    ]
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="kick", description="Remove a member from the server (they can rejoin later)")
    async def kick_slash(
        self, 
        interaction: Interaction, 
        member: nextcord.Member = nextcord.SlashOption(
            description="The member you want to kick from the server",
            required=True
        ), 
        reason: str = nextcord.SlashOption(
            description="Why the member is being kicked (optional)",
            required=False
        )
    ):
        try:
            # Check if user has kick permissions
            if not interaction.user.guild_permissions.kick_members:
                embed = nextcord.Embed(
                    title="⚠️ Missing Permissions",
                    description="You need the **Kick Members** permission to use this command.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Check if bot has kick permissions
            if not interaction.guild.me.guild_permissions.kick_members:
                embed = nextcord.Embed(
                    title="⚠️ Bot Missing Permissions",
                    description="I need the **Kick Members** permission to perform this action.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Check if the user is trying to kick someone with a higher role
            if interaction.user.top_role <= member.top_role and interaction.user.id != interaction.guild.owner_id:
                embed = nextcord.Embed(
                    title="⚠️ Role Hierarchy",
                    description=f"You cannot kick {member.mention} as they have a higher or equal role to you.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Check if the bot can kick the target member
            if interaction.guild.me.top_role <= member.top_role:
                embed = nextcord.Embed(
                    title="⚠️ Role Hierarchy Issue",
                    description=f"I cannot kick {member.mention} as they have a higher or equal role to me.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Self-kick check
            if member.id == interaction.user.id:
                embed = nextcord.Embed(
                    title="❓ Self-Kick Prevented",
                    description="You cannot kick yourself. If you want to leave the server, you can do so from the server menu.",
                    color=nextcord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Bot self-kick check
            if member.id == self.bot.user.id:
                embed = nextcord.Embed(
                    title="❓ Bot Kick Prevented",
                    description="I cannot kick myself. If you want to remove me from the server, you can do so from the server settings.",
                    color=nextcord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Use a random reason if none is provided
            if reason is None:
                reason = random.choice(self.kick_reasons)
                full_reason = f"{reason} (Auto-generated reason)"
            else:
                full_reason = reason

            # Send a direct message to the member before kicking them
            try:
                dm_embed = nextcord.Embed(
                    title=f"You've been kicked from {interaction.guild.name}",
                    description="A moderator has removed you from the server.",
                    color=nextcord.Color.orange()
                )
                dm_embed.add_field(name="Reason", value=full_reason, inline=False)
                dm_embed.add_field(
                    name="What does this mean?", 
                    value="You can still rejoin the server with a new invite link if you wish.",
                    inline=False
                )
                
                if interaction.guild.icon:
                    dm_embed.set_thumbnail(url=interaction.guild.icon.url)
                    
                await member.send(embed=dm_embed)
            except nextcord.HTTPException:
                # Note that we couldn't send a DM, but continue with the kick
                could_not_dm = True
            else:
                could_not_dm = False

            # Kick the member
            await interaction.response.defer(ephemeral=False)
            await member.kick(reason=full_reason)
            
            # Create a detailed embed for the kick
            embed = nextcord.Embed(
                title="👢 Member Kicked",
                description=f"{member.mention} has been removed from the server.",
                color=nextcord.Color.orange()
            )
            
            embed.add_field(name="Member", value=f"{member.name} (`{member.id}`)", inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Reason", value=full_reason, inline=False)
            
            if could_not_dm:
                embed.add_field(
                    name="Note", 
                    value="I wasn't able to send this member a DM about their kick.",
                    inline=False
                )
                
            # Add member avatar if available
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
                
            await interaction.followup.send(embed=embed)
                
        except nextcord.Forbidden:
            embed = nextcord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to kick that member. This may be due to role hierarchy.",
                color=nextcord.Color.red()
            )
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            # Let the global error handler handle other exceptions
            if not interaction.response.is_done():
                await self.error_handler.handle_command_error(interaction, e, "kick")
            else:
                await self.error_handler.handle_command_error(interaction, e, "kick", is_followup=True)
    #=============================================================================================================================================================