import nextcord
from nextcord import Interaction
from nextcord.ext import commands
import asyncio

class Role(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    #=============================================================================================================================================================
    @nextcord.slash_command(name="role", description="Manage roles")
    async def role(self, interaction: Interaction):
        pass
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    @role.subcommand(name="add", description="Add a role to a user or all users")
    async def add_role(self, interaction: Interaction, 
                      role: nextcord.Role, 
                      user: nextcord.Member = nextcord.SlashOption(required=False, description="Leave empty to add the role to all members")):
        # Check permissions first
        if not interaction.user.guild_permissions.manage_roles:
            embed = nextcord.Embed(title="⛔ Permission Denied", 
                                  description="You need the 'Manage Roles' permission to use this command.",
                                  color=nextcord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        # Check if bot has permission to manage this role
        if role.position >= interaction.guild.me.top_role.position:
            embed = nextcord.Embed(title="⛔ Cannot Assign Role", 
                                  description=f"I cannot assign roles that are higher than or equal to my highest role.",
                                  color=nextcord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        try:
            # If adding to a specific user
            if user:
                # Check if user already has role
                if role in user.roles:
                    embed = nextcord.Embed(title="Role Already Assigned", 
                                          description=f"{user.mention} already has the {role.mention} role.",
                                          color=nextcord.Color.yellow())
                    return await interaction.response.send_message(embed=embed)
                    
                # Add role to the user
                await user.add_roles(role)
                embed = nextcord.Embed(title="✅ Role Added", color=nextcord.Color.green())
                embed.add_field(name="User", value=user.mention, inline=True)
                embed.add_field(name="Role", value=role.mention, inline=True)
                await interaction.response.send_message(embed=embed)
            
            # If adding to all users
            else:
                # Ask for confirmation first - this is a bulk operation
                confirm_embed = nextcord.Embed(title="⚠️ Confirmation Required", 
                                             description=f"Are you sure you want to add the {role.mention} role to **all members** in the server? This may take some time for larger servers.",
                                             color=nextcord.Color.yellow())
                confirm_embed.set_footer(text="This operation will time out in 30 seconds.")
                
                # Create confirm/cancel buttons
                view = ConfirmView(timeout=30.0)
                await interaction.response.send_message(embed=confirm_embed, view=view)
                
                # Wait for the view to timeout or for a button to be pressed
                await view.wait()
                
                # If the user didn't confirm, abort
                if not view.value:
                    return await interaction.edit_original_message(
                        embed=nextcord.Embed(title="Operation Cancelled", 
                                           description="Role addition to all members was cancelled.",
                                           color=nextcord.Color.grey()),
                        view=None)
                
                # If confirmed, proceed with adding roles
                await interaction.edit_original_message(
                    embed=nextcord.Embed(title="🔄 Processing", 
                                       description=f"Adding {role.mention} to all members. This may take some time...",
                                       color=nextcord.Color.blue()),
                    view=None)
                
                # Keep track of progress
                total_members = len(interaction.guild.members)
                added_count = 0
                already_had = 0
                
                for member in interaction.guild.members:
                    # Skip bots if needed (optional, comment out if bots should also get the role)
                    # if member.bot:
                    #     continue
                        
                    if role not in member.roles:
                        try:
                            await member.add_roles(role)
                            added_count += 1
                        except:
                            continue  # Skip if we can't add to this member
                    else:
                        already_had += 1
                
                # Send completion message
                embed = nextcord.Embed(title="✅ Bulk Role Addition Complete", color=nextcord.Color.green())
                embed.add_field(name="Role", value=role.mention, inline=True)
                embed.add_field(name="Added to", value=f"{added_count} members", inline=True)
                if already_had > 0:
                    embed.add_field(name="Already had role", value=f"{already_had} members", inline=True)
                embed.set_footer(text=f"Processed {total_members} members in total")
                
                await interaction.edit_original_message(embed=embed)
                
        except nextcord.Forbidden:
            embed = nextcord.Embed(title="⛔ Permission Error", 
                                  description="I don't have permission to manage roles for one or more users.",
                                  color=nextcord.Color.red())
            if interaction.response.is_done():
                await interaction.edit_original_message(embed=embed)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            embed = nextcord.Embed(title="❌ Error", 
                                  description=f"An error occurred: {str(e)}",
                                  color=nextcord.Color.red())
            if interaction.response.is_done():
                await interaction.edit_original_message(embed=embed)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    @role.subcommand(name="remove", description="Remove a role from a user or all users")
    async def remove_role(self, interaction: Interaction, 
                         role: nextcord.Role, 
                         user: nextcord.Member = nextcord.SlashOption(required=False, description="Leave empty to remove the role from all members")):
        # Check permissions first
        if not interaction.user.guild_permissions.manage_roles:
            embed = nextcord.Embed(title="⛔ Permission Denied", 
                                  description="You need the 'Manage Roles' permission to use this command.",
                                  color=nextcord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        # Check if bot has permission to manage this role
        if role.position >= interaction.guild.me.top_role.position:
            embed = nextcord.Embed(title="⛔ Cannot Remove Role", 
                                  description=f"I cannot manage roles that are higher than or equal to my highest role.",
                                  color=nextcord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        try:
            # If removing from a specific user
            if user:
                # Check if user has the role
                if role not in user.roles:
                    embed = nextcord.Embed(title="Role Not Found", 
                                          description=f"{user.mention} doesn't have the {role.mention} role.",
                                          color=nextcord.Color.yellow())
                    return await interaction.response.send_message(embed=embed)
                    
                # Remove role from the user
                await user.remove_roles(role)
                embed = nextcord.Embed(title="✅ Role Removed", color=nextcord.Color.red())
                embed.add_field(name="User", value=user.mention, inline=True)
                embed.add_field(name="Role", value=role.mention, inline=True)
                await interaction.response.send_message(embed=embed)
            
            # If removing from all users
            else:
                # Ask for confirmation first - this is a bulk operation
                confirm_embed = nextcord.Embed(title="⚠️ Confirmation Required", 
                                             description=f"Are you sure you want to remove the {role.mention} role from **all members** in the server? This may take some time for larger servers.",
                                             color=nextcord.Color.yellow())
                confirm_embed.set_footer(text="This operation will time out in 30 seconds.")
                
                # Create confirm/cancel buttons
                view = ConfirmView(timeout=30.0)
                await interaction.response.send_message(embed=confirm_embed, view=view)
                
                # Wait for the view to timeout or for a button to be pressed
                await view.wait()
                
                # If the user didn't confirm, abort
                if not view.value:
                    return await interaction.edit_original_message(
                        embed=nextcord.Embed(title="Operation Cancelled", 
                                           description="Role removal from all members was cancelled.",
                                           color=nextcord.Color.grey()),
                        view=None)
                
                # If confirmed, proceed with removing roles
                await interaction.edit_original_message(
                    embed=nextcord.Embed(title="🔄 Processing", 
                                       description=f"Removing {role.mention} from all members. This may take some time...",
                                       color=nextcord.Color.blue()),
                    view=None)
                
                # Keep track of progress
                total_members = len(interaction.guild.members)
                removed_count = 0
                didnt_have = 0
                
                for member in interaction.guild.members:
                    if role in member.roles:
                        try:
                            await member.remove_roles(role)
                            removed_count += 1
                        except:
                            continue  # Skip if we can't remove from this member
                    else:
                        didnt_have += 1
                
                # Send completion message
                embed = nextcord.Embed(title="✅ Bulk Role Removal Complete", color=nextcord.Color.red())
                embed.add_field(name="Role", value=role.mention, inline=True)
                embed.add_field(name="Removed from", value=f"{removed_count} members", inline=True)
                if didnt_have > 0:
                    embed.add_field(name="Didn't have role", value=f"{didnt_have} members", inline=True)
                embed.set_footer(text=f"Processed {total_members} members in total")
                
                await interaction.edit_original_message(embed=embed)
                
        except nextcord.Forbidden:
            embed = nextcord.Embed(title="⛔ Permission Error", 
                                  description="I don't have permission to manage roles for one or more users.",
                                  color=nextcord.Color.red())
            if interaction.response.is_done():
                await interaction.edit_original_message(embed=embed)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            embed = nextcord.Embed(title="❌ Error", 
                                  description=f"An error occurred: {str(e)}",
                                  color=nextcord.Color.red())
            if interaction.response.is_done():
                await interaction.edit_original_message(embed=embed)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    @role.subcommand(name="info", description="Get information about a role")
    async def role_info(self, interaction: Interaction, role: nextcord.Role):
        try:
            # Get role details
            embed = nextcord.Embed(title=f"Role Information: {role.name}", 
                                  color=role.color)
            
            # Basic information
            embed.add_field(name="ID", value=role.id, inline=True)
            embed.add_field(name="Color", value=f"#{role.color.value:06x}", inline=True)
            embed.add_field(name="Position", value=role.position, inline=True)
            
            # Role properties
            properties = []
            if role.hoist:
                properties.append("Displayed separately")
            if role.mentionable:
                properties.append("Mentionable")
            if role.managed:
                properties.append("Managed by integration")
            
            embed.add_field(name="Properties", value=", ".join(properties) if properties else "None", inline=False)
            
            # Member count
            member_count = len([m for m in interaction.guild.members if role in m.roles])
            embed.add_field(name="Members", value=f"{member_count} members have this role", inline=False)
            
            # Created date
            embed.add_field(name="Created", value=f"<t:{int(role.created_at.timestamp())}:F>", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            embed = nextcord.Embed(title="❌ Error", 
                                  description=f"An error occurred: {str(e)}",
                                  color=nextcord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    @role.subcommand(name="list", description="List all members with a specific role")
    async def list_role_members(self, interaction: Interaction, role: nextcord.Role):
        try:
            # Get all members with this role
            members_with_role = [member for member in interaction.guild.members if role in member.roles]
            
            if not members_with_role:
                embed = nextcord.Embed(title=f"Role Members: {role.name}", 
                                      description="No members have this role.",
                                      color=role.color)
                return await interaction.response.send_message(embed=embed)
            
            # Create the initial embed
            embed = nextcord.Embed(title=f"Role Members: {role.name}", 
                                  description=f"**{len(members_with_role)}** members have this role",
                                  color=role.color)
            
            # For large member lists, we'll need to paginate
            if len(members_with_role) > 20:
                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title=f"Role Members: {role.name}",
                        description=f"**{len(members_with_role)}** members have this role. Generating member list...",
                        color=role.color
                    )
                )
                
                # Create paginated embeds
                pages = []
                for i in range(0, len(members_with_role), 20):
                    page_embed = nextcord.Embed(title=f"Role Members: {role.name}", 
                                              description=f"**{len(members_with_role)}** members have this role",
                                              color=role.color)
                    
                    members_text = "\n".join([f"{idx+1+i}. {member.mention} ({member.name})" 
                                            for idx, member in enumerate(members_with_role[i:i+20])])
                    page_embed.add_field(name=f"Members (Page {i//20 + 1}/{(len(members_with_role)-1)//20 + 1})", 
                                        value=members_text, 
                                        inline=False)
                    
                    pages.append(page_embed)
                
                # Create pagination view
                view = PaginationView(pages)
                await interaction.edit_original_message(embed=pages[0], view=view)
            else:
                # If we have 20 or fewer members, just list them all in one embed
                members_text = "\n".join([f"{idx+1}. {member.mention} ({member.name})" 
                                        for idx, member in enumerate(members_with_role)])
                embed.add_field(name="Members", value=members_text, inline=False)
                
                await interaction.response.send_message(embed=embed)
        
        except Exception as e:
            embed = nextcord.Embed(title="❌ Error", 
                                  description=f"An error occurred: {str(e)}",
                                  color=nextcord.Color.red())
            if interaction.response.is_done():
                await interaction.edit_original_message(embed=embed)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
    #=============================================================================================================================================================
    
# Confirmation View for bulk operations
class ConfirmView(nextcord.ui.View):
    def __init__(self, timeout=180.0):
        super().__init__(timeout=timeout)
        self.value = None
        
    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: Interaction):
        self.value = True
        self.stop()
        
    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red)
    async def cancel(self, button: nextcord.ui.Button, interaction: Interaction):
        self.value = False
        self.stop()

# Pagination View for member lists
class PaginationView(nextcord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=180.0)
        self.pages = pages
        self.current_page = 0
        
    @nextcord.ui.button(label="Previous", style=nextcord.ButtonStyle.grey)
    async def previous_page(self, button: nextcord.ui.Button, interaction: Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.pages[self.current_page])
        else:
            await interaction.response.send_message("You are already on the first page.", ephemeral=True)
        
    @nextcord.ui.button(label="Next", style=nextcord.ButtonStyle.grey)
    async def next_page(self, button: nextcord.ui.Button, interaction: Interaction):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.pages[self.current_page])
        else:
            await interaction.response.send_message("You are already on the last page.", ephemeral=True)
