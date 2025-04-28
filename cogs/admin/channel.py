import nextcord
from nextcord.ext import commands
from nextcord import Interaction


class Channel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # CHANNEL COMMANDS
    #=============================================================================================================================================================
    @nextcord.slash_command(name="channel", description="Manage channels")
    async def channel(self, interaction: Interaction):
        pass
    
    # CHANNEL CREATE COMMAND
    #=============================================================================================================================================================
    @channel.subcommand(name="create", description="Create a new channel")
    async def create_channel(self, interaction: Interaction, name: str, category: nextcord.CategoryChannel = nextcord.SlashOption(required=False)):
        await interaction.response.defer()
        guild = interaction.guild
        if category:
            channel = await guild.create_text_channel(name, category=category)
        else:
            channel = await guild.create_text_channel(name)
        embed = nextcord.Embed(title="Channel Created", color=nextcord.Color.green())
        embed.add_field(name="Name", value=channel.mention, inline=True)
        await interaction.followup.send(embed=embed)

    # CHANNEL DELETE COMMAND
    #=============================================================================================================================================================
    @channel.subcommand(name="delete", description="Delete a channel")
    async def delete_channel(self, interaction: Interaction, channel: nextcord.TextChannel):
        await interaction.response.defer()
        await channel.delete()
        embed = nextcord.Embed(title="Channel Deleted", color=nextcord.Color.red())
        embed.add_field(name="Name", value=channel.mention, inline=True)
        await interaction.followup.send(embed=embed)

    # CHANNEL RENAME COMMAND
    #=============================================================================================================================================================
    @channel.subcommand(name="rename", description="Rename a channel")
    async def rename_channel(self, interaction: Interaction, channel: nextcord.TextChannel, new_name: str):
        await interaction.response.defer()
        await channel.edit(name=new_name)
        embed = nextcord.Embed(title="Channel Renamed", color=nextcord.Color.blue())
        embed.add_field(name="Old Name", value=channel.mention, inline=True)
        embed.add_field(name="New Name", value=new_name, inline=True)
        await interaction.followup.send(embed=embed)

    # CHANNEL MOVE COMMAND
    #=============================================================================================================================================================
    @channel.subcommand(name="move", description="Move a channel to a new category")
    async def move_channel(self, interaction: Interaction, channel: nextcord.TextChannel, category: nextcord.CategoryChannel):
        await interaction.response.defer()
        await channel.edit(category=category)
        embed = nextcord.Embed(title="Channel Moved", color=nextcord.Color.purple())
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Category", value=category.mention, inline=True)
        await interaction.followup.send(embed=embed)
    #=============================================================================================================================================================

