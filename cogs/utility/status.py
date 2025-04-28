from nextcord.ext import commands
import nextcord
import time
import psutil
import os
import platform

# Bot version constant
BOT_VERSION = 'v1.0.0'  # Update this when you update your bot

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="status", description="Shows the system resources used by bot")
    async def status(self, interaction: nextcord.Interaction):
        # System resources calculation
        total_memory = round(psutil.virtual_memory().total / 1024 / 1024)
        free_memory = round(psutil.virtual_memory().available / 1024 / 1024)
        used_memory = total_memory - free_memory
        memory_percentage = round((used_memory/total_memory)*100)
        cpu_usage = psutil.cpu_percent()
        free_space = round(psutil.disk_usage('/').free / (1024 * 1024 * 1024))

        # Bot information
        uptime = time.time() - psutil.Process().create_time()
        latency = round(self.bot.latency * 1000)
        guild_count = len(self.bot.guilds)
        user_count = len(self.bot.users)
        channel_count = sum(len(guild.channels) for guild in self.bot.guilds)

        # Format uptime
        days = int(uptime // 86400)
        hours = int((uptime % 86400) // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

        embed = nextcord.Embed(
            color=0x5865F2,
            title='Bot Status Dashboard',
            description='Current performance metrics and statistics'
        )

        # System Resources Field
        embed.add_field(
            name='System Resources',
            value=f'```\n'
                  f'CPU Usage   : {cpu_usage}%\n'
                  f'Memory      : {used_memory}MB / {total_memory}MB ({memory_percentage}%)\n'
                  f'Disk Space  : {free_space}GB Free\n'
                  f'Platform    : {platform.system()} ({platform.release()})\n'
                  f'CPU Cores   : {psutil.cpu_count()}\n'
                  f'Arch        : {platform.machine()}\n'
                  f'```',
            inline=False
        )

        # Bot Statistics Field
        embed.add_field(
            name='Bot Statistics',
            value=f'```\n'
                  f'Bot Version : {BOT_VERSION}\n'
                  f'Nextcord    : {nextcord.__version__}\n'
                  f'Python      : {platform.python_version()}\n'
                  f'Uptime      : {uptime_str}\n'
                  f'Latency     : {latency}ms\n'
                  f'Servers     : {guild_count}\n'
                  f'Users       : {user_count}\n'
                  f'Channels    : {channel_count}\n'
                  f'Process ID  : {os.getpid()}\n'
                  f'```',
            inline=False
        )

        # Memory Usage Field
        embed.add_field(
            name='Memory Usage',
            value=f'```\n'
                  f'RSS         : {round(psutil.Process().memory_info().rss / 1024 / 1024)}MB\n'
                  f'VMS         : {round(psutil.Process().memory_info().vms / 1024 / 1024)}MB\n'
                  f'```',
            inline=False
        )

        embed.set_footer(text=f'Requested by {interaction.user}', icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = nextcord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

