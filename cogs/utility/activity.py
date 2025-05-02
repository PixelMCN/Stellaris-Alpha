import nextcord
from nextcord.ext import commands, tasks
import random

class ActivityManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.activities = [
            {"type": nextcord.ActivityType.playing, "name": "with commands"},
            {"type": nextcord.ActivityType.playing, "name": "with Discord API"},
            {"type": nextcord.ActivityType.playing, "name": "with servers"},
            
            {"type": nextcord.ActivityType.watching, "name": "over your server"},
            {"type": nextcord.ActivityType.watching, "name": "for commands"},
            {"type": nextcord.ActivityType.watching, "name": "your messages"},
            
            {"type": nextcord.ActivityType.listening, "name": "to slash commands"},
            {"type": nextcord.ActivityType.listening, "name": "to your feedback"},
            
            {"type": nextcord.ActivityType.custom, "name": "Ready to help!"}
        ]
        self.current_index = 0
        self.change_activity.start()
        
    def cog_unload(self):
        self.change_activity.cancel()
    
    @tasks.loop(minutes=10)
    async def change_activity(self):
        if not self.bot.is_ready():
            return
            
        activity_data = self.activities[self.current_index]
        
        activity = nextcord.Activity(
            type=activity_data["type"],
            name=activity_data["name"]
        )
        
        await self.bot.change_presence(activity=activity)
        
        self.current_index = (self.current_index + 1) % len(self.activities)
    
    @change_activity.before_loop
    async def before_change_activity(self):
        await self.bot.wait_until_ready()