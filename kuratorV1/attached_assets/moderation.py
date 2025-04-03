import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import setup_logger

logger = setup_logger()

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Kicks a member from the server")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f'{member.name} has been kicked.\nReason: {reason}')
            logger.info(f'User {member.name} was kicked by {interaction.user.name}')
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to kick members!", ephemeral=True)
        except Exception as e:
            logger.error(f'Error kicking member: {str(e)}')
            await interaction.response.send_message("An error occurred while trying to kick the member.", ephemeral=True)

    @app_commands.command(name="ban", description="Bans a member from the server")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f'{member.name} has been banned.\nReason: {reason}')
            logger.info(f'User {member.name} was banned by {interaction.user.name}')
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban members!", ephemeral=True)
        except Exception as e:
            logger.error(f'Error banning member: {str(e)}')
            await interaction.response.send_message("An error occurred while trying to ban the member.", ephemeral=True)

    @app_commands.command(name="clear", description="Clears specified number of messages")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        try:
            # Defer the response since clearing messages might take time
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f'Cleared {len(deleted)} messages.', ephemeral=True)
            logger.info(f'{len(deleted)} messages cleared by {interaction.user.name}')
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to delete messages!", ephemeral=True)
        except Exception as e:
            logger.error(f'Error clearing messages: {str(e)}')
            await interaction.followup.send("An error occurred while trying to clear messages.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))