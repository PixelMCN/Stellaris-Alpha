import nextcord
import random
from nextcord.ext import commands


class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # BAN COMMANDS
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="ban", description="Ban from the server")
    async def ban(self, ctx: nextcord.Interaction, member: nextcord.Member, *, reason=None):
        if not ctx.user.guild_permissions.ban_members:
            await ctx.respond("This command requires ``ban permission``", ephemeral=True)
            return

        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} has been banned by {ctx.user.mention} for: {reason}", ephemeral=True)
        # Adding reactions
        await ctx.channel.send(f"✅{member.mention} has been banned by {ctx.user.mention} for: {reason}")

        # Send a direct message to the banned member
        try:
            await member.send(f"You have been banned from **{ctx.guild.name}** for: {reason}")
        except nextcord.HTTPException:
            await ctx.respond("Failed to send a direct message to the banned member.", ephemeral=True)

    # UNBAN COMMANDS using user ID
    #=============================================================================================================================================================
    # Slash command implementation
    @nextcord.slash_command(name="unban", description="Unban from the server")
    async def unban(self, ctx: nextcord.Interaction, user_id: int):
        if not ctx.user.guild_permissions.ban_members:
            await ctx.respond("This command requires ``ban permission``", ephemeral=True)
            return

        banned_users = await ctx.guild.bans()
        for ban_entry in banned_users:
            if ban_entry.user.id == user_id:
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"{ban_entry.user.mention} has been unbanned by {ctx.user.mention}", ephemeral=True)
                # Adding reactions
                await ctx.channel.send(f"✅{ban_entry.user.mention} has been unbanned by {ctx.user.mention}")
                return

        await ctx.send(f"No banned user found with ID: {user_id}", ephemeral=True)
    #=============================================================================================================================================================