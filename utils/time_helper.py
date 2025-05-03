import re
from datetime import datetime
import time
from typing import Optional

class TimeHelper:
    """Helper class for time-related operations"""
    
    @staticmethod
    def now() -> datetime:
        """
        Returns the current datetime object
        This method was added to fix the error in role_add and role_remove
        """
        return datetime.now()
    
    @staticmethod
    def parse_time(time_str: str) -> Optional[int]:
        """
        Parse a time string like "10s", "5m", "1h", "2d" into seconds
        Returns None if the format is invalid
        """
        if not time_str:
            return None
            
        # Regular expression to match a number followed by a time unit
        match = re.match(r'^(\d+)([smhd])$', time_str.lower())
        if not match:
            return None
            
        value, unit = match.groups()
        value = int(value)
        
        if unit == 's':
            return value
        elif unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
        elif unit == 'd':
            return value * 86400
        return None
    
    @staticmethod
    def format_time_remaining(expiry_time: float) -> str:
        """Format the remaining time until expiry in a human-readable way"""
        seconds_remaining = int(expiry_time - time.time())
        if seconds_remaining <= 0:
            return "0 seconds"
            
        days, remainder = divmod(seconds_remaining, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 and not parts:  # Only show seconds if there are no larger units
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
            
        return ", ".join(parts)
    
    @staticmethod
    def format_timestamp(timestamp: float) -> str:
        """Format a timestamp into a human-readable date and time"""
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")