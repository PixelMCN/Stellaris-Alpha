import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="unban", description="Unban a user from the server")
    async def unban(
        self, 
        interaction: Interaction, 
        user_id: str = SlashOption(
            description="The ID of the user to unban",
            required=True
        ),
        reason: str = SlashOption(
            description="Reason for unbanning the user",
            required=False
        )
    ):
        # Check if the user has ban permissions
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You don't have permission to unban members.", ephemeral=True)
            return
            
        # Check if the bot has ban permissions
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message("I don't have permission to unban members.", ephemeral=True)
            return

        # Default reason if none provided
        if reason is None:
            reason = f"Unbanned by {interaction.user}"

        try:
            # Try to convert the user_id to an integer
            try:
                user_id = int(user_id)
            except ValueError:
                await interaction.response.send_message("Please provide a valid user ID.", ephemeral=True)
                return
                
            # Get the ban entry
            banned_users = [ban_entry async for ban_entry in interaction.guild.bans()]
            banned_user = next((ban_entry for ban_entry in banned_users if ban_entry.user.id == user_id), None)
            
            if banned_user is None:
                await interaction.response.send_message(f"User with ID {user_id} is not banned.", ephemeral=True)
                return
                
            # Unban the user
            await interaction.guild.unban(banned_user.user, reason=reason)
            
            # Create an embed for the response
            embed = nextcord.Embed(
                title="User Unbanned",
                description=f"**{banned_user.user}** has been unbanned.",
                color=0x00FF00
            )
            embed.add_field(name="User ID", value=user_id, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.set_footer(text=f"Unbanned by {interaction.user}")
            
            # Send the response
            await interaction.response.send_message(embed=embed)
            
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to unban that user.", ephemeral=True)
        except Exception as e:
            # Let the global error handler handle other exceptions
            raise e