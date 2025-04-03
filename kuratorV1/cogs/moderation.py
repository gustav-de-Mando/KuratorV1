import discord
from discord import app_commands
from discord.ext import commands
import config

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def is_moderator(self, member: discord.Member) -> bool:
        """Check if a member has a moderator role"""
        return any(role.name in config.MOD_ROLES for role in member.roles)
    
    @app_commands.command(name="kick", description="Kick a member from the server")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        """Kick a member from the server"""
        # Check if the user has permission
        if not interaction.user.guild_permissions.kick_members and not self.is_moderator(interaction.user):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        
        # Check if the bot has permission
        if not interaction.guild.me.guild_permissions.kick_members:
            await interaction.response.send_message("I don't have permission to kick members.", ephemeral=True)
            return
        
        # Check if the target is the user themselves
        if member.id == interaction.user.id:
            await interaction.response.send_message("You cannot kick yourself.", ephemeral=True)
            return
        
        # Check if the target is higher in the role hierarchy
        if interaction.user.top_role <= member.top_role and interaction.guild.owner_id != interaction.user.id:
            await interaction.response.send_message("You cannot kick someone with a higher or equal role.", ephemeral=True)
            return
        
        # Create an embed for the kick message
        embed = discord.Embed(title="Member Kicked", color=discord.Color.red())
        embed.add_field(name="Member", value=f"{member.mention} ({member.name}#{member.discriminator})", inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        
        # Try to send a DM to the user
        try:
            dm_embed = discord.Embed(
                title=f"You have been kicked from {interaction.guild.name}",
                color=discord.Color.red()
            )
            if reason:
                dm_embed.add_field(name="Reason", value=reason)
            
            await member.send(embed=dm_embed)
        except:
            # If DM fails, don't interrupt the kick process
            pass
        
        # Kick the member
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to kick that member.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"An error occurred while kicking the member: {e}", ephemeral=True)
    
    @app_commands.command(name="ban", description="Ban a member from the server")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        """Ban a member from the server"""
        # Check if the user has permission
        if not interaction.user.guild_permissions.ban_members and not self.is_moderator(interaction.user):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        
        # Check if the bot has permission
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message("I don't have permission to ban members.", ephemeral=True)
            return
        
        # Check if the target is the user themselves
        if member.id == interaction.user.id:
            await interaction.response.send_message("You cannot ban yourself.", ephemeral=True)
            return
        
        # Check if the target is higher in the role hierarchy
        if interaction.user.top_role <= member.top_role and interaction.guild.owner_id != interaction.user.id:
            await interaction.response.send_message("You cannot ban someone with a higher or equal role.", ephemeral=True)
            return
        
        # Create an embed for the ban message
        embed = discord.Embed(title="Member Banned", color=discord.Color.dark_red())
        embed.add_field(name="Member", value=f"{member.mention} ({member.name}#{member.discriminator})", inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        
        # Try to send a DM to the user
        try:
            dm_embed = discord.Embed(
                title=f"You have been banned from {interaction.guild.name}",
                color=discord.Color.dark_red()
            )
            if reason:
                dm_embed.add_field(name="Reason", value=reason)
            
            await member.send(embed=dm_embed)
        except:
            # If DM fails, don't interrupt the ban process
            pass
        
        # Ban the member
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban that member.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"An error occurred while banning the member: {e}", ephemeral=True)

    @app_commands.command(name="clear", description="Clear a specified number of messages")
    async def clear(self, interaction: discord.Interaction, amount: int):
        """Clear a specified number of messages"""
        # Check if the user has permission
        if not interaction.user.guild_permissions.manage_messages and not self.is_moderator(interaction.user):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        
        # Check if the bot has permission
        if not interaction.guild.me.guild_permissions.manage_messages:
            await interaction.response.send_message("I don't have permission to delete messages.", ephemeral=True)
            return
        
        # Limit the amount to a reasonable number
        if amount <= 0:
            await interaction.response.send_message("Please specify a positive number of messages to delete.", ephemeral=True)
            return
        
        if amount > 100:
            amount = 100  # Discord API limits purge to 100 messages at a time
        
        # Defer the response since this might take a moment
        await interaction.response.defer(ephemeral=True)
        
        # Delete the messages
        try:
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"Successfully deleted {len(deleted)} messages.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to delete messages in this channel.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f"An error occurred while deleting messages: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))