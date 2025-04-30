import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
from typing import Optional


class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize error handler reference
        self.error_handler = bot.error_handler

    # UNBAN COMMAND
    #=============================================================================================================================================================
    @nextcord.slash_command(
        name="unban", 
        description="Unban a user from the server"
    )
    async def unban(
        self, 
        interaction: Interaction, 
        user_id: str = SlashOption(
            description="The ID of the user to unban",
            required=True
        ),
        reason: Optional[str] = SlashOption(
            description="Reason for unbanning the user",
            required=False
        )
    ):
        """
        Unbans a user from the server using their ID.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        user_id: The ID of the user to unban
        reason: Optional reason for unbanning the user
        """
        try:
            # Check if the user has ban permissions
            if not interaction.user.guild_permissions.ban_members:
                await interaction.response.send_message(
                    "❌ You don't have permission to unban members.", 
                    ephemeral=True
                )
                return
                
            # Check if the bot has ban permissions
            if not interaction.guild.me.guild_permissions.ban_members:
                await interaction.response.send_message(
                    "❌ I don't have permission to unban members. Please check my role permissions.", 
                    ephemeral=True
                )
                return

            # Use defer to handle potential delays when fetching ban list
            await interaction.response.defer(ephemeral=False)
            
            # Default reason if none provided
            if not reason:
                reason = f"Unbanned by {interaction.user}"

            # Try to convert the user_id to an integer
            try:
                user_id_int = int(user_id)
            except ValueError:
                await interaction.followup.send(
                    "❌ Please provide a valid user ID. User IDs are numerical values.", 
                    ephemeral=True
                )
                return
            
            # Check if the ID is a plausible Discord user ID (at least 17 digits)
            if len(user_id) < 17:
                await interaction.followup.send(
                    "❌ The provided ID is too short to be a valid Discord user ID.", 
                    ephemeral=True
                )
                return
            
            try:
                # Get the ban entry
                banned_users = [ban_entry async for ban_entry in interaction.guild.bans()]
                banned_user = next((ban_entry for ban_entry in banned_users if ban_entry.user.id == user_id_int), None)
                
                if banned_user is None:
                    await interaction.followup.send(
                        f"ℹ️ User with ID `{user_id}` is not banned from this server.", 
                        ephemeral=True
                    )
                    return
                
                # Store user information before unbanning
                user_name = str(banned_user.user)
                user_avatar = banned_user.user.display_avatar.url
                
                # Unban the user
                await interaction.guild.unban(banned_user.user, reason=f"{reason} - By {interaction.user}")
                
                # Create an embed for the response
                embed = nextcord.Embed(
                    title="🔓 User Unbanned",
                    description=f"**{user_name}** has been unbanned from the server.",
                    color=nextcord.Color.green(),
                    timestamp=interaction.created_at
                )
                embed.add_field(name="User", value=f"{user_name}", inline=True)
                embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                
                # Add user avatar if available
                if user_avatar:
                    embed.set_thumbnail(url=user_avatar)
                
                embed.set_footer(text=f"Unbanned by {interaction.user}")
                
                # Send the response
                await interaction.followup.send(embed=embed)
                
                # Log the unban if a log channel is set up
                log_channel_id = self.bot.config.get("log_channel") if hasattr(self.bot, "config") else None
                if log_channel_id:
                    try:
                        log_channel = interaction.guild.get_channel(log_channel_id)
                        if log_channel:
                            log_embed = embed.copy()
                            log_embed.title = "🔓 User Unbanned - Mod Log"
                            await log_channel.send(embed=log_embed)
                    except Exception:
                        pass  # Silently fail if logging fails
            
            except nextcord.NotFound:
                await interaction.followup.send(
                    "❌ User not found. Please check the ID and try again.", 
                    ephemeral=True
                )
                
        except nextcord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to unban that user. This might be due to role hierarchy constraints.", 
                ephemeral=True
            )
        except nextcord.HTTPException as e:
            await interaction.followup.send(
                f"❌ An error occurred while processing the unban: {str(e)}", 
                ephemeral=True
            )
        except Exception as e:
            # Let the global error handler handle other exceptions
            await self.error_handler.handle_command_error(interaction, e, "unban")
    #=============================================================================================================================================================
    
    # USER LOOKUP COMMAND (useful for finding banned users)
    #=============================================================================================================================================================
    @nextcord.slash_command(
        name="banlookup", 
        description="Look up a user in the ban list"
    )
    async def ban_lookup(
        self, 
        interaction: Interaction, 
        query: str = SlashOption(
            description="Username or ID to search for in the ban list",
            required=True
        )
    ):
        """
        Searches for a banned user by username or partial ID.
        
        Parameters:
        -----------
        interaction: The slash command interaction
        query: Username or user ID to search for in the ban list
        """
        try:
            # Check if the user has ban permissions
            if not interaction.user.guild_permissions.ban_members:
                await interaction.response.send_message(
                    "❌ You don't have permission to view the ban list.", 
                    ephemeral=True
                )
                return
                
            # Check if the bot has ban permissions
            if not interaction.guild.me.guild_permissions.ban_members:
                await interaction.response.send_message(
                    "❌ I don't have permission to access the ban list. Please check my role permissions.", 
                    ephemeral=True
                )
                return
                
            # Use defer as fetching the ban list might take time
            await interaction.response.defer(ephemeral=True)
            
            # Fetch the ban list
            ban_entries = [ban_entry async for ban_entry in interaction.guild.bans()]
            
            if not ban_entries:
                await interaction.followup.send(
                    "ℹ️ There are no banned users in this server.", 
                    ephemeral=True
                )
                return
                
            # Search for the query in usernames or IDs
            query = query.lower()
            results = []
            
            # Check if query is a number (potential ID)
            is_id_query = query.isdigit()
            
            for ban_entry in ban_entries:
                user = ban_entry.user
                username_matches = query in user.name.lower()
                
                # For ID queries, check if the ID contains the query
                id_matches = is_id_query and query in str(user.id)
                
                if username_matches or id_matches:
                    results.append(ban_entry)
                    
                # Limit results to avoid big responses
                if len(results) >= 10:
                    break
                    
            if not results:
                await interaction.followup.send(
                    f"❌ No banned users found matching '{query}'.", 
                    ephemeral=True
                )
                return
                
            # Create embed with results
            embed = nextcord.Embed(
                title="🔍 Ban List Search Results",
                description=f"Found {len(results)} banned user{'s' if len(results) != 1 else ''} matching '{query}':",
                color=nextcord.Color.blue(),
                timestamp=interaction.created_at
            )
            
            for i, ban_entry in enumerate(results):
                user = ban_entry.user
                reason = ban_entry.reason or "No reason provided"
                
                # Format the entry with user info and ban reason
                embed.add_field(
                    name=f"{i+1}. {user.name} (ID: {user.id})",
                    value=f"**Reason:** {reason}\n**Unban command:** `/unban {user.id}`",
                    inline=False
                )
                
            if len(results) == 10:
                embed.set_footer(text="Showing first 10 results. Please refine your search for more specific results.")
            else:
                embed.set_footer(text=f"Showing all {len(results)} results")
                
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except nextcord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to access the ban list.", 
                ephemeral=True
            )
        except Exception as e:
            # Let the global error handler handle other exceptions
            await self.error_handler.handle_command_error(interaction, e, "banlookup")
    #=============================================================================================================================================================
    