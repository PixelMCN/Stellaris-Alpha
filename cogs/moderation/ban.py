import nextcord
import random
from nextcord.ext import commands
from nextcord import Interaction

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # List of ban reasons
    ban_reasons = [
        "Breaking server rules",
        "Inappropriate behavior",
        "Spamming",
        "Harassment"
    ]

    @nextcord.slash_command(name="ban", description="Ban a member from the server")
    async def ban(self, interaction: Interaction, member: nextcord.Member, reason: str = None, delete_messages: int = 0):
        # Check if the user has ban permissions
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You don't have permission to ban members.", ephemeral=True)
            return
            
        # Check if the bot has ban permissions
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message("I don't have permission to ban members.", ephemeral=True)
            return
            
        # Check if the user is trying to ban someone with a higher role
        if interaction.user.top_role <= member.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("You can't ban someone with a higher or equal role.", ephemeral=True)
            return
            
        # Check if the bot can ban the target member
        if interaction.guild.me.top_role <= member.top_role:
            await interaction.response.send_message("I can't ban someone with a higher or equal role than me.", ephemeral=True)
            return

        # Use a random reason if none is provided
        if reason is None:
            reason = random.choice(self.ban_reasons)

        try:
            # Convert delete_messages to days for compatibility
            delete_days = min(7, max(0, delete_messages))
            
            # Ban the member
            await member.ban(reason=reason, delete_message_days=delete_days)
            
            # Send confirmation message
            await interaction.response.send_message(f'{member.mention} has been banned for: {reason}')
            
            # Try to DM the banned user
            try:
                await member.send(f"You have been banned from **{interaction.guild.name}** for: **{reason}**")
            except:
                # If DM fails, just continue
                pass
                
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban that member.", ephemeral=True)
        except Exception as e:
            # Let the global error handler handle other exceptions
            raise e
        
    @nextcord.slash_command(name="unban", description="Unban a member from the server")
    async def unban(self, interaction: Interaction, member: nextcord.Member, reason: str = None):
        # Check if the user has ban permissions
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You don't have permission to unban members.", ephemeral=True)
            return

        # Check if the bot has ban permissions  
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message("I don't have permission to unban members.", ephemeral=True)
            return

        # Use a random reason if none is provided
        if reason is None:
            reason = random.choice(self.ban_reasons)

        try:
            # Unban the member
            await interaction.guild.unban(member, reason=reason)

            # Send confirmation message
            await interaction.response.send_message(f'{member.mention} has been unbanned for: {reason}')

        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to unban that member.", ephemeral=True)
        except Exception as e:
            # Let the global error handler handle other exceptions
            raise e