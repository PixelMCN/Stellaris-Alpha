import nextcord
from nextcord import Interaction
from nextcord.ext import commands
from datetime import datetime
import time
import logging

class ServerInfo(commands.Cog):
    """Cog for retrieving and displaying detailed server information"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('bot.ServerInfo')
    
    @nextcord.slash_command(
        name="serverinfo", 
        description="Get detailed information about the current server"
    )
    async def serverinfo(self, interaction: Interaction):
        """Display comprehensive information about the current Discord server"""
        try:
            # Defer response to allow time for processing
            await interaction.response.defer()
            
            guild = interaction.guild
            if not guild:
                await interaction.followup.send("This command can only be used in a server.")
                return
                
            # Collect server statistics
            stats = self._collect_server_stats(guild)
            
            # Create and send the embed
            embed = self._create_server_info_embed(guild, stats, interaction.user)
            await interaction.followup.send(embed=embed)
            
            self.logger.info(f"Server info displayed for {guild.name} (ID: {guild.id}) - requested by {interaction.user}")
            
        except Exception as e:
            self.logger.error(f"Error in serverinfo command: {str(e)}", exc_info=True)
            await interaction.followup.send("Sorry, I couldn't retrieve the server information. Please try again later.")
    
    def _collect_server_stats(self, guild):
        """Collect all statistics about the server"""
        stats = {
            "total_members": guild.member_count,
            "online_members": sum(1 for member in guild.members if member.status != nextcord.Status.offline) if guild.members else 0,
            "total_text_channels": len(guild.text_channels),
            "total_voice_channels": len(guild.voice_channels),
            "total_categories": len(guild.categories),
            "total_roles": len(guild.roles) - 1,  # Subtract @everyone role
            "verification_level": self._format_verification_level(guild.verification_level),
            "creation_timestamp": int(time.mktime(guild.created_at.timetuple())),
            "features": ", ".join(sorted(guild.features)) if guild.features else "None",
            "emojis": f"{len(guild.emojis):,}/{guild.emoji_limit:,}",
            "stickers": f"{len(guild.stickers):,}/{guild.sticker_limit:,}" if hasattr(guild, 'stickers') else "0/0",
        }
        return stats
        
    def _format_verification_level(self, level):
        """Convert verification level to a readable format"""
        levels = {
            nextcord.VerificationLevel.none: "None",
            nextcord.VerificationLevel.low: "Low",
            nextcord.VerificationLevel.medium: "Medium",
            nextcord.VerificationLevel.high: "High",
            nextcord.VerificationLevel.highest: "Highest"
        }
        return levels.get(level, str(level).capitalize())
        
    def _create_server_info_embed(self, guild, stats, user):
        """Create a rich embed with the server information"""
        embed = nextcord.Embed(
            title=f"{guild.name} Server Information",
            description=f"**ID:** `{guild.id}`",
            color=0x5865F2  # Discord Blurple
        )
        
        # Add server icon if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Add server banner if available
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        # Section 1: General Info
        owner = guild.owner
        embed.add_field(
            name="📋 General",
            value=f"**Owner:** {owner.mention} (`{owner.name}`)\n"
                  f"**Created:** <t:{stats['creation_timestamp']}:F>\n"
                  f"**Age:** <t:{stats['creation_timestamp']}:R>",
            inline=False
        )
        
        # Section 2: Server Population
        embed.add_field(
            name="👥 Population",
            value=f"**Members:** {stats['total_members']:,}\n"
                  f"**Roles:** {stats['total_roles']:,}\n"
                  f"**Boost Level:** {guild.premium_tier} "
                  f"({guild.premium_subscription_count:,} boosts)",
            inline=True
        )
        
        # Section 3: Channel Statistics
        embed.add_field(
            name="💬 Channels",
            value=f"**Text:** {stats['total_text_channels']:,}\n"
                  f"**Voice:** {stats['total_voice_channels']:,}\n"
                  f"**Categories:** {stats['total_categories']:,}",
            inline=True
        )
        
        # Section 4: Server Assets
        embed.add_field(
            name="🎨 Assets",
            value=f"**Emojis:** {stats['emojis']}\n"
                  f"**Stickers:** {stats['stickers']}\n"
                  f"**Verification Level:** {stats['verification_level']}",
            inline=True
        )
        
        # Add description if available
        if guild.description:
            embed.add_field(
                name="📝 Description",
                value=guild.description,
                inline=False
            )
        
        # Add server features if any
        if stats['features'] != "None":
            embed.add_field(
                name="✨ Server Features",
                value=stats['features'],
                inline=False
            )
        
        # Finishing touches
        embed.set_footer(text=f"Requested by {user.name}")
        embed.timestamp = datetime.now()
        
        return embed