import os
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import utilities
from utils.error_handler import ErrorHandler
from utils.embed_helper import EmbedHelper, EmbedColors
from utils.time_helper import TimeHelper

# Bot version
BOT_VERSION = 'v1.0.1'

#importing moderation cogs
#=============================================================================================================================================================
from cogs.moderation.ban import BanCommands
from cogs.moderation.kick import KickCommands
from cogs.moderation.purge import PurgeCommands
from cogs.moderation.lock import LockCommands
from cogs.moderation.slowmode import SlowmodeCommands
from cogs.moderation.mute import MuteCommands
from cogs.moderation.deafen import DeafenCommands
#=============================================================================================================================================================


#importing admin cogs
#=============================================================================================================================================================
from cogs.admin.role import RoleCommands
from cogs.admin.logs import LogsCommands
from cogs.admin.autorole import Autorole
#=============================================================================================================================================================


#importing utility cogs
#=============================================================================================================================================================
from cogs.utility.help import HelpCommand
from cogs.utility.activity import ActivityManager
from cogs.utility.status import Status
from cogs.utility.avatar import Avatar
from cogs.utility.serverinfo import ServerInfo
from cogs.utility.userinfo import UserInfo
#=============================================================================================================================================================
# importing activity cogs
from utils.activity import ActivityManager
#=============================================================================================================================================================

BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# INTENTS
intents = nextcord.Intents.default()
intents.message_content = True  
intents.guilds = True
intents.members = True

# BOT INSTANCE
bot = commands.Bot(command_prefix="s!", intents=intents, help_command=None)

# Make utilities available to all cogs
bot.error_handler = ErrorHandler(bot)
bot.error_handler.register_error_handlers()
bot.embed_helper = EmbedHelper
bot.embed_colors = EmbedColors
bot.time_helper = TimeHelper
bot.version = BOT_VERSION

# Load Moderation cogs
#=============================================================================================================================================================
bot.add_cog(BanCommands(bot))
bot.add_cog(KickCommands(bot))
bot.add_cog(PurgeCommands(bot))
bot.add_cog(LockCommands(bot))
bot.add_cog(SlowmodeCommands(bot))
bot.add_cog(MuteCommands(bot))
bot.add_cog(DeafenCommands(bot))
#=============================================================================================================================================================
# Load Admin cogs
#=============================================================================================================================================================
bot.add_cog(RoleCommands(bot))
bot.add_cog(LogsCommands(bot))
bot.add_cog(Autorole(bot))
#=============================================================================================================================================================
# Load utility cogs
#=============================================================================================================================================================
bot.add_cog(HelpCommand(bot))
bot.add_cog(Status(bot))
bot.add_cog(Avatar(bot))
bot.add_cog(ServerInfo(bot))
bot.add_cog(UserInfo(bot))
#=============================================================================================================================================================
# EVENTS & ACTIVITIES
bot.add_cog(ActivityManager(bot))
#=============================================================================================================================================================
# WILL IMPLEMENT THIS LATER LOL
"""
# Load cogs automatically
def load_cogs(bot):
    for folder in os.listdir('./commands'):
        if os.path.isdir(f'./commands/{folder}'):
            for filename in os.listdir(f'./commands/{folder}'):
                if filename.endswith('.py'):
                    bot.load_extension(f'commands.{folder}.{filename[:-3]}')

load_cogs(bot)
"""

# Bot event for when it's ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print(f'Bot Version: {BOT_VERSION}')
    print(f'Nextcord Version: {nextcord.__version__}')
    print(f'Connected to {len(bot.guilds)} servers')
    print('------')

# Run the bot
bot.run(BOT_TOKEN)
