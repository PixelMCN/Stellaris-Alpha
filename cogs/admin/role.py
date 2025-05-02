import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
from typing import List, Optional, Union

from utils.embed_helper import EmbedHelper
from utils.error_handler import ErrorHandler
from utils.time_helper import TimeHelper
#=============================================================================================================================================================
class RoleView(nextcord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
        self.value = None
    
    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green, emoji="✅")
    async def confirm(self, button: nextcord.ui.Button, interaction: Interaction):
        self.value = True
        self.stop()
    
    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red, emoji="❌")
    async def cancel(self, button: nextcord.ui.Button, interaction: Interaction):
        self.value = False
        self.stop()
#=============================================================================================================================================================
class RoleCommands(commands.Cog):
    """Commands for managing server roles"""
    
    def __init__(self, bot):
        self.bot = bot
        self.error_handler = ErrorHandler(bot)
    #=============================================================================================================================================================
    @nextcord.slash_command(name="role", description="Manage server roles")
    async def role(self, interaction: Interaction):
        """Base command for role management"""
        pass
    
    async def check_role_permissions(self, interaction: Interaction, role: nextcord.Role, action: str = "modify") -> bool:
        """Check if the user and bot have appropriate permissions to modify roles"""
        # Check if user has manage roles permission
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=EmbedHelper.permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return False
        
        # Check if bot has permission to manage roles
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=EmbedHelper.bot_permission_error_embed("Manage Roles"),
                ephemeral=True
            )
            return False
        
        # Check if the role is higher than the bot's highest role
        if role.position >= interaction.guild.me.top_role.position:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Role Hierarchy Error",
                    f"I cannot {action} roles that are higher than or equal to my highest role."
                ),
                ephemeral=True
            )
            return False
        
        # Check if the role is higher than the user's highest role (unless they're the owner)
        if role.position >= interaction.user.top_role.position and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                embed=EmbedHelper.error_embed(
                    "Role Hierarchy Error",
                    f"You cannot {action} roles that are higher than or equal to your highest role."
                ),
                ephemeral=True
            )
            return False
        
        return True
    
    async def parse_users(self, interaction: Interaction, users_input: str) -> List[Union[nextcord.Member, int]]:
        """Parse user mentions and IDs from input string"""
        user_ids = []
        
        # Special case for "all" or "@everyone"
        if users_input.lower() in ["all", "everyone", "@everyone"]:
            return "all"
        
        for word in users_input.split():
            # Remove mention formatting and extract ID
            user_id = word.strip("<@!&>")
            if user_id.isdigit():
                user_ids.append(int(user_id))
        
        return user_ids
    
    async def get_members_from_ids(self, interaction: Interaction, user_ids: List[int]) -> tuple:
        """Convert user IDs to member objects"""
        members = []
        failed_ids = []
        
        for user_id in user_ids:
            try:
                member = await interaction.guild.fetch_member(user_id)
                members.append(member)
            except nextcord.errors.NotFound:
                failed_ids.append(user_id)
        
        return members, failed_ids
    #=============================================================================================================================================================
    @role.subcommand(name="add", description="Add a role to users")
    async def role_add(
        self,
        interaction: Interaction,
        role: nextcord.Role = SlashOption(description="The role to add"),
        users: str = SlashOption(
            description="Users to add the role to (mention or IDs, space separated) or 'all' for everyone"
        ),
        reason: str = SlashOption(description="Reason for adding the role", required=False)
    ):
        """Add a role to one, multiple, or all users"""
        # Check permissions
        if not await self.check_role_permissions(interaction, role, "assign"):
            return
        
        # Parse users input
        parsed_users = await self.parse_users(interaction, users)
        
        # Handle "all users" case
        if parsed_users == "all":
            # Ask for confirmation first
            embed = EmbedHelper.warning_embed(
                "Confirm Mass Role Assignment",
                f"Are you sure you want to add {role.mention} to **ALL** members in the server? "
                f"This will affect **{len(interaction.guild.members)}** members and may take a long time."
            )
            view = RoleView()
            
            await interaction.response.send_message(embed=embed, view=view)
            await view.wait()
            
            if not view.value:
                await interaction.edit_original_message(
                    embed=EmbedHelper.info_embed("Operation Cancelled", "Role assignment cancelled."),
                    view=None
                )
                return
            
            # Use all guild members
            target_members = interaction.guild.members
            await interaction.edit_original_message(
                embed=EmbedHelper.info_embed(
                    "Processing",
                    f"Adding {role.mention} to all members. This may take some time..."
                ),
                view=None
            )
        else:
            # Handle empty user list
            if not parsed_users:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Invalid Users",
                        "No valid user mentions or IDs were provided. Use mentions, IDs, or 'all' for everyone."
                    ),
                    ephemeral=True
                )
                return
            
            # Get member objects
            target_members, failed_ids = await self.get_members_from_ids(interaction, parsed_users)
            
            # If no valid members were found
            if not target_members:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Invalid Users",
                        "None of the provided user IDs could be found in this server."
                    ),
                    ephemeral=True
                )
                return
            
            # Ask for confirmation if adding role to many users
            if len(target_members) > 5:
                embed = EmbedHelper.warning_embed(
                    "Confirm Role Assignment",
                    f"Are you sure you want to add {role.mention} to **{len(target_members)}** members?"
                )
                view = RoleView()
                
                await interaction.response.send_message(embed=embed, view=view)
                await view.wait()
                
                if not view.value:
                    await interaction.edit_original_message(
                        embed=EmbedHelper.info_embed("Operation Cancelled", "Role assignment cancelled."),
                        view=None
                    )
                    return
                
                await interaction.edit_original_message(
                    embed=EmbedHelper.info_embed("Processing", "Adding roles to members..."),
                    view=None
                )
            else:
                await interaction.response.defer(ephemeral=False)
        
        # Process each user
        success_users = []
        failed_users = []
        already_had_role = []
        
        for member in target_members:
            try:
                # Skip bot user
                if member.bot:
                    continue
                    
                # Check if user already has the role
                if role in member.roles:
                    already_had_role.append(member)
                    continue
                
                # Add the role
                await member.add_roles(
                    role, 
                    reason=f"Role added by {interaction.user} ({interaction.user.id})" + 
                           (f" | Reason: {reason}" if reason else "")
                )
                success_users.append(member)
            except Exception as e:
                failed_users.append(f"{member.mention} (Error: {str(e)[:50]})")
        
        # Create response embed
        if success_users:
            # Create embed
            embed = EmbedHelper.success_embed(
                "Role Added",
                f"Successfully added {role.mention} to {len(success_users)} member(s)."
            )
            
            # Add users field (with appropriate limiting for large operations)
            if len(success_users) <= 20:
                user_mentions = [user.mention for user in success_users]
                users_text = ", ".join(user_mentions)
                embed.add_field(name="Members", value=users_text, inline=False)
            else:
                embed.add_field(
                    name="Members",
                    value=f"Added role to {len(success_users)} members (too many to list)",
                    inline=False
                )
            
            # Add reason if provided
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            # Add moderator field
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Date", value=f"<t:{int(TimeHelper.now().timestamp())}:F>", inline=True)
            
            # Add already had role field if applicable
            if already_had_role:
                if len(already_had_role) <= 20:
                    already_had_text = ", ".join([user.mention for user in already_had_role])
                else:
                    already_had_text = f"{len(already_had_role)} members already had this role"
                embed.add_field(name="Already Had Role", value=already_had_text, inline=False)
            
            # Add failed users field if applicable
            if failed_users:
                if len(failed_users) <= 10:
                    failed_text = "\n".join(failed_users)
                else:
                    failed_text = f"Failed to add role to {len(failed_users)} members"
                embed.add_field(name="Failed", value=failed_text, inline=False)
            
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=embed)
            except:
                pass
                
            # Handle the follow-up message
            if hasattr(interaction, 'edit_original_message'):
                await interaction.edit_original_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
        else:
            # If no successful role additions
            if already_had_role and not failed_users:
                embed = EmbedHelper.info_embed(
                    "No Changes Made",
                    f"All specified members already had the {role.mention} role."
                )
            elif failed_users and not already_had_role:
                embed = EmbedHelper.error_embed(
                    "Failed to Add Role",
                    f"Could not add {role.mention} to any of the specified members."
                )
            else:
                embed = EmbedHelper.warning_embed(
                    "Partial Failure",
                    f"Some members already had the role and others could not be modified."
                )
                
            # Handle the follow-up message
            if hasattr(interaction, 'edit_original_message'):
                await interaction.edit_original_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
    #=============================================================================================================================================================
    @role.subcommand(name="remove", description="Remove a role from users")
    async def role_remove(
        self,
        interaction: Interaction,
        role: nextcord.Role = SlashOption(description="The role to remove"),
        users: str = SlashOption(
            description="Users to remove the role from (mention or IDs, space separated) or 'all' for everyone"
        ),
        reason: str = SlashOption(description="Reason for removing the role", required=False)
    ):
        """Remove a role from one, multiple, or all users"""
        # Check permissions
        if not await self.check_role_permissions(interaction, role, "remove"):
            return
        
        # Parse users input
        parsed_users = await self.parse_users(interaction, users)
        
        # Handle "all users" case
        if parsed_users == "all":
            # Ask for confirmation first
            embed = EmbedHelper.warning_embed(
                "Confirm Mass Role Removal",
                f"Are you sure you want to remove {role.mention} from **ALL** members who have it? "
                f"This may take a long time."
            )
            view = RoleView()
            
            await interaction.response.send_message(embed=embed, view=view)
            await view.wait()
            
            if not view.value:
                await interaction.edit_original_message(
                    embed=EmbedHelper.info_embed("Operation Cancelled", "Role removal cancelled."),
                    view=None
                )
                return
            
            # Get all members with the role
            target_members = role.members
            await interaction.edit_original_message(
                embed=EmbedHelper.info_embed(
                    "Processing",
                    f"Removing {role.mention} from {len(target_members)} members. This may take some time..."
                ),
                view=None
            )
        else:
            # Handle empty user list
            if not parsed_users:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Invalid Users",
                        "No valid user mentions or IDs were provided. Use mentions, IDs, or 'all' for everyone with the role."
                    ),
                    ephemeral=True
                )
                return
            
            # Get member objects
            target_members, failed_ids = await self.get_members_from_ids(interaction, parsed_users)
            
            # If no valid members were found
            if not target_members:
                await interaction.response.send_message(
                    embed=EmbedHelper.error_embed(
                        "Invalid Users",
                        "None of the provided user IDs could be found in this server."
                    ),
                    ephemeral=True
                )
                return
            
            # Ask for confirmation if removing role from many users
            if len(target_members) > 5:
                embed = EmbedHelper.warning_embed(
                    "Confirm Role Removal",
                    f"Are you sure you want to remove {role.mention} from **{len(target_members)}** members?"
                )
                view = RoleView()
                
                await interaction.response.send_message(embed=embed, view=view)
                await view.wait()
                
                if not view.value:
                    await interaction.edit_original_message(
                        embed=EmbedHelper.info_embed("Operation Cancelled", "Role removal cancelled."),
                        view=None
                    )
                    return
                
                await interaction.edit_original_message(
                    embed=EmbedHelper.info_embed("Processing", "Removing roles from members..."),
                    view=None
                )
            else:
                await interaction.response.defer(ephemeral=False)
        
        # Process each user
        success_users = []
        failed_users = []
        didnt_have_role = []
        
        for member in target_members:
            try:
                # Check if user doesn't have the role
                if role not in member.roles:
                    didnt_have_role.append(member)
                    continue
                
                # Remove the role
                await member.remove_roles(
                    role, 
                    reason=f"Role removed by {interaction.user} ({interaction.user.id})" + 
                           (f" | Reason: {reason}" if reason else "")
                )
                success_users.append(member)
            except Exception as e:
                failed_users.append(f"{member.mention} (Error: {str(e)[:50]})")
        
        # Create response embed
        if success_users:
            # Create embed
            embed = EmbedHelper.success_embed(
                "Role Removed",
                f"Successfully removed {role.mention} from {len(success_users)} member(s)."
            )
            
            # Add users field (with appropriate limiting for large operations)
            if len(success_users) <= 20:
                user_mentions = [user.mention for user in success_users]
                users_text = ", ".join(user_mentions)
                embed.add_field(name="Members", value=users_text, inline=False)
            else:
                embed.add_field(
                    name="Members",
                    value=f"Removed role from {len(success_users)} members (too many to list)",
                    inline=False
                )
            
            # Add reason if provided
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            # Add moderator field
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Date", value=f"<t:{int(TimeHelper.now().timestamp())}:F>", inline=True)
            
            # Add didn't have role field if applicable
            if didnt_have_role:
                if len(didnt_have_role) <= 20:
                    didnt_have_text = ", ".join([user.mention for user in didnt_have_role])
                else:
                    didnt_have_text = f"{len(didnt_have_role)} members didn't have this role"
                embed.add_field(name="Didn't Have Role", value=didnt_have_text, inline=False)
            
            # Add failed users field if applicable
            if failed_users:
                if len(failed_users) <= 10:
                    failed_text = "\n".join(failed_users)
                else:
                    failed_text = f"Failed to remove role from {len(failed_users)} members"
                embed.add_field(name="Failed", value=failed_text, inline=False)
            
            # Try to send to mod-logs channel if it exists
            try:
                log_channel = nextcord.utils.get(interaction.guild.channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(embed=embed)
            except:
                pass
                
            # Handle the follow-up message
            if hasattr(interaction, 'edit_original_message'):
                await interaction.edit_original_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
        else:
            # If no successful role removals
            if didnt_have_role and not failed_users:
                embed = EmbedHelper.info_embed(
                    "No Changes Made",
                    f"None of the specified members had the {role.mention} role."
                )
            elif failed_users and not didnt_have_role:
                embed = EmbedHelper.error_embed(
                    "Failed to Remove Role",
                    f"Could not remove {role.mention} from any of the specified members."
                )
            else:
                embed = EmbedHelper.warning_embed(
                    "Partial Failure",
                    f"Some members didn't have the role and others could not be modified."
                )
                
            # Handle the follow-up message
            if hasattr(interaction, 'edit_original_message'):
                await interaction.edit_original_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
    #=============================================================================================================================================================
    @role.subcommand(name="info", description="Get detailed information about a role")
    async def role_info(
        self,
        interaction: Interaction,
        role: nextcord.Role = SlashOption(description="The role to get information about")
    ):
        """Display detailed information about a role"""
        # Get role creation date
        created_at_timestamp = int(role.created_at.timestamp())
        creation_date = f"<t:{created_at_timestamp}:F>"
        role_age = f"<t:{created_at_timestamp}:R>"
        
        # Get role permissions
        permissions = []
        for perm, value in role.permissions:
            if value:
                formatted_perm = perm.replace('_', ' ').title()
                permissions.append(f"`{formatted_perm}`")
        
        permissions_text = ", ".join(permissions) if permissions else "None"
        
        # Get member count with this role
        member_count = len(role.members)
        
        # Create embed
        embed = nextcord.Embed(
            title=f"Role Information: {role.name}",
            description=f"**ID:** {role.id}",
            color=role.color if role.color.value else nextcord.Color.light_grey()
        )
        
        # Role stats
        embed.add_field(name="Color", value=f"#{role.color.value:06x}" if role.color.value else "Default", inline=True)
        embed.add_field(name="Position", value=f"{role.position} (of {len(interaction.guild.roles)})", inline=True)
        embed.add_field(name="Members", value=f"{member_count} member{'' if member_count == 1 else 's'}", inline=True)
        
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="Displayed Separately", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="Managed by Integration", value="Yes" if role.managed else "No", inline=True)
        
        embed.add_field(name="Created", value=f"{creation_date} ({role_age})", inline=False)
        
        # Key permissions - handle with categories for better organization
        key_permission_categories = {
            "Moderation": ["kick_members", "ban_members", "moderate_members", "manage_messages"],
            "Administration": ["administrator", "manage_guild", "manage_roles", "manage_channels", "manage_webhooks"],
            "Voice": ["mute_members", "deafen_members", "move_members", "priority_speaker"],
            "Content": ["mention_everyone", "manage_emojis", "manage_events", "send_messages_in_threads"]
        }
        
        # Group permissions by category for more organized display
        categorized_perms = {}
        for category, perm_list in key_permission_categories.items():
            category_perms = []
            for perm in perm_list:
                if getattr(role.permissions, perm):
                    formatted_perm = perm.replace('_', ' ').title()
                    category_perms.append(f"`{formatted_perm}`")
            
            if category_perms:
                categorized_perms[category] = category_perms
        
        # Add permissions fields by category
        if categorized_perms:
            for category, perms in categorized_perms.items():
                embed.add_field(name=f"{category} Permissions", value=", ".join(perms), inline=False)
        else:
            embed.add_field(name="Permissions", value="This role has no special permissions", inline=False)
        
        # Add administrator warning if applicable
        if role.permissions.administrator:
            embed.add_field(
                name="⚠️ Administrator Role", 
                value="This role has full administrator permissions and can perform any action in the server.",
                inline=False
            )
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        # Add a color block to visualize the role color
        if role.color.value:
            # Create a small color sample using unicode block characters
            color_block = "■" * 12
            embed.description = f"**ID:** {role.id}\n**Color Sample:** {color_block}"
        
        await interaction.response.send_message(embed=embed)
    #=============================================================================================================================================================
    @role.subcommand(name="members", description="Show members who have a specific role")
    async def role_members(
        self,
        interaction: Interaction,
        role: nextcord.Role = SlashOption(description="The role to check members for")
    ):
        """Display all members who have a specific role"""
        # Get members with this role
        members = role.members
        
        if not members:
            embed = EmbedHelper.info_embed(
                f"Role Members: {role.name}",
                f"No members have the {role.mention} role."
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Create embed
        embed = nextcord.Embed(
            title=f"Members with {role.name}",
            description=f"Found {len(members)} member{'' if len(members) == 1 else 's'} with this role",
            color=role.color if role.color.value else nextcord.Color.light_grey()
        )
        
        # Handle large member counts
        if len(members) > 50:
            # Show sample of members
            sample_members = members[:25]
            sample_text = "\n".join([f"• {member.mention} ({member.display_name})" for member in sample_members])
            
            embed.add_field(
                name=f"Sample of Members (showing 25/{len(members)})",
                value=sample_text,
                inline=False
            )
            
            embed.set_footer(text="This role has too many members to display them all")
        else:
            # Split members into chunks of 15 for multiple fields if needed
            chunks = [members[i:i+15] for i in range(0, len(members), 15)]
            
            for i, chunk in enumerate(chunks):
                field_value = "\n".join([f"• {member.mention} ({member.display_name})" for member in chunk])
                embed.add_field(
                    name=f"Members {i+1}" if len(chunks) > 1 else "Members",
                    value=field_value,
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)
#=============================================================================================================================================================