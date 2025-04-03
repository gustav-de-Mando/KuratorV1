import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import setup_logger

logger = setup_logger()

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="invite", description="Get the bot's invite link")
    async def invite(self, interaction: discord.Interaction):
        """Get the bot's invite link"""
        permissions = discord.Permissions(
            kick_members=True,
            ban_members=True,
            manage_messages=True,
            read_messages=True,
            send_messages=True,
            read_message_history=True
        )
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=permissions,
            scopes=("bot", "applications.commands")
        )
        embed = discord.Embed(
            title="Bot Invite Link",
            description=f"To add me to your server with slash commands support, [click here]({invite_url})\n\n"
                       f"Make sure to keep all permissions enabled for full functionality!",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ping", description="Check bot's latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f'Pong! Latency: {latency}ms')

    @app_commands.command(name="serverinfo", description="Display server information")
    async def serverinfo(self, interaction: discord.Interaction):
        server = interaction.guild
        embed = discord.Embed(title=f"{server.name} Info", color=discord.Color.blue())
        embed.add_field(name="Server ID", value=server.id, inline=True)
        embed.add_field(name="Member Count", value=server.member_count, inline=True)
        embed.add_field(name="Created At", value=server.created_at.strftime("%Y-%m-%d"), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Display user information")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(title=f"{member.name}'s Info", color=discord.Color.green())
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Roles", value=len(member.roles), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="commands", description="Zeigt alle verfügbaren Befehle mit Beschreibung")
    async def commands(self, interaction: discord.Interaction):
        try:
            logger.info(f"User {interaction.user.name} requested command list")
            embed = discord.Embed(
                title="🤖 Verfügbare Befehle",
                description="Hier sind alle verfügbaren Slash-Befehle mit Beschreibung:",
                color=discord.Color.blue()
            )

            # Moderations-Befehle
            embed.add_field(
                name="👮 Moderation",
                value="```\n"
                      "/kick - Kickt einen Benutzer vom Server\n"
                      "/ban - Bannt einen Benutzer vom Server\n"
                      "/clear - Löscht eine bestimmte Anzahl von Nachrichten\n"
                      "```",
                inline=False
            )

            # Handels- und Vertragsbefehle
            embed.add_field(
                name="💰 Handel & Verträge",
                value="```\n"
                      "/handelsvertrag - Erstelle einen Handelsvertrag mit einem anderen Land\n"
                      "/vertrag - Erstelle einen politischen Vertrag (Nichtangriffspakt, Schutzbündnis, etc.)\n"
                      "/verträge - Zeige alle deine aktiven Verträge an\n"
                      "```",
                inline=False
            )
            
            # Ausbau-Befehle
            embed.add_field(
                name="🏗️ Ausbau",
                value="```\n"
                      "/ausbau - Führe einen Ausbau in deinem Land durch (Wirtschaft, Bevölkerung, Militär, etc.)\n"
                      "```",
                inline=False
            )

            # Allgemeine Befehle
            embed.add_field(
                name="📝 Allgemein",
                value="```\n"
                      "/ping - Überprüft die Latenz des Bots\n"
                      "/serverinfo - Zeigt Informationen über den Server\n"
                      "/userinfo - Zeigt Informationen über einen Benutzer\n"
                      "/invite - Generiert einen Einladungslink für den Bot\n"
                      "/commands - Zeigt diese Befehlsübersicht\n"
                      "/help - Zeigt die Hilfe an\n"
                      "```",
                inline=False
            )

            embed.set_footer(text="Benutze diese Befehle mit einem / am Anfang")
            await interaction.response.send_message(embed=embed)
            logger.info("Command list displayed successfully")
        except Exception as e:
            logger.error(f"Error displaying commands: {str(e)}")
            await interaction.response.send_message("Ein Fehler ist aufgetreten. Bitte versuche es später erneut.", ephemeral=True)

    @app_commands.command(name="help", description="Display help information")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Bot Commands",
            description="Here are all available slash commands:",
            color=discord.Color.blue()
        )

        # Add Moderation Commands
        embed.add_field(
            name="Moderation",
            value="```\n"
                  "/kick - Kick a member\n"
                  "/ban - Ban a member\n"
                  "/clear - Clear messages\n"
                  "```",
            inline=False
        )

        # Add Trade Commands
        embed.add_field(
            name="Trade & Diplomacy",
            value="```\n"
                  "/handelsvertrag - Create a trade agreement with another country\n"
                  "/vertrag - Create a political treaty (non-aggression pact, alliance, etc.)\n"
                  "/verträge - Show all your active treaties\n"
                  "```",
            inline=False
        )
        
        # Add Development Commands
        embed.add_field(
            name="Development",
            value="```\n"
                  "/ausbau - Develop your country (economy, population, military, etc.)\n"
                  "```",
            inline=False
        )

        # Add General Commands
        embed.add_field(
            name="General",
            value="```\n"
                  "/ping - Check bot latency\n"
                  "/serverinfo - Server information\n"
                  "/userinfo - User information\n"
                  "/invite - Get bot's invite link\n"
                  "/commands - Show commands in German\n"
                  "/help - Show this help message\n"
                  "```",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))