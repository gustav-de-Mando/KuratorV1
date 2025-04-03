import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from utils.logger import setup_logger
import asyncio
from io import BytesIO
from utils.image_generator import generate_treaty_image

logger = setup_logger()

class TreatyTypes:
    NON_AGGRESSION = "Nichtangriffspakt"
    PROTECTION = "Schutzbündnis"
    ALLIANCE = "Allianzvertrag"
    MARRIAGE = "Hochzeitspakt"
    GRAND_ALLIANCE = "Großallianzvertrag"

class Treaties(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_treaties = {}

    async def cog_load(self):
        """Diese Methode wird aufgerufen, wenn der Cog geladen wird."""
        # Starte die Aufgabe zum Überprüfen abgelaufener Verträge
        # Wir verwenden setup_hook, da loop attribute nicht in non-async Kontext aufgerufen werden kann
        asyncio.create_task(self.check_expired_treaties())

    @app_commands.command(
        name="vertrag",
        description="Erstelle einen neuen Vertrag (Nichtangriffspakt, Schutzbündnis, Allianz, Hochzeit, Großallianz)"
    )
    @app_commands.choices(vertragstyp=[
        app_commands.Choice(name="Nichtangriffspakt", value="Nichtangriffspakt"),
        app_commands.Choice(name="Schutzbündnis", value="Schutzbündnis"),
        app_commands.Choice(name="Allianzvertrag", value="Allianzvertrag"),
        app_commands.Choice(name="Hochzeitspakt", value="Hochzeitspakt"),
        app_commands.Choice(name="Großallianzvertrag", value="Großallianzvertrag")
    ])
    @app_commands.describe(
        partner="Der Vertragspartner, mit dem du einen Vertrag schließen möchtest",
        vertragstyp="Art des Vertrags (Nichtangriffspakt: max 3, Schutzbündnis: max 3, Allianz: max 3, Hochzeit: max 1, Großallianz: max 1)",
        laufzeit="Dauer des Vertrags in Tagen (Standard: 7 Tage)",
        vertragsbruch_klausel="Spezielle Vertragsbruchklausel (optional)",
        anmerkungen="Zusätzliche Anmerkungen zum Vertrag (optional)"
    )
    async def create_treaty(
        self,
        interaction: discord.Interaction,
        partner: discord.Member,
        vertragstyp: app_commands.Choice[str],
        laufzeit: int = 7,
        vertragsbruch_klausel: str = "",
        anmerkungen: str = ""
    ):
        try:
            # Prüfe Vertragstyp
            if vertragstyp.value not in vars(TreatyTypes).values():
                await interaction.response.send_message(
                    f"Ungültiger Vertragstyp! Bitte wähle einen der vorgegebenen Typen.",
                    ephemeral=True
                )
                return

            # Prüfe Länderzugehörigkeit
            user_country = next((role for role in interaction.user.roles if role.name != "@everyone"), None)
            partner_country = next((role for role in partner.roles if role.name != "@everyone"), None)

            if not user_country or not partner_country:
                await interaction.response.send_message(
                    "Beide Vertragspartner müssen ein Land (Rolle) haben!",
                    ephemeral=True
                )
                return

            # Prüfe Bündnislimit
            if not self.check_treaty_limit(interaction.user, vertragstyp):
                await interaction.response.send_message(
                    "Bündnislimit erreicht! Siehe §7 für Details.",
                    ephemeral=True
                )
                return

            # Erstelle Vertrag
            treaty_id = f"{interaction.user.id}-{partner.id}-{datetime.now().timestamp()}"
            expiry_date = datetime.now() + timedelta(days=laufzeit)

            # Standardklausel für Vertragsbruch, falls keine angegeben wurde
            standard_klausel = (
                "Der Schuldige muss das Doppelte des Wertes oder eine gleichwertige Entschädigung zahlen. "
                "Ein Vertragsbruchkrieg (§2.1.1) kann erklärt werden. "
                "Vertragsbrüche werden von der Spielleitung geprüft. "
                "Sanktionen können wirtschaftlicher, militärischer oder territorialer Natur sein."
            )

            # Verwende die angegebene Klausel oder die Standardklausel
            klausel_text = vertragsbruch_klausel if vertragsbruch_klausel else standard_klausel

            embed = discord.Embed(
                title=f"📜 {vertragstyp.value}",
                description="Ein neuer Vertrag wurde vorgeschlagen",
                color=discord.Color.gold()
            )
            embed.add_field(name="Land 1", value=f"{user_country.name} ({interaction.user.mention})", inline=True)
            embed.add_field(name="Land 2", value=f"{partner_country.name} ({partner.mention})", inline=True)
            embed.add_field(name="Laufzeit", value=f"{laufzeit} Tage (bis {expiry_date.strftime('%d.%m.%Y')})", inline=False)

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

            # Speichere Vertragsinformationen
            self.active_treaties[treaty_id] = {
                "type": vertragstyp.value,
                "country1": user_country.name,
                "country2": partner_country.name,
                "initiator": interaction.user,
                "partner": partner,
                "expiry_date": expiry_date,
                "accepted": {"initiator": False, "partner": False},
                "vertragsbruch_klausel": vertragsbruch_klausel if vertragsbruch_klausel else standard_klausel,
                "anmerkungen": anmerkungen
            }

            # Sende DMs zur Bestätigung
            await self.send_treaty_confirmation(treaty_id, interaction.user, partner, embed)

            try:
                await interaction.edit_original_response(
                    content="Vertrag wurde erstellt. Beide Parteien wurden per DM benachrichtigt."
                )
            except:
                logger.warning("Could not update original message")

        except Exception as e:
            logger.error(f"Error in treaty creation: {str(e)}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Ein Fehler ist aufgetreten. Bitte versuche es später erneut.",
                    ephemeral=True
                )

    @app_commands.command(
        name="verträge",
        description="Zeige alle aktiven Verträge"
    )
    async def list_treaties(self, interaction: discord.Interaction):
        user_treaties = []

        for treaty_id, treaty in self.active_treaties.items():
            if interaction.user in [treaty["initiator"], treaty["partner"]]:
                user_treaties.append(treaty)

        if not user_treaties:
            await interaction.response.send_message("Du hast keine aktiven Verträge.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📜 Deine aktiven Verträge",
            color=discord.Color.blue()
        )

        for treaty in user_treaties:
            embed.add_field(
                name=f"{treaty['type']}",
                value=f"Mit: {treaty['country2'] if treaty['initiator'] == interaction.user else treaty['country1']}\n"
                      f"Läuft ab: {treaty['expiry_date'].strftime('%d.%m.%Y')}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    def check_treaty_limit(self, user: discord.Member, treaty_type: app_commands.Choice[str]) -> bool:
        user_treaties = [t for t in self.active_treaties.values() 
                        if (t["initiator"] == user or t["partner"] == user) and t["type"] == treaty_type.value]

        limits = {
            TreatyTypes.NON_AGGRESSION: 3,
            TreatyTypes.PROTECTION: 3,
            TreatyTypes.ALLIANCE: 3,
            TreatyTypes.MARRIAGE: 1,
            TreatyTypes.GRAND_ALLIANCE: 1
        }

        return len(user_treaties) < limits.get(treaty_type.value, 0)

    async def send_treaty_confirmation(self, treaty_id: str, initiator: discord.Member, partner: discord.Member, embed: discord.Embed):
        if treaty_id not in self.active_treaties:
            return

        try:
            # Sende DMs mit Anweisungen zur Antwort - nur einmal
            if not self.active_treaties[treaty_id].get("messages_sent"):
                await initiator.send(
                    "Bitte antworte mit 'ja' oder 'nein' um den folgenden Vertrag zu bestätigen:",
                    embed=embed
                )
                await partner.send(
                    "Du hast einen neuen Vertragsvorschlag erhalten. Bitte antworte mit 'ja' oder 'nein':",
                    embed=embed
                )
                self.active_treaties[treaty_id]["messages_sent"] = True

            def check_response(message):
                return (
                    isinstance(message.channel, discord.DMChannel) and
                    message.author.id in [initiator.id, partner.id] and
                    message.content.lower() in ['ja', 'nein']
                )

            try:
                # Warte auf Antworten
                initiator_msg = await self.bot.wait_for('message', check=check_response, timeout=300)
                self.active_treaties[treaty_id]["accepted"]["initiator"] = initiator_msg.content.lower() == 'ja'

                if not self.active_treaties[treaty_id]["accepted"]["initiator"]:
                    await self.finalize_treaty(treaty_id, False, "Der Vertrag wurde vom Initiator abgelehnt.")
                    return

                partner_msg = await self.bot.wait_for('message', check=check_response, timeout=300)
                self.active_treaties[treaty_id]["accepted"]["partner"] = partner_msg.content.lower() == 'ja'

                await self.finalize_treaty(
                    treaty_id,
                    self.active_treaties[treaty_id]["accepted"]["partner"],
                    "Der Vertrag wurde vom Partner abgelehnt." if not self.active_treaties[treaty_id]["accepted"]["partner"] else None
                )

            except asyncio.TimeoutError:
                await initiator.send("Zeit abgelaufen. Der Vertrag wurde abgebrochen.")
                await partner.send("Zeit abgelaufen. Der Vertrag wurde abgebrochen.")
                if treaty_id in self.active_treaties:
                    del self.active_treaties[treaty_id]

        except discord.Forbidden:
            logger.error(f"Treaty {treaty_id}: Unable to send DMs to users")
            if treaty_id in self.active_treaties:
                del self.active_treaties[treaty_id]

    async def finalize_treaty(self, treaty_id: str, accepted: bool, rejection_reason: str | None = None):
        treaty = self.active_treaties.get(treaty_id)
        if not treaty:
            return

        announcement_channel = self.bot.get_channel(1351332809981038632)  # Ersetze mit tatsächlicher Channel ID
        if not announcement_channel:
            logger.error("Could not find announcement channel")
            return

        embed = discord.Embed(
            title=f"📜 {treaty['type']}",
            description="Ein neuer Vertrag wurde geschlossen" if accepted else "Vertrag wurde abgelehnt",
            color=discord.Color.green() if accepted else discord.Color.red()
        )
        embed.add_field(name="Land 1", value=treaty["country1"], inline=True)
        embed.add_field(name="Land 2", value=treaty["country2"], inline=True)
        if accepted:
            embed.add_field(name="Läuft ab", value=treaty["expiry_date"].strftime("%d.%m.%Y"), inline=False)

        if accepted:
            # Lade Vertragstyp und andere Daten
            treaty_type = treaty['type']
            initiator = treaty["initiator"]
            partner = treaty["partner"]
            initiator_country = treaty["country1"]
            partner_country = treaty["country2"]
            vertragsbruch_klausel = treaty.get("vertragsbruch_klausel", "")
            anmerkungen = treaty.get("anmerkungen", "")

            try:
                # Importiere die Bild-Generator-Funktion
                from utils.image_generator import generate_treaty_image

                # Erstelle das Vertragsbild
                treaty_image = generate_treaty_image(
                    initiator_name=initiator.display_name,
                    partner_name=partner.display_name,
                    initiator_country=initiator_country,
                    partner_country=partner_country,
                    treaty_type=treaty_type,
                    expiry_date=treaty["expiry_date"],
                    vertragsbruch_klausel=vertragsbruch_klausel,
                    anmerkungen=anmerkungen
                )

                # Bereite die Datei für Discord vor
                treaty_image_file = discord.File(treaty_image, filename="vertrag.png")

                # Sende eine Ankündigung mit dem Bild in den Channel
                await announcement_channel.send(
                    f"📜 **{treaty_type} ratifiziert** 📜\n\n"
                    f"Die ehrenwerten Reiche {initiator_country} ({initiator.mention}) und {partner_country} ({partner.mention}) "
                    f"haben einen feierlichen Vertrag geschlossen.",
                    file=treaty_image_file
                )

                # Verwende dasselbe Bild für beide DMs, um doppelte Generierung zu vermeiden
                # Erstelle Kopien des ursprünglichen Bildes
                treaty_image.seek(0)  # Zurück zum Anfang des BytesIO-Objekts
                initiator_file = discord.File(BytesIO(treaty_image.getvalue()), filename="vertrag.png")

                treaty_image.seek(0)  # Zurück zum Anfang des BytesIO-Objekts
                partner_file = discord.File(BytesIO(treaty_image.getvalue()), filename="vertrag.png")

                # Historische Nachrichten basierend auf Vertragstyp
                messages = {
                    "Nichtangriffspakt": 
                        f"✅ **{treaty_type} ratifiziert**\n\n"
                        f"Eure Exzellenz, Herrscher von {initiator_country},\n\n"
                        f"Der Friedenspakt mit dem Reich {partner_country} wurde feierlich unterzeichnet. "
                        f"Möge dieses Abkommen eine Ära des Friedens und der Prosperität einläuten. "
                        f"Eine Kopie der Urkunde wurde in den königlichen Archiven hinterlegt.",

                    "Schutzbündnis": 
                        f"✅ **{treaty_type} ratifiziert**\n\n"
                        f"Eure Majestät, Herrscher von {initiator_country},\n\n"
                        f"Das Schutzbündnis mit dem Reich {partner_country} wurde besiegelt. "
                        f"Unsere Truppen stehen bereit, unsere Verbündeten zu verteidigen. "
                        f"Das offizielle Dokument wurde mit dem königlichen Siegel versehen.",

                    "Allianzvertrag": 
                        f"✅ **{treaty_type} ratifiziert**\n\n"
                        f"Eure Erhabenheit, Herrscher von {initiator_country},\n\n"
                        f"Die Allianz mit dem Reich {partner_country} wurde feierlich geschlossen. "
                        f"Diese glorreiche Verbindung wird die Macht beider Reiche mehren. "
                        f"Das Bündnisdokument wurde im Staatsarchiv verwahrt.",

                    "Hochzeitspakt": 
                        f"✅ **{treaty_type} ratifiziert**\n\n"
                        f"Eure Hoheit, Herrscher von {initiator_country},\n\n"
                        f"Der heilige Hochzeitspakt mit dem Reich {partner_country} wurde gesegnet. "
                        f"Diese Verbindung zweier edler Häuser wird die Geschichte neu schreiben. "
                        f"Die Eheurkunde wurde in beiden Königshäusern hinterlegt.",

                    "Großallianzvertrag": 
                        f"✅ **{treaty_type} ratifiziert**\n\n"
                        f"Erhabener Herrscher von {initiator_country},\n\n"
                        f"Die Großallianz mit dem Reich {partner_country} wurde geschlossen. "
                        f"Dieses mächtige Bündnis wird unsere Feinde erzittern lassen. "
                        f"Das Dokument wurde mit den Siegeln beider Reiche versehen."
                }

                # Standardnachricht für unbekannte Vertragstypen
                default_message = (
                    f"✅ **{treaty_type} ratifiziert**\n\n"
                    f"Eure Exzellenz, Herrscher von {initiator_country},\n\n"
                    f"Der Vertrag mit dem Reich {partner_country} wurde von beiden Parteien unterzeichnet. "
                    f"Eine formelle Kopie des Dokuments wurde in Euren Archiven hinterlegt."
                )

                # Sende historische Nachricht an den Initiator
                initiator_message = messages.get(treaty_type, default_message)
                await initiator.send(initiator_message, file=initiator_file)

                # Ersetze den Ländernamen für die Nachricht an den Partner
                partner_message = messages.get(treaty_type, default_message).replace(initiator_country, partner_country).replace(partner_country, initiator_country)
                await partner.send(partner_message, file=partner_file)

            except Exception as e:
                logger.error(f"Failed to generate treaty image: {str(e)}")
                # Fallback zu einfacher Nachricht
                await announcement_channel.send(
                    f"🤝 Neuer {treaty_type} zwischen {initiator_country} und {partner_country}!",
                    embed=embed
                )
                await treaty["initiator"].send(f"✅ Der {treaty_type} wurde von beiden Parteien angenommen!")
                await treaty["partner"].send(f"✅ Der {treaty_type} wurde von beiden Parteien angenommen!")
        else:
            # Sende Ablehnungsnachricht, die nach 10 Minuten automatisch gelöscht wird
            rejection_msg = await announcement_channel.send(
                f"📜 **{treaty['type']} abgelehnt** 📜\n\n"
                f"Die Verhandlungen zwischen den Reichen {treaty['country1']} ({treaty['initiator'].mention}) und "
                f"{treaty['country2']} ({treaty['partner'].mention}) wurden ohne Einigung beendet. "
                f"Die Diplomaten beider Länder haben sich zurückgezogen.",
                embed=embed,
                delete_after=600  # 10 Minuten
            )
            logger.info(f"Treaty {treaty_id}: Sent rejection message that will auto-delete in 10 minutes")

            # Erstelle personalisierte historische Ablehnungsnachrichten
            base_rejection = rejection_reason or f"Der vorgeschlagene {treaty['type']} wurde abgelehnt."

            # Historische Nachricht für den Initiator
            initiator_rejection = (
                f"❌ **Vertragsverhandlungen gescheitert**\n\n"
                f"Eure Exzellenz, Herrscher von {treaty['country1']},\n\n"
                f"Mit Bedauern müssen wir Euch mitteilen, dass die Verhandlungen über einen {treaty['type']} mit dem Reich {treaty['country2']} "
                f"nicht den gewünschten Erfolg gebracht haben. Die diplomatischen Gesandten sind ohne Einigung zurückgekehrt.\n\n"
                f"Grund: {base_rejection}\n\n"
                f"Die königlichen Berater empfehlen, zu einem späteren Zeitpunkt neue Verhandlungen aufzunehmen."
            )

            # Historische Nachricht für den Partner
            partner_rejection = (
                f"❌ **Vertragsverhandlungen gescheitert**\n\n"
                f"Eure Exzellenz, Herrscher von {treaty['country2']},\n\n"
                f"Mit Bedauern müssen wir Euch mitteilen, dass die Verhandlungen über einen {treaty['type']} mit dem Reich {treaty['country1']} "
                f"nicht den gewünschten Erfolg gebracht haben. Die diplomatischen Gesandten sind ohne Einigung zurückgekehrt.\n\n"
                f"Grund: {base_rejection}\n\n"
                f"Die königlichen Berater empfehlen, zu einem späteren Zeitpunkt neue Verhandlungen aufzunehmen."
            )

            # Sende personalisierte Ablehnungsnachrichten
            await treaty["initiator"].send(initiator_rejection)
            await treaty["partner"].send(partner_rejection)

        if not accepted:
            del self.active_treaties[treaty_id]

    async def check_expired_treaties(self):
        while True:
            now = datetime.now()
            expired_treaties = []

            for treaty_id, treaty in self.active_treaties.items():
                if treaty["expiry_date"] <= now:
                    expired_treaties.append(treaty_id)
                    try:
                        # Historische Nachrichten für abgelaufene Verträge
                        treaty_type = treaty['type']
                        initiator_country = treaty['country1']
                        partner_country = treaty['country2']

                        # Spezifische Nachrichten je nach Vertragstyp
                        expiry_messages = {
                            "Nichtangriffspakt": 
                                f"📜 **{treaty_type} ausgelaufen**\n\n"
                                f"Eure Exzellenz, Herrscher von {initiator_country},\n\n"
                                f"Der Friedenspakt mit dem Reich {partner_country} ist gemäß seiner Bestimmungen erloschen. "
                                f"Die Diplomaten beider Reiche empfehlen eine Neubewertung der Beziehungen.",

                            "Schutzbündnis": 
                                f"📜 **{treaty_type} ausgelaufen**\n\n"
                                f"Eure Majestät, Herrscher von {initiator_country},\n\n"
                                f"Das Schutzbündnis mit dem Reich {partner_country} ist erloschen. "
                                f"Unsere militärischen Verpflichtungen gegenüber diesem Reich sind hiermit aufgehoben. "
                                f"Das Oberkommando erwartet Eure weiteren Instruktionen.",

                            "Allianzvertrag": 
                                f"📜 **{treaty_type} ausgelaufen**\n\n"
                                f"Eure Erhabenheit, Herrscher von {initiator_country},\n\n"
                                f"Die Allianz mit dem Reich {partner_country} ist nach Ablauf der vereinbarten Zeit erloschen. "
                                f"Die Staatsräte ersuchen um eine Audienz, um die künftige Ausrichtung unserer Außenpolitik zu besprechen.",

                            "Hochzeitspakt": 
                                f"📜 **{treaty_type} ausgelaufen**\n\n"
                                f"Eure Hoheit, Herrscher von {initiator_country},\n\n"
                                f"Der Hochzeitspakt mit dem Reich {partner_country} ist nach Ablauf seiner Laufzeit erloschen. "
                                f"Die königlichen Berater empfehlen eine Erneuerung der Verbindung zur Sicherung der dynastischen Interessen.",

                            "Großallianzvertrag": 
                                f"📜 **{treaty_type} ausgelaufen**\n\n"
                                f"Erhabener Herrscher von {initiator_country},\n\n"
                                f"Die Großallianz mit dem Reich {partner_country} ist zu ihrem Ende gekommen. "
                                f"Unsere militärischen Verbände stehen bereit, neue Befehle zu empfangen. "
                                f"Der Kriegsrat erbittet eine Audienz zur Besprechung der strategischen Lage."
                        }

                        # Standardnachricht für unbekannte Vertragstypen
                        default_expiry_message = (
                            f"📜 **{treaty_type} ausgelaufen**\n\n"
                            f"Eure Exzellenz, Herrscher von {initiator_country},\n\n"
                            f"Der Vertrag mit dem Reich {partner_country} ist nach Ablauf seiner Laufzeit erloschen. "
                            f"Unsere Diplomaten erwarten Eure Weisungen bezüglich der künftigen Beziehungen."
                        )

                        # Sende historische Nachrichten
                        initiator_expiry_message = expiry_messages.get(treaty_type, default_expiry_message)
                        await treaty["initiator"].send(initiator_expiry_message)

                        # Ersetze den Ländernamen für die Nachricht an den Partner
                        partner_expiry_message = expiry_messages.get(treaty_type, default_expiry_message).replace(initiator_country, partner_country).replace(partner_country, initiator_country)
                        await treaty["partner"].send(partner_expiry_message)
                    except discord.Forbidden:
                        logger.error(f"Could not send expiry notification for treaty {treaty_id}")

            for treaty_id in expired_treaties:
                del self.active_treaties[treaty_id]

            await asyncio.sleep(3600)  # Prüfe stündlich

async def setup(bot):
    await bot.add_cog(Treaties(bot))