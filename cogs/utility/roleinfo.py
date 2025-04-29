# roleinfo.py
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
from datetime import datetime
import time
from typing import Optional

class RoleInfo(commands.Cog):
    """Command for getting information about a role"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @nextcord.slash_command(name="roleinfo", description="Get information about a role")
    async def roleinfo(
        self, 
        interaction: Interaction, 
        role: Optional[nextcord.Role] = SlashOption(description="The role to get information about", required=True)
    ):
        """Display detailed information about a specific role"""
        if not role:
            return await interaction.response.send_message("Please specify a role!", ephemeral=True)
        
        # Get role creation date and calculate age
        created_at = role.created_at
        timestamp = int(time.mktime(created_at.timetuple()))
        creation_date = f"<t:{timestamp}:F>"
        age = f"<t:{timestamp}:R>"
        
        # Get members with this role
        member_count = len(role.members)
        
        # Get permissions
        permissions = []
        for perm, value in role.permissions:
            if value:
                formatted_perm = perm.replace('_', ' ').title()
                permissions.append(f"`{formatted_perm}`")
        
        permissions_text = ", ".join(permissions) if permissions else "None"
        
        # Create embed
        embed = nextcord.Embed(
            title=f"Role Information: {role.name}",
            description=f"**ID:** {role.id}",
            color=role.color
        )
        
        # Role stats
        embed.add_field(name="Color", value=f"#{role.color.value:06x}", inline=True)
        embed.add_field(name="Members", value=f"{member_count:,}", inline=True)
        embed.add_field(name="Position", value=f"{role.position:,}", inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="Displayed Separately", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="Managed by Integration", value="Yes" if role.managed else "No", inline=True)
        embed.add_field(name="Created", value=f"{creation_date} ({age})", inline=False)
        
        if len(permissions_text) > 1024:
            # If permissions text is too long, split it
            embed.add_field(name="Key Permissions", value="This role has many permissions. See below.", inline=False)
            
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
            embed.add_field(name="Permissions", value=permissions_text, inline=False)
        
        embed.set_footer(text=f"Requested by {interaction.user.name}")
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)
