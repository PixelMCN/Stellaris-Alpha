import nextcord
import datetime

class EmbedColors:
    """Standard color scheme for different types of embeds"""
    SUCCESS = 0x57F287  # Green
    ERROR = 0xED4245    # Red
    WARNING = 0xFEE75C  # Yellow
    INFO = 0x3498DB     # Blue
    MODERATION = 0xEB459E  # Pink/Purple for moderation actions
    VOICE = 0xF1C40F    # Gold for voice-related actions
    UTILITY = 0x5865F2  # Discord Blurple for utility commands

class EmbedHelper:
    """Helper class for creating standardized embeds across the bot"""
    
    @staticmethod
    def success_embed(title, description, **kwargs):
        """Creates a standardized success embed"""
        embed = nextcord.Embed(
            title=f"✅ {title}",
            description=description,
            color=EmbedColors.SUCCESS,
            timestamp=kwargs.get('timestamp', datetime.datetime.now())
        )
        
        # Add fields if provided
        fields = kwargs.get('fields', [])
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
            
        # Add footer if provided
        if 'footer' in kwargs:
            embed.set_footer(text=kwargs['footer'], icon_url=kwargs.get('footer_icon', None))
            
        # Add thumbnail if provided
        if 'thumbnail' in kwargs:
            embed.set_thumbnail(url=kwargs['thumbnail'])
            
        return embed
    
    @staticmethod
    def error_embed(title, description, **kwargs):
        """Creates a standardized error embed"""
        embed = nextcord.Embed(
            title=f"❌ {title}",
            description=description,
            color=EmbedColors.ERROR,
            timestamp=kwargs.get('timestamp', datetime.datetime.now())
        )
        
        # Add fields if provided
        fields = kwargs.get('fields', [])
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
            
        # Add footer if provided
        if 'footer' in kwargs:
            embed.set_footer(text=kwargs['footer'], icon_url=kwargs.get('footer_icon', None))
            
        return embed
    
    @staticmethod
    def warning_embed(title, description, **kwargs):
        """Creates a standardized warning embed"""
        embed = nextcord.Embed(
            title=f"⚠️ {title}",
            description=description,
            color=EmbedColors.WARNING,
            timestamp=kwargs.get('timestamp', datetime.datetime.now())
        )
        
        # Add fields if provided
        fields = kwargs.get('fields', [])
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
            
        # Add footer if provided
        if 'footer' in kwargs:
            embed.set_footer(text=kwargs['footer'], icon_url=kwargs.get('footer_icon', None))
            
        return embed
    
    @staticmethod
    def info_embed(title, description, **kwargs):
        """Creates a standardized info embed"""
        embed = nextcord.Embed(
            title=f"ℹ️ {title}",
            description=description,
            color=EmbedColors.INFO,
            timestamp=kwargs.get('timestamp', datetime.datetime.now())
        )
        
        # Add fields if provided
        fields = kwargs.get('fields', [])
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
            
        # Add footer if provided
        if 'footer' in kwargs:
            embed.set_footer(text=kwargs['footer'], icon_url=kwargs.get('footer_icon', None))
            
        # Add thumbnail if provided
        if 'thumbnail' in kwargs:
            embed.set_thumbnail(url=kwargs['thumbnail'])
            
        return embed
    
    @staticmethod
    def moderation_embed(title, description, **kwargs):
        """Creates a standardized moderation action embed"""
        embed = nextcord.Embed(
            title=f"{kwargs.get('emoji', '🛡️')} {title}",
            description=description,
            color=EmbedColors.MODERATION,
            timestamp=kwargs.get('timestamp', datetime.datetime.now())
        )
        
        # Standard fields for moderation embeds
        if 'member' in kwargs:
            member = kwargs['member']
            embed.add_field(name="Member", value=f"{member.name} (`{member.id}`)", inline=True)
            
            # Add member avatar if available
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
        
        if 'moderator' in kwargs:
            embed.add_field(name="Moderator", value=kwargs['moderator'].mention, inline=True)
            
        if 'reason' in kwargs:
            embed.add_field(name="Reason", value=kwargs['reason'], inline=False)
            
        # Add duration if provided (for temporary actions)
        if 'duration' in kwargs:
            embed.add_field(name="Duration", value=kwargs['duration'], inline=True)
            
        if 'expires' in kwargs:
            embed.add_field(name="Expires", value=kwargs['expires'], inline=True)
            
        # Add fields if provided
        fields = kwargs.get('fields', [])
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
            
        # Add footer if provided
        if 'footer' in kwargs:
            embed.set_footer(text=kwargs['footer'], icon_url=kwargs.get('footer_icon', None))
            
        return embed
    
    @staticmethod
    def voice_embed(title, description, **kwargs):
        """Creates a standardized voice action embed"""
        embed = nextcord.Embed(
            title=f"{kwargs.get('emoji', '🔊')} {title}",
            description=description,
            color=EmbedColors.VOICE,
            timestamp=kwargs.get('timestamp', datetime.datetime.now())
        )
        
        # Add fields if provided
        fields = kwargs.get('fields', [])
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
            
        # Add footer if provided
        if 'footer' in kwargs:
            embed.set_footer(text=kwargs['footer'], icon_url=kwargs.get('footer_icon', None))
            
        # Add thumbnail if provided
        if 'thumbnail' in kwargs:
            embed.set_thumbnail(url=kwargs['thumbnail'])
            
        return embed
    
    @staticmethod
    def permission_error_embed(permission_name):
        """Creates a standardized permission error embed"""
        return EmbedHelper.warning_embed(
            "Missing Permissions",
            f"You need the **{permission_name}** permission to use this command."
        )
    
    @staticmethod
    def bot_permission_error_embed(permission_name):
        """Creates a standardized bot permission error embed"""
        return EmbedHelper.warning_embed(
            "Bot Missing Permissions",
            f"I don't have the **{permission_name}** permission. Please update my role permissions to use this command."
        )