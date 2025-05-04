import nextcord
from nextcord.ext import commands
from nextcord import Interaction


class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_helper = bot.embed_helper

    # AVATAR COMMANDS
    #=============================================================================================================================================================
    @nextcord.slash_command(name="avatar", description="Get the avatar of a user")
    async def avatar(self, interaction: Interaction, member: nextcord.Member = nextcord.SlashOption(required=False)):
        """
        Displays the avatar of a user.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        member: Optional - The member whose avatar to display. If not provided, shows your own avatar.
        """
        # Don't defer - respond immediately
        if member is None:
            member = interaction.user
            
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        
        embed = self.embed_helper.info_embed(
            f"{member.name}'s Avatar",
            "",
            thumbnail=avatar_url
        )
        embed.set_image(url=avatar_url)
        
        await interaction.response.send_message(embed=embed)
    #=============================================================================================================================================================
        