import os
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


#importing moderation cogs
#=============================================================================================================================================================
from cogs.moderation.ban import Ban
from cogs.moderation.kick import Kick
from cogs.moderation.purge import Purge
from cogs.moderation.timeout import Timeout
from cogs.moderation.LockUnlock import LockUnlock
from cogs.moderation.mute import Mute
from cogs.moderation.deafened import Deafen
#=============================================================================================================================================================


#importing admin cogs
#=============================================================================================================================================================
from cogs.admin.role import Role
from cogs.admin.logs import Logs
from cogs.admin.channel import Channel
from cogs.admin.autorole import AutoRole
#=============================================================================================================================================================


#importing utility cogs
#=============================================================================================================================================================
from cogs.utility.help import Help
from cogs.utility.status import Status
from cogs.utility.avatar import Avatar
#=============================================================================================================================================================

BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# Define your intents
intents = nextcord.Intents.default()
intents.message_content = True  
intents.guilds = True
intents.members = True

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Load Moderation cogs
#=============================================================================================================================================================
bot.add_cog(Ban(bot))
bot.add_cog(Kick(bot))
bot.add_cog(Purge(bot))
bot.add_cog(Timeout(bot))
bot.add_cog(LockUnlock(bot))
bot.add_cog(Mute(bot))
bot.add_cog(Deafen(bot))
#=============================================================================================================================================================


# Load Admin cogs
#=============================================================================================================================================================
bot.add_cog(Role(bot))
bot.add_cog(Logs(bot))
bot.add_cog(Channel(bot))
bot.add_cog(AutoRole(bot))
#=============================================================================================================================================================


# Load utility cogs
#=============================================================================================================================================================
bot.add_cog(Help(bot))
bot.add_cog(Status(bot))
bot.add_cog(Avatar(bot))
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
