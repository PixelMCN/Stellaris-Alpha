import nextcord
import random
from nextcord.ext import commands
from nextcord import Interaction


class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Check if error_handler exists, otherwise create a simple handler
        self.error_handler = getattr(bot, 'error_handler', None)

    # List of ban reasons
    ban_reasons = [
        "Breaking server rules",
        "Inappropriate behavior",
        "Spamming",
        "Harassment",
        "Malicious content",
        "Repeated violations"
    ]
    # BAN COMMAND
    #=============================================================================================================================================================
    @nextcord.slash_command(name="ban", description="Remove a member from the server permanently")
    async def ban(
        self, 
        interaction: Interaction, 
        member: nextcord.Member = nextcord.SlashOption(
            description="The member you want to ban from the server",
            required=True
        ),
        reason: str = nextcord.SlashOption(
            description="Why the member is being banned (optional)",
            required=False
        ),
        deletedays: int = nextcord.SlashOption(
            description="Number of days of message history to delete (0-7)",
            required=False,
            min_value=0,
            max_value=7,
            default=0
        )
    ):
        try:
            # Check if the user has ban permissions
            if not interaction.user.guild_permissions.ban_members:
                embed = nextcord.Embed(
                    title="⚠️ Missing Permissions",
                    description="You need the **Ban Members** permission to use this command.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Check if the bot has ban permissions
            if not interaction.guild.me.guild_permissions.ban_members:
                embed = nextcord.Embed(
                    title="⚠️ Bot Missing Permissions",
                    description="I don't have the **Ban Members** permission. Please update my role permissions to use this command.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Check if the user is trying to ban someone with a higher role
            if interaction.user.top_role <= member.top_role and interaction.user.id != interaction.guild.owner_id:
                embed = nextcord.Embed(
                    title="⚠️ Role Hierarchy",
                    description=f"You cannot ban {member.mention} as they have a higher or equal role to you.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Check if the bot can ban the target member
            if interaction.guild.me.top_role <= member.top_role:
                embed = nextcord.Embed(
                    title="⚠️ Role Hierarchy Issue",
                    description=f"I cannot ban {member.mention} as they have a higher or equal role to me. Please move my role higher in the server settings.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Self-ban check
            if member.id == interaction.user.id:
                embed = nextcord.Embed(
                    title="❓ Self-Ban Prevented",
                    description="You cannot ban yourself. If you want to leave the server, you can do so from the server menu.",
                    color=nextcord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Bot self-ban check
            if member.id == self.bot.user.id:
                embed = nextcord.Embed(
                    title="❓ Bot Ban Prevented",
                    description="I cannot ban myself. If you want to remove me from the server, you can do so from the server settings.",
                    color=nextcord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Use a random reason if none is provided
            if reason is None:
                reason = random.choice(self.ban_reasons)
                full_reason = f"{reason} (Auto-generated reason)"
            else:
                full_reason = reason

            # Convert delete_messages to seconds (1 day = 86400 seconds)
            delete_seconds = deletedays * 86400
            
            # Send a direct message to the member before banning them
            try:
                dm_embed = nextcord.Embed(
                    title=f"You've been banned from {interaction.guild.name}",
                    description=f"A moderator has permanently removed you from the server.",
                    color=nextcord.Color.red()
                )
                dm_embed.add_field(name="Reason", value=full_reason, inline=False)
                dm_embed.add_field(
                    name="What does this mean?", 
                    value="You cannot rejoin the server unless an administrator unbans you.",
                    inline=False
                )
                dm_embed.set_footer(text=f"If you believe this was a mistake, you may contact the server administrators.")
                
                if interaction.guild.icon:
                    dm_embed.set_thumbnail(url=interaction.guild.icon.url)
                    
                await member.send(embed=dm_embed)
            except nextcord.HTTPException:
                # Note that we couldn't send a DM, but continue with the ban
                could_not_dm = True
            else:
                could_not_dm = False
            
            # Confirmation message before banning
            await interaction.response.defer(ephemeral=False)
            
            # Ban the member
            await member.ban(reason=full_reason, delete_message_seconds=delete_seconds)
            
            # Create a detailed embed for the ban
            embed = nextcord.Embed(
                title="🔨 Member Banned",
                description=f"{member.mention} has been permanently banned from the server.",
                color=nextcord.Color.red()
            )
            embed.add_field(name="Member", value=f"{member.name} (`{member.id}`)", inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Reason", value=full_reason, inline=False)
            
            if deletedays > 0:
                embed.add_field(name="Message History", value=f"Deleted messages from the past {deletedays} day(s)", inline=False)
            
            if could_not_dm:
                embed.add_field(
                    name="Note", 
                    value="I wasn't able to send this member a DM about their ban.",
                    inline=False
                )
            
            # Add member avatar if available
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
                
            await interaction.followup.send(embed=embed)
                
        except nextcord.Forbidden:
            embed = nextcord.Embed(
                title="❌ Action Failed",
                description="I couldn't ban that member due to Discord permissions. Please check my role permissions.",
                color=nextcord.Color.red()
            )
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            # Handle errors even if error_handler is not available
            if self.error_handler:
                if not interaction.response.is_done():
                    await self.error_handler.handle_command_error(interaction, e, "ban")
                else:
                    await self.error_handler.handle_command_error(interaction, e, "ban", is_followup=True)
            else:
                # Basic error handling if no error_handler is available
                embed = nextcord.Embed(
                    title="❌ Something Went Wrong",
                    description=f"There was an error while trying to ban this member: `{str(e)}`",
                    color=nextcord.Color.red()
                )
                embed.add_field(name="Need help?", value="If this issue persists, please contact the bot developer.", inline=False)
                
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
    #=============================================================================================================================================================