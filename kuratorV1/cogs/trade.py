import os
import uuid
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
from utils.image_generator import generate_trade_agreement_image
from utils import sheets

class TradeResources:
    STEIN = "Stein"
    EISEN = "Eisen"
    HOLZ = "Holz"
    NAHRUNG = "Nahrung"
    STOFF = "Stoff"
    DUKATEN = "Dukaten"

class Trade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_trades = {}  # Dict to store pending trade agreements
    
    trade_resources = [
        app_commands.Choice(name="Stein", value=TradeResources.STEIN),
        app_commands.Choice(name="Eisen", value=TradeResources.EISEN),
        app_commands.Choice(name="Holz", value=TradeResources.HOLZ),
        app_commands.Choice(name="Nahrung", value=TradeResources.NAHRUNG),
        app_commands.Choice(name="Stoff", value=TradeResources.STOFF),
        app_commands.Choice(name="Dukaten", value=TradeResources.DUKATEN),
    ]
    
    @app_commands.command(name="create_trade", description="Erstelle einen Handelsvertrag mit einem anderen Land")
    @app_commands.describe(
        partner="Der Handelspartner",
        land="Dein Land/Reich",
        partner_land="Das Land/Reich des Partners",
        angebot_ressource="Die Ressource, die du anbietest",
        angebot_menge="Die Menge, die du anbietest",
        nachfrage_ressource="Die Ressource, die du im Gegenzug möchtest",
        nachfrage_menge="Die Menge, die du im Gegenzug möchtest",
        vertragsbruch_klausel="Optionale Klausel für den Fall eines Vertragsbruchs",
        anmerkungen="Optionale Anmerkungen zum Vertrag"
    )
    async def create_trade(
        self,
        interaction: discord.Interaction,
        partner: discord.Member,
        land: str,
        partner_land: str,
        angebot_ressource: app_commands.Choice[str],
        angebot_menge: int,
        nachfrage_ressource: app_commands.Choice[str],
        nachfrage_menge: int,
        vertragsbruch_klausel: str = "",
        anmerkungen: str = ""
    ):
        """
        Erstellt einen Handelsvertrag zwischen zwei Ländern.
        
        Parameters:
        -----------
        partner: Der Handelspartner
        land: Dein Land/Reich
        partner_land: Das Land/Reich des Partners
        angebot_ressource: Die Ressource, die du anbietest
        angebot_menge: Die Menge, die du anbietest
        nachfrage_ressource: Die Ressource, die du im Gegenzug möchtest
        nachfrage_menge: Die Menge, die du im Gegenzug möchtest
        vertragsbruch_klausel: Optionale Klausel für den Fall eines Vertragsbruchs
        anmerkungen: Optionale Anmerkungen zum Vertrag
        """
        # Check if the partner is a bot
        if partner.bot:
            await interaction.response.send_message("Du kannst keinen Handelsvertrag mit einem Bot schließen.", ephemeral=True)
            return
        
        # Check if the partner is the user
        if partner.id == interaction.user.id:
            await interaction.response.send_message("Du kannst keinen Handelsvertrag mit dir selbst schließen.", ephemeral=True)
            return
        
        # Create a unique ID for this trade
        trade_id = str(uuid.uuid4())
        
        # Create an embed with the trade details
        embed = discord.Embed(
            title="Handelsvertrag",
            description=f"Ein Handelsvertrag wurde von {interaction.user.mention} vorgeschlagen.",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Von", value=f"{interaction.user.mention} von {land}", inline=True)
        embed.add_field(name="An", value=f"{partner.mention} von {partner_land}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)  # Empty field for formatting
        
        embed.add_field(name=f"{land} bietet", value=f"{angebot_menge} {angebot_ressource.value}", inline=True)
        embed.add_field(name=f"{partner_land} bietet", value=f"{nachfrage_menge} {nachfrage_ressource.value}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)  # Empty field for formatting
        
        if vertragsbruch_klausel:
            embed.add_field(name="Vertragsbruch-Klausel", value=vertragsbruch_klausel, inline=False)
        
        if anmerkungen:
            embed.add_field(name="Anmerkungen", value=anmerkungen, inline=False)
        
        # Get the current timestamp
        timestamp = datetime.datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")
        embed.set_footer(text=f"Trade ID: {trade_id} • {timestamp}")
        
        # Create the image for the trade agreement
        trade_image = generate_trade_agreement_image(
            interaction.user.display_name, 
            partner.display_name,
            land,
            partner_land,
            angebot_ressource.value,
            angebot_menge,
            nachfrage_ressource.value,
            nachfrage_menge,
            timestamp,
            vertragsbruch_klausel,
            anmerkungen
        )
        
        # Store the trade data
        self.pending_trades[trade_id] = {
            "initiator": interaction.user,
            "partner": partner,
            "initiator_country": land,
            "partner_country": partner_land,
            "offer_resource": angebot_ressource.value,
            "offer_amount": angebot_menge,
            "request_resource": nachfrage_ressource.value,
            "request_amount": nachfrage_menge,
            "embed": embed,
            "timestamp": timestamp
        }
        
        # Send a confirmation message to the user
        await interaction.response.send_message(
            f"Handelsangebot an {partner.mention} gesendet. Warte auf deren Bestätigung.",
            file=discord.File(fp=trade_image, filename="handelsvertrag.png"),
            ephemeral=True
        )
        
        # Send the trade offer to the partner
        await self.send_trade_confirmation(trade_id, interaction.user, partner, embed)
    
    async def send_trade_confirmation(self, trade_id: str, initiator: discord.Member, partner: discord.Member, embed: discord.Embed):
        """
        Sends a confirmation message to the trade partner.
        
        Parameters:
        -----------
        trade_id: The unique ID of the trade
        initiator: The member who initiated the trade
        partner: The trade partner who needs to confirm
        embed: The embed with trade details
        """
        # Send a DM to the trade partner
        try:
            # Create the image for the trade agreement
            trade_data = self.pending_trades[trade_id]
            trade_image = generate_trade_agreement_image(
                initiator.display_name, 
                partner.display_name,
                trade_data["initiator_country"],
                trade_data["partner_country"],
                trade_data["offer_resource"],
                trade_data["offer_amount"],
                trade_data["request_resource"],
                trade_data["request_amount"],
                trade_data["timestamp"]
            )
            
            # DM the partner
            dm_message = await partner.send(
                f"{initiator.mention} hat dir einen Handelsvertrag angeboten. Akzeptiere mit `ja` oder lehne mit `nein [Grund]` ab:",
                embed=embed,
                file=discord.File(fp=trade_image, filename="handelsvertrag.png")
            )
            
            # Wait for a response from the partner
            def check_response(message):
                return message.author == partner and message.channel.type is discord.ChannelType.private and (
                    message.content.lower().startswith('ja') or message.content.lower().startswith('nein')
                )
            
            try:
                # Wait for 10 minutes for a response
                response = await self.bot.wait_for('message', check=check_response, timeout=600.0)
                
                # Process the response
                if response.content.lower().startswith('ja'):
                    await self.finalize_trade(trade_id, True)
                    await partner.send("Du hast den Handelsvertrag akzeptiert.")
                else:
                    rejection_reason = response.content[5:].strip() if len(response.content) > 5 else None
                    await self.finalize_trade(trade_id, False, rejection_reason)
                    await partner.send("Du hast den Handelsvertrag abgelehnt.")
            
            except asyncio.TimeoutError:
                await partner.send("Die Zeit für die Antwort ist abgelaufen. Der Handelsvertrag wurde automatisch abgelehnt.")
                await self.finalize_trade(trade_id, False, "Zeitüberschreitung")
        
        except discord.Forbidden:
            # Cannot send DMs to the partner
            channel = await initiator.create_dm()
            await channel.send(f"{partner.mention} hat DMs deaktiviert. Der Handelsvertrag konnte nicht gesendet werden.")
            if trade_id in self.pending_trades:
                del self.pending_trades[trade_id]
        
        except Exception as e:
            print(f"Error sending trade confirmation: {e}")
            channel = await initiator.create_dm()
            await channel.send(f"Fehler beim Senden des Handelsvertrags: {e}")
            if trade_id in self.pending_trades:
                del self.pending_trades[trade_id]
    
    async def finalize_trade(self, trade_id: str, accepted: bool, rejection_reason: str | None = None):
        """
        Finalizes a trade by informing the initiator and logging the result.
        
        Parameters:
        -----------
        trade_id: The unique ID of the trade
        accepted: Whether the trade was accepted or rejected
        rejection_reason: The reason for rejection, if applicable
        """
        # Retrieve the trade data
        if trade_id not in self.pending_trades:
            return
        
        trade_data = self.pending_trades[trade_id]
        initiator = trade_data["initiator"]
        partner = trade_data["partner"]
        
        # Send a message to the initiator
        try:
            if accepted:
                # Log the trade to the Google Sheet if accepted
                try:
                    sheets.log_trade_to_sheet(
                        os.environ.get('TRADE_SHEET_ID', ''),
                        trade_data["initiator_country"],
                        trade_data["partner_country"],
                        trade_data["offer_resource"],
                        trade_data["offer_amount"],
                        trade_data["request_resource"],
                        trade_data["request_amount"]
                    )
                except Exception as e:
                    print(f"Error logging trade to sheet: {e}")
                
                await initiator.send(f"{partner.mention} hat deinen Handelsvertrag akzeptiert!")
                
                # Create a final version of the trade agreement image
                trade_image = generate_trade_agreement_image(
                    initiator.display_name, 
                    partner.display_name,
                    trade_data["initiator_country"],
                    trade_data["partner_country"],
                    trade_data["offer_resource"],
                    trade_data["offer_amount"],
                    trade_data["request_resource"],
                    trade_data["request_amount"],
                    trade_data["timestamp"]
                )
                
                # Send the final image to both parties
                await initiator.send(file=discord.File(fp=trade_image, filename="handelsvertrag_final.png"))
                await partner.send(file=discord.File(fp=trade_image, filename="handelsvertrag_final.png"))
                
            else:
                reason_msg = f" Grund: {rejection_reason}" if rejection_reason else ""
                await initiator.send(f"{partner.mention} hat deinen Handelsvertrag abgelehnt.{reason_msg}")
        
        except discord.Forbidden:
            print(f"Cannot send DM to {initiator.name}")
        
        except Exception as e:
            print(f"Error finalizing trade: {e}")
        
        # Remove the trade from pending trades
        if trade_id in self.pending_trades:
            del self.pending_trades[trade_id]

async def setup(bot):
    await bot.add_cog(Trade(bot))