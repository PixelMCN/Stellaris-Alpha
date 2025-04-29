# serverinfo.py
import nextcord
from nextcord import Interaction
from nextcord.ext import commands
from datetime import datetime
import time

class ServerInfo(commands.Cog):
    """Command for getting information about the server"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @nextcord.slash_command(name="serverinfo", description="Get information about the server")
    async def serverinfo(self, interaction: Interaction):
        """Display detailed information about the current server"""
        guild = interaction.guild
        
        # Get counts
        total_members = guild.member_count
        total_text_channels = len(guild.text_channels)
        total_voice_channels = len(guild.voice_channels)
        total_categories = len(guild.categories)
        total_roles = len(guild.roles) - 1  # Subtract @everyone role
        
        # Get server creation date and calculate age
        created_at = guild.created_at
        timestamp = int(time.mktime(created_at.timetuple()))
        creation_date = f"<t:{timestamp}:F>"
        age = f"<t:{timestamp}:R>"
        
        # Get guild features
        features = ", ".join(guild.features) if guild.features else "None"
        
        # Get verification level
        verification = str(guild.verification_level).title()
        
        # Create embed
        embed = nextcord.Embed(
            title=f"{guild.name} Server Information",
            description=f"**ID:** {guild.id}",
            color=0x3498db
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        # Owner information
        owner = guild.owner
        embed.add_field(
            name="Owner",
            value=f"{owner.mention} ({owner.name})",
            inline=False
        )
        
        # Server stats
        embed.add_field(name="Members", value=f"{total_members:,}", inline=True)
        embed.add_field(name="Roles", value=f"{total_roles:,}", inline=True)
        embed.add_field(name="Emojis", value=f"{len(guild.emojis):,}/{guild.emoji_limit:,}", inline=True)
        embed.add_field(name="Text Channels", value=f"{total_text_channels:,}", inline=True)
        embed.add_field(name="Voice Channels", value=f"{total_voice_channels:,}", inline=True)
        embed.add_field(name="Categories", value=f"{total_categories:,}", inline=True)
        
        # Server details
        embed.add_field(name="Verification Level", value=verification, inline=True)
        embed.add_field(name="Boost Tier", value=f"Level {guild.premium_tier}", inline=True)
        embed.add_field(name="Boost Count", value=f"{guild.premium_subscription_count:,}", inline=True)
        
        if guild.description:
            embed.add_field(name="Description", value=guild.description, inline=False)
            
        embed.add_field(name="Features", value=features, inline=False)
        embed.add_field(name="Created", value=f"{creation_date} ({age})", inline=False)
        
        embed.set_footer(text=f"Requested by {interaction.user.name}")
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)