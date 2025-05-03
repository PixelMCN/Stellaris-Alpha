import nextcord
from nextcord.ext import commands
import time
import psutil
import os
import platform
import logging
from typing import Optional
import sys

# Bot version & configuration
BOT_VERSION = 'v1.0.0'  # Update this when you update your bot
CONFIG = {
    "SUPPORT_SERVER": "https://discord.gg/wqgvsuw7r8",
    "DOCS_URL": "https://your-documentation-url.com",
    "GITHUB_URL": "https://github.com/PixelMCN/Stellaris-Alpha",
    "BANNER_URL": "https://raw.githubusercontent.com/PixelMCN/Stellaris-Alpha/refs/heads/main/assets/banner.png"
}

class StatusPanelView(nextcord.ui.View):
    """UI View containing support links and resources"""
    
    def __init__(self):
        super().__init__(timeout=None)  # No timeout for buttons
        
        # Add the buttons with their URLs
        self.add_item(nextcord.ui.Button(
            label="Support Server",
            url=CONFIG["SUPPORT_SERVER"],
            style=nextcord.ButtonStyle.blurple
        ))
        self.add_item(nextcord.ui.Button(
            label="Documentation",
            url=CONFIG["DOCS_URL"],
            style=nextcord.ButtonStyle.green
        ))
        self.add_item(nextcord.ui.Button(
            label="GitHub",
            url=CONFIG["GITHUB_URL"],
            style=nextcord.ButtonStyle.gray
        ))


class Status(commands.Cog):
    """Cog for displaying system diagnostics and bot statistics"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('bot.Status')
        self.start_time = time.time()
    
    @nextcord.slash_command(
        name="status", 
        description="Show detailed bot diagnostics and system information"
    )
    async def status(self, interaction: nextcord.Interaction):
        """Displays diagnostic information about the bot and system resources"""
        try:
            # Defer response to allow time for resource collection
            await interaction.response.defer()
            
            # Collect system and bot metrics
            metrics = self._collect_metrics()
            
            # Create and send the embed with metrics
            embed = self._create_status_embed(metrics, interaction.user)
            view = StatusPanelView()
            
            await interaction.followup.send(embed=embed, view=view)
            
            self.logger.info(f"Status panel displayed - requested by {interaction.user}")
            
        except Exception as e:
            self.logger.error(f"Error in status command: {str(e)}", exc_info=True)
            await interaction.followup.send("Failed to retrieve system diagnostics. Please try again later.")
    
    @commands.command(
        name="status", 
        description="Show detailed bot diagnostics and system information"
    )
    async def status_prefix(self, ctx):
        """Legacy prefix command version of the status command"""
        try:
            # Show typing indicator while collecting metrics
            async with ctx.typing():
                # Collect system and bot metrics
                metrics = self._collect_metrics()
                
                # Create and send the embed with metrics
                embed = self._create_status_embed(metrics, ctx.author)
                view = StatusPanelView()
                
                await ctx.send(embed=embed, view=view)
                
                self.logger.info(f"Status panel displayed via prefix command - requested by {ctx.author}")
                
        except Exception as e:
            self.logger.error(f"Error in status prefix command: {str(e)}", exc_info=True)
            await ctx.send("Failed to retrieve system diagnostics. Please try again later.")
    
    def _collect_metrics(self):
        """Collect all system and bot metrics in a structured format"""
        # Get process information
        process = psutil.Process()
        
        # System resources data
        system_data = {
            "cpu_usage": psutil.cpu_percent(interval=0.5),  # Short interval for responsiveness
            "memory_total": round(psutil.virtual_memory().total / (1024 * 1024)),
            "memory_available": round(psutil.virtual_memory().available / (1024 * 1024)),
            "disk_free": round(psutil.disk_usage('/').free / (1024 * 1024 * 1024)),
            "disk_total": round(psutil.disk_usage('/').total / (1024 * 1024 * 1024)),
            "platform": f"{platform.system()} {platform.release()}",
            "cpu_cores": f"{psutil.cpu_count(logical=False)} physical ({psutil.cpu_count(logical=True)} logical)",
            "arch": platform.machine()
        }
        
        # Calculate memory percentage
        system_data["memory_used"] = system_data["memory_total"] - system_data["memory_available"]
        system_data["memory_percent"] = round((system_data["memory_used"] / system_data["memory_total"]) * 100)
        system_data["disk_percent"] = round((system_data["disk_free"] / system_data["disk_total"]) * 100)
        
        # Bot information
        bot_data = {
            "version": BOT_VERSION,
            "nextcord_version": nextcord.__version__,
            "python_version": platform.python_version(),
            "uptime": self._format_uptime(self.start_time),
            "latency": round(self.bot.latency * 1000),
            "guilds": len(self.bot.guilds),
            "users": sum(guild.member_count for guild in self.bot.guilds),
            "channels": sum(len(guild.channels) for guild in self.bot.guilds),
            "process_id": os.getpid()
        }
        
        # Process-specific memory info
        process_data = {
            "rss": round(process.memory_info().rss / (1024 * 1024)),
            "vms": round(process.memory_info().vms / (1024 * 1024)),
            "threads": process.num_threads()
        }
        
        # Combine all metrics
        return {
            "system": system_data,
            "bot": bot_data,
            "process": process_data
        }
    
    def _format_uptime(self, start_time):
        """Format uptime in a human-readable format"""
        uptime = time.time() - start_time
        
        days = int(uptime // 86400)
        hours = int((uptime % 86400) // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _create_status_embed(self, metrics, user):
        """Create a rich embed with all diagnostic information"""
        embed = nextcord.Embed(
            color=0x5865F2,  # Discord Blurple
            title='System Diagnostics',
            description='Current performance metrics and bot statistics'
        )
        
        # System Resources Field with ANSI color status indicators
        sys = metrics["system"]
        
        # Create ANSI color codes for status indicators
        cpu_status = self._get_ansi_status(sys["cpu_usage"], 70, 90)
        mem_status = self._get_ansi_status(sys["memory_percent"], 70, 90)
        disk_status = self._get_ansi_status(100 - sys["disk_percent"], 80, 90)  # Inverted for disk (lower is worse)
        
        embed.add_field(
            name='System Resources',
            value=f'```ansi\n'
                  f'CPU Usage   : {cpu_status}{sys["cpu_usage"]}%\u001b[0m\n'
                  f'Memory      : {mem_status}{sys["memory_used"]:,}MB / {sys["memory_total"]:,}MB ({sys["memory_percent"]}%)\u001b[0m\n'
                  f'Disk Space  : {disk_status}{sys["disk_free"]:,}GB Free ({sys["disk_percent"]}% free)\u001b[0m\n'
                  f'Platform    : {sys["platform"]}\n'
                  f'CPU Cores   : {sys["cpu_cores"]}\n'
                  f'Architecture: {sys["arch"]}\n'
                  f'```',
            inline=False
        )
        
        # Bot Statistics Field
        bot = metrics["bot"]
        embed.add_field(
            name='Bot Statistics',
            value=f'```ansi\n'
                  f'Bot Version : \u001b[34;1m{bot["version"]}\u001b[0m\n'
                  f'Nextcord    : \u001b[34;1m{bot["nextcord_version"]}\u001b[0m\n'
                  f'Python      : \u001b[34;1m{bot["python_version"]}\u001b[0m\n'
                  f'Uptime      : \u001b[32;1m{bot["uptime"]}\u001b[0m\n'
                  f'Latency     : {self._get_ansi_status(bot["latency"], 100, 200)}{bot["latency"]}ms\u001b[0m\n'
                  f'Servers     : \u001b[36;1m{bot["guilds"]:,}\u001b[0m\n'
                  f'Users       : \u001b[36;1m{bot["users"]:,}\u001b[0m\n'
                  f'Channels    : \u001b[36;1m{bot["channels"]:,}\u001b[0m\n'
                  f'Process ID  : {bot["process_id"]}\n'
                  f'```',
            inline=False
        )
        
        # Process Memory Usage Field
        proc = metrics["process"]
        embed.add_field(
            name='Memory Usage',
            value=f'```ansi\n'
                  f'RSS Memory  : \u001b[33;1m{proc["rss"]:,}MB\u001b[0m\n'
                  f'Virtual Mem : \u001b[33;1m{proc["vms"]:,}MB\u001b[0m\n'
                  f'Threads     : \u001b[36;1m{proc["threads"]}\u001b[0m\n'
                  f'```',
            inline=False
        )
        
        # Set a banner image if available
        if CONFIG["BANNER_URL"]:
            embed.set_image(url=CONFIG["BANNER_URL"])
        
        # Set footer with user information and timestamp
        avatar_url = user.avatar.url if user.avatar else None
        embed.set_footer(text=f'Requested by {user}', icon_url=avatar_url)
        embed.timestamp = nextcord.utils.utcnow()
        
        return embed
    
    def _get_ansi_status(self, value, warning_threshold, critical_threshold):
        """Return ANSI color code based on value thresholds"""
        if value < warning_threshold:
            return "\u001b[32;1m"  # Green
        elif value < critical_threshold:
            return "\u001b[33;1m"  # Yellow
        else:
            return "\u001b[31;1m"  # Red