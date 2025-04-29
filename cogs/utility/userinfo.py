# userinfo.py
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
from datetime import datetime
import time
from typing import Optional

class UserInfo(commands.Cog):
    """Command for getting information about a user"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @nextcord.slash_command(name="userinfo", description="Get information about a user")
    async def userinfo(
        self,
        interaction: Interaction,
        user: Optional[nextcord.Member] = SlashOption(description="The user to get information about", required=False)
    ):
        """Display detailed information about a user"""
        # If no user is specified, use the command invoker
        user = user or interaction.user
        
        # Get account creation date and server join date
        created_at_timestamp = int(time.mktime(user.created_at.timetuple()))
        creation_date = f"<t:{created_at_timestamp}:F>"
        account_age = f"<t:{created_at_timestamp}:R>"
        
        joined_at_timestamp = int(time.mktime(user.joined_at.timetuple()))
        join_date = f"<t:{joined_at_timestamp}:F>"
        server_age = f"<t:{joined_at_timestamp}:R>"
        
        # Get roles
        roles = [role.mention for role in reversed(user.roles) if role.name != "@everyone"]
        roles_text = ", ".join(roles) if roles else "None"
        
        # Get permissions
        permissions = []
        for perm, value in user.guild_permissions:
            if value:
                formatted_perm = perm.replace('_', ' ').title()
                permissions.append(f"`{formatted_perm}`")
        
        permissions_text = ", ".join(permissions) if permissions else "None"
        
        # Get status and activity
        status = str(user.status).title()
        activity = "None"
        if user.activity:
            if user.activity.type == nextcord.ActivityType.playing:
                activity = f"Playing {user.activity.name}"
            elif user.activity.type == nextcord.ActivityType.streaming:
                activity = f"Streaming {user.activity.name}"
            elif user.activity.type == nextcord.ActivityType.listening:
                activity = f"Listening to {user.activity.name}"
            elif user.activity.type == nextcord.ActivityType.watching:
                activity = f"Watching {user.activity.name}"
            elif user.activity.type == nextcord.ActivityType.custom:
                activity = user.activity.name
            else:
                activity = f"{user.activity.name}"
        
        # Create embed
        embed = nextcord.Embed(
            title=f"User Information: {user.name}",
            description=f"**ID:** {user.id}",
            color=user.top_role.color
        )
        
        if user.avatar:
            embed.set_thumbnail(url=user.display_avatar.url)
        
        if user.banner:
            embed.set_image(url=user.banner.url)
        
        # User stats
        embed.add_field(name="Display Name", value=user.display_name, inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Bot Account", value="Yes" if user.bot else "No", inline=True)
        
        embed.add_field(name="Activity", value=activity, inline=False)
        embed.add_field(name="Created", value=f"{creation_date} ({account_age})", inline=True)
        embed.add_field(name="Joined Server", value=f"{join_date} ({server_age})", inline=True)
        
        # Top role
        embed.add_field(name="Top Role", value=user.top_role.mention if user.top_role.name != "@everyone" else "None", inline=False)
        
        # Roles
        if len(roles_text) > 1024:
            embed.add_field(name="Roles", value=f"User has {len(roles)} roles. Too many to display.", inline=False)
        else:
            embed.add_field(name=f"Roles [{len(roles)}]", value=roles_text, inline=False)
        
        # Key permissions
        if len(permissions_text) > 1024:
            embed.add_field(name="Key Permissions", value="This user has many permissions. See below.", inline=False)
            
            # Split permissions into multiple fields if needed
            chunks = []
            current_chunk = []
            current_length = 0
            
            for perm in permissions:
                if current_length + len(perm) + 2 > 1024:  # +2 for ", "
                    chunks.append(current_chunk)
                    current_chunk = [perm]
                    current_length = len(perm)
                else:
                    current_chunk.append(perm)
                    current_length += len(perm) + 2
            
            if current_chunk:
                chunks.append(current_chunk)
                
            for i, chunk in enumerate(chunks):
                embed.add_field(name=f"Permissions {i+1}", value=", ".join(chunk), inline=False)
        else:
            embed.add_field(name="Key Permissions", value=permissions_text, inline=False)
        
        embed.set_footer(text=f"Requested by {interaction.user.name}")
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)