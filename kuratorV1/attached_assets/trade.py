import os
import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import setup_logger
from datetime import datetime
from utils.image_generator import generate_trade_agreement_image
import io
from io import BytesIO

logger = setup_logger()

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
        self.pending_trades = {}

    @app_commands.command(
        name="handelsvertrag",
        description="Erstelle einen Handelsvertrag mit einem anderen Land"
    )
    @app_commands.describe(
        partner="Der Handelspartner, mit dem du einen Vertrag schließen möchtest",
        angebot_ressource="Die Ressource, die du exportieren möchtest",
        angebot_menge="Die Menge, die du exportieren möchtest",
        wunsch_ressource="Die Ressource, die du importieren möchtest",
        wunsch_menge="Die Menge, die du importieren möchtest",
        vertragsbruch_klausel="Spezielle Vertragsbruchklausel (optional, leer lassen für Standardklausel)",
        anmerkungen="Zusätzliche Anmerkungen zum Vertrag (optional)"
    )
    @app_commands.choices(
        angebot_ressource=[
            app_commands.Choice(name="Stein", value="Stein"),
            app_commands.Choice(name="Eisen", value="Eisen"),
            app_commands.Choice(name="Holz", value="Holz"),
            app_commands.Choice(name="Nahrung", value="Nahrung"),
            app_commands.Choice(name="Stoff", value="Stoff"),
            app_commands.Choice(name="Dukaten", value="Dukaten")
        ],
        wunsch_ressource=[
            app_commands.Choice(name="Stein", value="Stein"),
            app_commands.Choice(name="Eisen", value="Eisen"),
            app_commands.Choice(name="Holz", value="Holz"),
            app_commands.Choice(name="Nahrung", value="Nahrung"),
            app_commands.Choice(name="Stoff", value="Stoff"),
            app_commands.Choice(name="Dukaten", value="Dukaten")
        ]
    )
    async def trade_agreement(
        self,
        interaction: discord.Interaction,
        partner: discord.Member,
        angebot_ressource: app_commands.Choice[str],
        angebot_menge: int,
        wunsch_ressource: app_commands.Choice[str],
        wunsch_menge: int,
        vertragsbruch_klausel: str = "",
        anmerkungen: str = ""
    ):
        try:
            # Check if user has a country role
            user_country = next((role for role in interaction.user.roles if role.name != "@everyone"), None)
            partner_country = next((role for role in partner.roles if role.name != "@everyone"), None)

            if not user_country or not partner_country:
                await interaction.response.send_message(
                    "Beide Handelspartner müssen ein Land (Rolle) haben!",
                    ephemeral=True
                )
                return

            # Bei Verwendung von app_commands.Choice ist keine manuelle Validierung mehr nötig,
            # da Discord bereits die Auswahl auf die definierten Optionen beschränkt

            # Create a unique trade ID
            trade_id = f"{interaction.user.id}-{partner.id}-{datetime.now().timestamp()}"

            # Standardklausel für Vertragsbruch
            standard_klausel = (
                "Der Schuldige muss das Doppelte des Wertes oder eine gleichwertige Entschädigung zahlen. "
                "Ein Vertragsbruchkrieg (§2.1.1) kann erklärt werden. "
                "Vertragsbrüche werden von der Spielleitung geprüft. "
                "Sanktionen können wirtschaftlicher, militärischer oder territorialer Natur sein."
            )

            # Verwende die angegebene Klausel oder die Standardklausel
            klausel_text = vertragsbruch_klausel if vertragsbruch_klausel else standard_klausel

            # Create trade agreement embed
            embed = discord.Embed(
                title="📜 Handelsvertrag",
                description="Ein neuer Handelsvertrag wurde vorgeschlagen",
                color=discord.Color.gold()
            )

            # Erste Zeile: Land 1 exportiert und Land 2 importiert
            embed.add_field(
                name=f"{user_country.name} (Export)",
                value=f"{interaction.user.mention} liefert {angebot_menge}x {angebot_ressource.value}",
                inline=True
            )
            embed.add_field(
                name=f"{partner_country.name} (Import)",
                value=f"{partner.mention} erhält {angebot_menge}x {angebot_ressource.value}",
                inline=True
            )
            embed.add_field(name="\u200b", value="\u200b", inline=True)  # Spacer for alignment

            # Zweite Zeile: Land 2 exportiert und Land 1 importiert
            embed.add_field(
                name=f"{partner_country.name} (Export)",
                value=f"{partner.mention} liefert {wunsch_menge}x {wunsch_ressource.value}",
                inline=True
            )
            embed.add_field(
                name=f"{user_country.name} (Import)",
                value=f"{interaction.user.mention} erhält {wunsch_menge}x {wunsch_ressource.value}",
                inline=True
            )
            embed.add_field(name="\u200b", value="\u200b", inline=True)  # Spacer for alignment

            # Vertragsbruchklausel hinzufügen
            embed.add_field(
                name="Vertragsbruchklausel",
                value=klausel_text,
                inline=False
            )

            # Anmerkungen hinzufügen, falls vorhanden
            if anmerkungen:
                embed.add_field(
                    name="Anmerkungen",
                    value=anmerkungen,
                    inline=False
                )

            # Store the trade info
            self.pending_trades[trade_id] = {
                "initiator": interaction.user,
                "partner": partner,
                "embed": embed,
                "channel": interaction.channel,
                "accepted": {"initiator": False, "partner": False},
                "vertragsbruch_klausel": vertragsbruch_klausel,
                "anmerkungen": anmerkungen
            }

            try:
                # Zuerst die Interaktion bestätigen
                await interaction.response.send_message(
                    "Handelsvertrag wird erstellt...",
                    ephemeral=True
                )

                # Dann DMs senden
                await self.send_trade_confirmation(trade_id, interaction.user, partner, embed)

                # Optional: Update der ursprünglichen Nachricht
                try:
                    await interaction.edit_original_response(
                        content="Handelsvertrag wurde erstellt. Beide Parteien wurden per DM benachrichtigt."
                    )
                except Exception as e:
                    logger.warning(f"Konnte ursprüngliche Nachricht nicht aktualisieren: {str(e)}")

            except Exception as e:
                logger.error(f"Error in trade agreement: {str(e)}")
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "Ein Fehler ist aufgetreten. Bitte versuche es später erneut.",
                        ephemeral=True
                    )

    async def send_trade_confirmation(self, trade_id: str, initiator: discord.Member, partner: discord.Member, embed: discord.Embed):
        try:
            # Einmalige Nachricht an den Initiator
            await initiator.send(
                f"📜 **Neuer Handelsvertrag**\n\n"
                f"Ein neuer Handelsvertrag wurde erstellt. Bitte bestätigt mit 'ja' oder 'nein':",
                embed=embed
            )

            # Einmalige Nachricht an den Partner
            await partner.send(
                f"📜 **Handelsvertrag zur Prüfung**\n\n"
                f"Ein neuer Handelsvertrag wurde vorgeschlagen. Bitte bestätigt mit 'ja' oder 'nein':",
                embed=embed
            )

            def check_response(message):
                # Check if message is in DM and from either party
                return (
                    isinstance(message.channel, discord.DMChannel) and
                    message.author.id in [initiator.id, partner.id] and
                    message.content.lower() in ['ja', 'nein']
                )

            # Wait for responses from both parties
            try:
                # Wait for initiator response
                initiator_msg = await self.bot.wait_for('message', check=check_response, timeout=300)
                initiator_accepted = initiator_msg.content.lower() == 'ja'
                self.pending_trades[trade_id]["accepted"]["initiator"] = initiator_accepted
                logger.info(f"Trade {trade_id}: Initiator ({initiator.name}) responded: {initiator_msg.content}")

                if not initiator_accepted:
                    await self.finalize_trade(trade_id, False, "Der Handelsvertrag wurde vom Anbieter abgelehnt.")
                    return

                # Wait for partner response
                partner_msg = await self.bot.wait_for('message', check=check_response, timeout=300)
                partner_accepted = partner_msg.content.lower() == 'ja'
                self.pending_trades[trade_id]["accepted"]["partner"] = partner_accepted
                logger.info(f"Trade {trade_id}: Partner ({partner.name}) responded: {partner_msg.content}")

                await self.finalize_trade(trade_id, partner_accepted, "Der Handelspartner hat den Vertrag abgelehnt." if not partner_accepted else None)

            except TimeoutError:
                logger.info(f"Trade {trade_id}: Timeout waiting for responses")
                await initiator.send("Zeit abgelaufen. Der Handelsvertrag wurde abgebrochen.")
                await partner.send("Zeit abgelaufen. Der Handelsvertrag wurde abgebrochen.")
                if trade_id in self.pending_trades:
                    del self.pending_trades[trade_id]

        except discord.Forbidden:
            # Handle cases where DMs are disabled
            logger.error(f"Trade {trade_id}: Unable to send DMs to users")
            channel = self.pending_trades[trade_id]["channel"]
            await channel.send(
                f"Konnte keine DM an {initiator.mention} oder {partner.mention} senden. "
                "Bitte stelle sicher, dass DMs aktiviert sind.",
                ephemeral=True
            )
            del self.pending_trades[trade_id]

    async def finalize_trade(self, trade_id: str, accepted: bool, rejection_reason: str | None = None):
        trade = self.pending_trades.get(trade_id)
        if not trade:
            return

        # Get the announcement channel
        announcement_channel = self.bot.get_channel(1351332809981038632)
        if not announcement_channel:
            logger.error("Could not find announcement channel")
            return

        embed = trade["embed"]
        initiator = trade["initiator"]
        partner = trade["partner"]

        # Get country roles for both participants, regardless of acceptance or rejection
        initiator_country = next((role.name for role in initiator.roles if role.name != "@everyone"), "Unbekannt")
        partner_country = next((role.name for role in partner.roles if role.name != "@everyone"), "Unbekannt")

        if accepted:
            try:
                # Log to Google Sheet
                spreadsheet_id = os.getenv('TRADE_SHEET_ID')
                if spreadsheet_id:
                    from utils.sheets import log_trade_to_sheet
                    from datetime import datetime

                    # Verwende die bereits definierten Ländernamen

                    # Extract resources from embed fields based on export fields
                    initiator_export_field = next(f for f in embed.fields if f.name == f"{initiator_country} (Export)")
                    partner_export_field = next(f for f in embed.fields if f.name == f"{partner_country} (Export)")

                    # Parse amounts and resources from the fields
                    initiator_export_value = initiator_export_field.value
                    partner_export_value = partner_export_field.value

                    # Extract offer (from initiator) details
                    offer_amount = int(initiator_export_value.split('liefert ')[1].split('x')[0])
                    offer_resource = initiator_export_value.split('x ')[1].strip()

                    # Extract request (from partner) details
                    request_amount = int(partner_export_value.split('liefert ')[1].split('x')[0])
                    request_resource = partner_export_value.split('x ')[1].strip()

                    # Log to sheet
                    log_trade_to_sheet(
                        spreadsheet_id,
                        initiator_country,
                        partner_country,
                        offer_resource,
                        offer_amount,
                        request_resource,
                        request_amount
                    )
            except Exception as e:
                logger.error(f"Failed to log trade to sheet: {str(e)}")

            embed.color = discord.Color.green()
            embed.add_field(name="Status", value="✅ Vertrag angenommen", inline=False)

            # Verwende die bereits definierten Ländernamen

            # Extract resources from embed fields
            initiator_export_field = next(f for f in embed.fields if f.name == f"{initiator_country} (Export)")
            partner_export_field = next(f for f in embed.fields if f.name == f"{partner_country} (Export)")

            # Parse amounts and resources from the fields
            initiator_export_value = initiator_export_field.value
            partner_export_value = partner_export_field.value

            # Extract offer (from initiator) details
            offer_amount = int(initiator_export_value.split('liefert ')[1].split('x')[0])
            offer_resource = initiator_export_value.split('x ')[1].strip()

            # Extract request (from partner) details
            request_amount = int(partner_export_value.split('liefert ')[1].split('x')[0])
            request_resource = partner_export_value.split('x ')[1].strip()

            # Generate trade agreement image
            try:
                # Erstelle das historische Vertragsbild
                from datetime import datetime

                # Hole Vertragsbruchklausel und Anmerkungen
                vertragsbruch_klausel = trade.get("vertragsbruch_klausel")
                anmerkungen = trade.get("anmerkungen")

                trade_image = generate_trade_agreement_image(
                    initiator_name=initiator.display_name,
                    partner_name=partner.display_name,
                    initiator_country=initiator_country,
                    partner_country=partner_country,
                    offer_resource=offer_resource,
                    offer_amount=offer_amount,
                    request_resource=request_resource,
                    request_amount=request_amount,
                    timestamp=datetime.now(),
                    vertragsbruch_klausel=vertragsbruch_klausel,
                    anmerkungen=anmerkungen
                )

                # Prepare the file for Discord
                trade_image_file = discord.File(trade_image, filename="handelsvertrag.png")

                # Sende eine Ankündigung mit dem Bild in den Channel
                await announcement_channel.send(
                    f"📜 **Handelsvertrag ratifiziert** 📜\n\n"
                    f"Die ehrenwerten Reiche {initiator_country} ({initiator.mention}) und {partner_country} ({partner.mention}) "
                    f"haben einen feierlichen Handelsvertrag geschlossen. Möge dieser Austausch "
                    f"von Waren den Wohlstand beider Reiche fördern.",
                    file=trade_image_file
                )

                # Verwende dasselbe Bild für beide DMs, um doppelte Generierung zu vermeiden
                # Erstelle Kopien des ursprünglichen Bildes
                trade_image.seek(0)  # Zurück zum Anfang des BytesIO-Objekts
                initiator_file = discord.File(BytesIO(trade_image.getvalue()), filename="handelsvertrag.png")

                trade_image.seek(0)  # Zurück zum Anfang des BytesIO-Objekts
                partner_file = discord.File(BytesIO(trade_image.getvalue()), filename="handelsvertrag.png")

                # Sende das Bild mit einer Nachricht an jeden Herrscher
                # Historische Nachricht für den Initiator
                await initiator.send(
                    f"✅ **Handelsvertrag ratifiziert**\n\n"
                    f"Eure Exzellenz, Herrscher von {initiator_country},\n\n"
                    f"Mit großer Freude verkünden wir, dass der Handelsvertrag mit dem Reich {partner_country} "
                    f"von beiden Parteien ratifiziert wurde. Die vereinbarten Handelswege werden umgehend geöffnet, "
                    f"und der Austausch von Waren wird unverzüglich beginnen.\n\n"
                    f"Eine formelle Kopie des Dokuments wurde in Euren königlichen Handelsarchiven hinterlegt.",
                    file=initiator_file
                )

                # Historische Nachricht für den Partner
                await partner.send(
                    f"✅ **Handelsvertrag ratifiziert**\n\n"
                    f"Eure Exzellenz, Herrscher von {partner_country},\n\n"
                    f"Mit großer Freude verkünden wir, dass der Handelsvertrag mit dem Reich {initiator_country} "
                    f"von beiden Parteien ratifiziert wurde. Die vereinbarten Handelswege werden umgehend geöffnet, "
                    f"und der Austausch von Waren wird unverzüglich beginnen.\n\n"
                    f"Eine formelle Kopie des Dokuments wurde in Euren königlichen Handelsarchiven hinterlegt.",
                    file=partner_file
                )

            except Exception as e:
                logger.error(f"Failed to generate trade agreement image: {str(e)}")
                # Fallback to plain message if image generation fails
                await announcement_channel.send(
                    f"🤝 Neuer Handelsvertrag abgeschlossen zwischen {initiator.mention} und {partner.mention}!",
                    embed=embed
                )
                # Send fallback confirmation DMs
                await initiator.send("✅ Der Handelsvertrag wurde von beiden Parteien angenommen!")
                await partner.send("✅ Der Handelsvertrag wurde von beiden Parteien angenommen!")
            logger.info(f"Trade {trade_id}: Successfully completed between {initiator.name} and {partner.name}")
        else:
            embed.color = discord.Color.red()
            embed.add_field(name="Status", value="❌ Vertrag abgelehnt", inline=False)

            # Send rejection message that will auto-delete after 10 minutes
            rejection_msg = await trade["channel"].send(
                f"📜 **Handelsvertrag abgelehnt** 📜\n\n"
                f"Die Verhandlungen zwischen den Reichen {initiator_country} ({initiator.mention}) und "
                f"{partner_country} ({partner.mention}) wurden ohne Einigung beendet. "
                f"Die Diplomaten beider Länder haben sich zurückgezogen.",
                embed=embed,
                delete_after=600
            )
            logger.info(f"Trade {trade_id}: Sent rejection message that will auto-delete in 10 minutes")

            try:
                # Create personalized historical rejection messages
                base_rejection = rejection_reason or "Der vorgeschlagene Handelspakt wurde abgelehnt."

                # Historische Nachricht für den Initiator
                initiator_rejection = (
                    f"❌ **Handelsverhandlungen gescheitert**\n\n"
                    f"Eure Exzellenz, Herrscher von {initiator_country},\n\n"
                    f"Mit Bedauern müssen wir Euch mitteilen, dass die Handelsverhandlungen mit dem Reich {partner_country} "
                    f"nicht den gewünschten Erfolg gebracht haben. Die diplomatischen Gesandten sind ohne Einigung zurückgekehrt.\n\n"
                    f"Grund: {base_rejection}\n\n"
                    f"Die königlichen Berater empfehlen, zu einem späteren Zeitpunkt neue Verhandlungen aufzunehmen."
                )

                # Historische Nachricht für den Partner
                partner_rejection = (
                    f"❌ **Handelsverhandlungen gescheitert**\n\n"
                    f"Eure Exzellenz, Herrscher von {partner_country},\n\n"
                    f"Mit Bedauern müssen wir Euch mitteilen, dass die Handelsverhandlungen mit dem Reich {initiator_country} "
                    f"nicht den gewünschten Erfolg gebracht haben. Die diplomatischen Gesandten sind ohne Einigung zurückgekehrt.\n\n"
                    f"Grund: {base_rejection}\n\n"
                    f"Die königlichen Berater empfehlen, zu einem späteren Zeitpunkt neue Verhandlungen aufzunehmen."
                )

                # Sende personalisierte Ablehnungsnachrichten
                await initiator.send(initiator_rejection)
                await partner.send(partner_rejection)
            except Exception as e:
                logger.error(f"Error creating rejection messages: {str(e)}")
                await initiator.send("Der Handelsvertrag wurde abgelehnt.")
                await partner.send("Der Handelsvertrag wurde abgelehnt.")
            logger.info(f"Trade {trade_id}: Rejected - {base_rejection}")

        # Clean up
        del self.pending_trades[trade_id]

async def setup(bot):
    await bot.add_cog(Trade(bot))