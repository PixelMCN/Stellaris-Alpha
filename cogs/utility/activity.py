import nextcord
from nextcord.ext import commands, tasks
import random
import logging
import asyncio
from typing import Dict, List, Union, Optional, Any

logger = logging.getLogger(__name__)

class ActivityManager(commands.Cog):
    """
    A cog to manage dynamic activity status for Discord bots.
    Shows various dynamic statuses including server count and user count.
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_activity_index: int = -1  # Start with -1 so first activity will be at index 0
        self.change_activity_task: Optional[tasks.Loop] = None
        self.update_interval: int = 120  # Update status every 2 minutes
        
        # Start the activity rotation task
        self.start_activity_rotation()
    
    def start_activity_rotation(self) -> None:
        """Start the activity rotation task."""
        try:
            self.change_activity_task = self.change_activity.start()
            logger.info("Activity rotation started successfully")
        except Exception as e:
            logger.error(f"Failed to start activity rotation: {e}")
    
    def cog_unload(self) -> None:
        """Clean up when cog is unloaded."""
        if self.change_activity_task:
            self.change_activity_task.cancel()
            logger.info("Activity rotation stopped")
    
    def get_dynamic_activities(self) -> List[Dict[str, Any]]:
        """
        Generate a list of dynamic activities with current stats.
        Returns a list of activity dictionaries with up-to-date information.
        """
        # Calculate stats
        server_count = len(self.bot.guilds)
        user_count = sum(guild.member_count for guild in self.bot.guilds)
        
        return [
            # Watching activities
            {"type": nextcord.ActivityType.watching, "name": f"over {server_count} servers"},
            {"type": nextcord.ActivityType.watching, "name": f"{user_count} users"},
            {"type": nextcord.ActivityType.watching, "name": "for commands"},
            
            # Listening activities
            {"type": nextcord.ActivityType.listening, "name": "to slash commands"},
            {"type": nextcord.ActivityType.listening, "name": "to your feedback"},
            {"type": nextcord.ActivityType.listening, "name": f"to {user_count} users"},
            
            # Competing activities (available in newer versions)
            {"type": nextcord.ActivityType.competing, "name": "for the best bot award"},
            
            # Custom status
            {"type": nextcord.ActivityType.custom, "name": f"Serving {server_count} servers!"}
        ]
    
    @tasks.loop(seconds=5)
    async def change_activity(self) -> None:
        """
        Changes the bot's activity status at regular intervals.
        Dynamically generates activities with current stats.
        """
        # Wait a bit before changing to the regular interval
        if self.change_activity.current_loop == 0:
            self.change_activity.change_interval(seconds=self.update_interval)
        
        try:
            if not self.bot.is_ready():
                return
                
            # Get fresh activities with current stats
            activities = self.get_dynamic_activities()
            
            # Select a new random activity (but not the same as last time)
            available_indices = list(range(len(activities)))
            if self.last_activity_index in available_indices and len(available_indices) > 1:
                available_indices.remove(self.last_activity_index)
                
            new_index = random.choice(available_indices)
            self.last_activity_index = new_index
            
            activity_data = activities[new_index]
            
            # Create and set the activity
            activity = nextcord.Activity(
                type=activity_data["type"],
                name=activity_data["name"]
            )
            
            await self.bot.change_presence(activity=activity)
            logger.debug(f"Changed activity to: {activity_data['type']} {activity_data['name']}")
            
        except Exception as e:
            logger.error(f"Error changing activity status: {e}")
    
    @change_activity.before_loop
    async def before_change_activity(self) -> None:
        """Ensure the bot is ready before starting the activity loop."""
        logger.info("Waiting for bot to be ready before starting activity rotation...")
        await self.bot.wait_until_ready()
        logger.info("Bot is ready, starting activity rotation")
    
    @commands.command(name="forcestatus")
    @commands.is_owner()  # Only the bot owner can use this command
    async def force_status_update(self, ctx: commands.Context) -> None:
        """Force an immediate status update."""
        try:
            # Cancel and restart the task to force an immediate update
            self.change_activity.cancel()
            self.change_activity.start()
            await ctx.send("Status update forced!")
        except Exception as e:
            logger.error(f"Error forcing status update: {e}")
            await ctx.send(f"Error: {e}")


def setup(bot: commands.Bot) -> None:
    """Add the ActivityManager cog to the bot."""
    bot.add_cog(ActivityManager(bot))