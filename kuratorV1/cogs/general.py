import discord
from discord import app_commands
from discord.ext import commands
import platform
import time
import datetime

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="invite", description="Get the bot's invite link")
    async def invite(self, interaction: discord.Interaction):
        """Get the bot's invite link"""
        # This is a placeholder - replace with your actual invite link if you have one
        invite_link = "https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&scope=bot%20applications.commands"
        
        embed = discord.Embed(
            title="Invite Empire IV Bot",
            description=f"[Click here to invite the bot to your server]({invite_link})",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        """Check the bot's latency"""
        start_time = time.time()
        await interaction.response.send_message("Pinging...")
        
        end_time = time.time()
        latency = round((end_time - start_time) * 1000)
        websocket_latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(title="Pong! 🏓", color=discord.Color.green())
        embed.add_field(name="API Latency", value=f"{latency}ms", inline=True)
        embed.add_field(name="Websocket Latency", value=f"{websocket_latency}ms", inline=True)
        
        await interaction.edit_original_response(content="", embed=embed)
        
    @app_commands.command(name="serverinfo", description="Get information about the server")
    async def serverinfo(self, interaction: discord.Interaction):
        """Get information about the server"""
        guild = interaction.guild
        
        # Gather server information
        total_members = len(guild.members)
        total_text_channels = len(guild.text_channels)
        total_voice_channels = len(guild.voice_channels)
        total_categories = len(guild.categories)
        server_owner = guild.owner.mention if guild.owner else "Unknown"
        server_created_at = guild.created_at.strftime("%d %B %Y")
        
        # Create an embed with server information
        embed = discord.Embed(
            title=f"{guild.name} Server Information",
            description=guild.description or "No description",
            color=discord.Color.gold()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        embed.add_field(name="Owner", value=server_owner, inline=True)
        embed.add_field(name="Created On", value=server_created_at, inline=True)
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Members", value=total_members, inline=True)
        embed.add_field(name="Text Channels", value=total_text_channels, inline=True)
        embed.add_field(name="Voice Channels", value=total_voice_channels, inline=True)
        embed.add_field(name="Categories", value=total_categories, inline=True)
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="userinfo", description="Get information about a user")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        """Get information about a user"""
        # If no member is specified, use the command invoker
        member = member or interaction.user
        
        # Gather member information
        joined_at = member.joined_at.strftime("%d %B %Y") if member.joined_at else "Unknown"
        created_at = member.created_at.strftime("%d %B %Y")
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        roles_str = ", ".join(roles) if roles else "No roles"
        
        # Create an embed with user information
        embed = discord.Embed(
            title=f"User Information - {member.name}",
            color=member.color
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="Display Name", value=member.display_name, inline=True)
        embed.add_field(name="Account Created", value=created_at, inline=True)
        embed.add_field(name="Joined Server", value=joined_at, inline=True)
        embed.add_field(name="Roles", value=roles_str, inline=False)
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="commands", description="List all available commands")
    async def commands(self, interaction: discord.Interaction):
        """List all available commands"""
        # Create a dictionary to group commands by cog
        cogs_dict = {}
        
        # Iterate through the app commands
        for command in self.bot.tree.walk_commands():
            # Get the cog name, or use 'Other' if the command doesn't belong to a cog
            cog_name = command.extras.get('cog_name', 'Other')
            
            # Add the command to the corresponding cog in the dictionary
            if cog_name not in cogs_dict:
                cogs_dict[cog_name] = []
            
            # Add the command and its description
            cogs_dict[cog_name].append(f"/{command.name} - {command.description}")
        
        # Create an embed to display the commands
        embed = discord.Embed(
            title="Available Commands",
            description="Here's a list of all available commands grouped by category:",
            color=discord.Color.blue()
        )
        
        # Add each cog's commands to the embed
        for cog_name, commands_list in cogs_dict.items():
            # Skip empty categories
            if not commands_list:
                continue
            
            # Add the cog's commands as a field
            commands_text = "\n".join(commands_list)
            embed.add_field(name=cog_name, value=commands_text, inline=False)
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="help", description="Get help and information about the bot")
    async def help(self, interaction: discord.Interaction):
        """Get help and information about the bot"""
        embed = discord.Embed(
            title="Empire IV - Diplomacy Bot",
            description="Welcome to the Empire IV Diplomacy Bot! This bot helps manage diplomatic relations, trade, and development in the Empire IV roleplaying game.",
            color=discord.Color.blue()
        )
        
        # Add sections for each major feature
        embed.add_field(
            name="📜 Treaties",
            value="Create and manage diplomatic treaties between nations using `/create_treaty` and `/list_treaties`.",
            inline=False
        )
        
        embed.add_field(
            name="💰 Trade",
            value="Establish trade agreements between nations using `/create_trade`.",
            inline=False
        )
        
        embed.add_field(
            name="🏗️ Development",
            value="Develop your nation's infrastructure, economy, and military using `/develop`.",
            inline=False
        )
        
        embed.add_field(
            name="🛠️ General Commands",
            value="Use `/commands` to see a full list of available commands.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))