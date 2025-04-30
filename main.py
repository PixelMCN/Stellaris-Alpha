import os
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the error handler
from utils.error_handler import ErrorHandler

#importing moderation cogs
#=============================================================================================================================================================
from cogs.moderation.ban import Ban
from cogs.moderation.unban import Unban  
from cogs.moderation.kick import Kick
from cogs.moderation.purge import Purge
from cogs.moderation.timeout import Timeout
from cogs.moderation.lock import LockUnlock
from cogs.moderation.slowmode import Slowmode
from cogs.moderation.mute import MuteSystem
from cogs.moderation.deafen import DeafenSystem
#from cogs.moderation.automod import AutoMod  # WIP
#=============================================================================================================================================================


#importing admin cogs
#=============================================================================================================================================================
from cogs.admin.role import Role
from cogs.admin.logs import Logs
from cogs.admin.autorole import AutoRole
#=============================================================================================================================================================


#importing utility cogs
#=============================================================================================================================================================
from cogs.utility.debugpanel import Debug
from cogs.utility.avatar import Avatar
from cogs.utility.serverinfo import ServerInfo
from cogs.utility.userinfo import UserInfo
#=============================================================================================================================================================

BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# INTENTS
intents = nextcord.Intents.default()
intents.message_content = True  
intents.guilds = True
intents.members = True

# BOT INSTANCE
bot = commands.Bot(command_prefix="s!", intents=intents, help_command=None)

# ERROR HANDLER
bot.error_handler = ErrorHandler(bot)
bot.error_handler.register_error_handlers()

# Load Moderation cogs
#=============================================================================================================================================================
bot.add_cog(Ban(bot))
bot.add_cog(Unban(bot))  
bot.add_cog(Kick(bot))
bot.add_cog(Purge(bot))
bot.add_cog(Timeout(bot))
bot.add_cog(LockUnlock(bot))
bot.add_cog(Slowmode(bot))
bot.add_cog(MuteSystem(bot))
bot.add_cog(DeafenSystem(bot))
#bot.add_cog(AutoMod(bot))  # Still needs a bit of work ;-;
#=============================================================================================================================================================
# Load Admin cogs
#=============================================================================================================================================================
bot.add_cog(Role(bot))
bot.add_cog(Logs(bot))
bot.add_cog(AutoRole(bot))
#=============================================================================================================================================================
# Load utility cogs
#=============================================================================================================================================================
bot.add_cog(Debug(bot))
bot.add_cog(Avatar(bot))
bot.add_cog(ServerInfo(bot))
bot.add_cog(UserInfo(bot))
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

# Run the bot
bot.run(BOT_TOKEN)
