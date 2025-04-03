import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime
import os
from utils.logger import setup_logger
from utils.sheets import get_sheets_service

logger = setup_logger()

# Definiere die verschiedenen Ausbau-Arten
class AusbauArten:
    WIRTSCHAFT = "Wirtschaft"
    BEVOELKERUNG = "Bevölkerung"
    BERGBAU = "Bergbau"
    AGRABAU = "Agrabau"
    NEBENSTADT = "Nebenstadt"
    HANDELSPOSTEN = "Handelsposten"
    HAUPTSTADT = "Hauptstadt"
    HANDELSZENTRUM = "Handelszentrum"
    FESTUNG = "Festung"
    INFANTERIE = "Infanterie"
    KAVALLERIE = "Kavallerie"
    ARTILLERIE = "Artillerie"
    KORVETTE = "Korvette"
    FREGATTE = "Fregatte"
    LINIENSCHIFF = "Linienschiff"

# Definiere die Kosten für jeden Ausbau-Typ und Level
ausbau_kosten = {
    "Wirtschaft": {
        2: {"holz": 60, "stein": 60, "eisen": 10, "stoff": 0, "nahrung": 0, "gold": 1500000},
        3: {"holz": 150, "stein": 150, "eisen": 20, "stoff": 0, "nahrung": 0, "gold": 3000000},
        4: {"holz": 200, "stein": 200, "eisen": 50, "stoff": 10, "nahrung": 0, "gold": 5000000},
        5: {"holz": 350, "stein": 350, "eisen": 100, "stoff": 20, "nahrung": 0, "gold": 7500000},
        6: {"holz": 450, "stein": 450, "eisen": 150, "stoff": 50, "nahrung": 0, "gold": 10000000},
        7: {"holz": 500, "stein": 500, "eisen": 200, "stoff": 100, "nahrung": 0, "gold": 15000000}
    },
    "Bevölkerung": {
        2: {"holz": 80, "stein": 30, "eisen": 0, "stoff": 0, "nahrung": 20, "gold": 750000},
        3: {"holz": 200, "stein": 100, "eisen": 0, "stoff": 0, "nahrung": 50, "gold": 1000000},
        4: {"holz": 250, "stein": 150, "eisen": 10, "stoff": 10, "nahrung": 75, "gold": 2000000},
        5: {"holz": 400, "stein": 300, "eisen": 25, "stoff": 20, "nahrung": 100, "gold": 3000000},
        6: {"holz": 500, "stein": 400, "eisen": 50, "stoff": 50, "nahrung": 200, "gold": 5000000},
        7: {"holz": 600, "stein": 450, "eisen": 100, "stoff": 100, "nahrung": 300, "gold": 7000000}
    },
    "Bergbau": {
        2: {"holz": 50, "stein": 50, "eisen": 20, "stoff": 0, "nahrung": 0, "gold": 2000000},
        3: {"holz": 100, "stein": 100, "eisen": 30, "stoff": 0, "nahrung": 0, "gold": 4000000},
        4: {"holz": 150, "stein": 150, "eisen": 75, "stoff": 10, "nahrung": 0, "gold": 6000000},
        5: {"holz": 300, "stein": 300, "eisen": 125, "stoff": 20, "nahrung": 0, "gold": 8000000},
        6: {"holz": 400, "stein": 400, "eisen": 175, "stoff": 50, "nahrung": 0, "gold": 10000000},
        7: {"holz": 450, "stein": 450, "eisen": 250, "stoff": 100, "nahrung": 0, "gold": 12500000}
    },
    "Agrabau": {
        2: {"holz": 50, "stein": 50, "eisen": 10, "stoff": 0, "nahrung": 0, "gold": 2000000},
        3: {"holz": 125, "stein": 125, "eisen": 20, "stoff": 0, "nahrung": 0, "gold": 4000000},
        4: {"holz": 175, "stein": 175, "eisen": 50, "stoff": 10, "nahrung": 0, "gold": 6000000},
        5: {"holz": 325, "stein": 325, "eisen": 100, "stoff": 20, "nahrung": 0, "gold": 8000000},
        6: {"holz": 425, "stein": 425, "eisen": 150, "stoff": 50, "nahrung": 0, "gold": 10000000},
        7: {"holz": 475, "stein": 475, "eisen": 200, "stoff": 100, "nahrung": 0, "gold": 12500000}
    },
    "Nebenstadt": {
        2: {"holz": 150, "stein": 150, "eisen": 50, "stoff": 50, "nahrung": 0, "gold": 5000000},
        3: {"holz": 250, "stein": 250, "eisen": 50, "stoff": 150, "nahrung": 0, "gold": 7000000}
    },
    "Handelsposten": {
        2: {"holz": 200, "stein": 200, "eisen": 50, "stoff": 100, "nahrung": 0, "gold": 5000000},
        3: {"holz": 300, "stein": 300, "eisen": 75, "stoff": 200, "nahrung": 0, "gold": 7000000},
        4: {"holz": 500, "stein": 500, "eisen": 100, "stoff": 300, "nahrung": 0, "gold": 10000000},
        5: {"holz": 750, "stein": 750, "eisen": 150, "stoff": 500, "nahrung": 0, "gold": 15000000}
    },
    "Hauptstadt": {
        2: {"holz": 200, "stein": 200, "eisen": 50, "stoff": 100, "nahrung": 0, "gold": 5000000},
        3: {"holz": 300, "stein": 300, "eisen": 75, "stoff": 200, "nahrung": 0, "gold": 7000000},
        4: {"holz": 500, "stein": 500, "eisen": 100, "stoff": 300, "nahrung": 0, "gold": 10000000},
        5: {"holz": 750, "stein": 750, "eisen": 150, "stoff": 500, "nahrung": 0, "gold": 12500000},
        6: {"holz": 850, "stein": 850, "eisen": 200, "stoff": 750, "nahrung": 0, "gold": 17500000},
        7: {"holz": 1000, "stein": 1000, "eisen": 250, "stoff": 1000, "nahrung": 0, "gold": 20000000}
    },
    "Handelszentrum": {
        2: {"holz": 200, "stein": 200, "eisen": 50, "stoff": 200, "nahrung": 0, "gold": 7000000},
        3: {"holz": 300, "stein": 300, "eisen": 75, "stoff": 300, "nahrung": 0, "gold": 10000000},
        4: {"holz": 500, "stein": 500, "eisen": 100, "stoff": 500, "nahrung": 0, "gold": 12500000},
        5: {"holz": 750, "stein": 750, "eisen": 150, "stoff": 750, "nahrung": 0, "gold": 17500000},
        6: {"holz": 850, "stein": 850, "eisen": 200, "stoff": 1000, "nahrung": 0, "gold": 20000000},
        7: {"holz": 1000, "stein": 1000, "eisen": 250, "stoff": 1250, "nahrung": 0, "gold": 25000000}
    },
    "Festung": {
        1: {"holz": 100, "stein": 200, "eisen": 100, "stoff": 0, "nahrung": 75, "gold": 3000000},
        2: {"holz": 150, "stein": 300, "eisen": 150, "stoff": 0, "nahrung": 100, "gold": 5500000},
        3: {"holz": 200, "stein": 400, "eisen": 200, "stoff": 0, "nahrung": 150, "gold": 8000000},
        4: {"holz": 250, "stein": 500, "eisen": 250, "stoff": 50, "nahrung": 200, "gold": 11500000},
        5: {"holz": 300, "stein": 750, "eisen": 300, "stoff": 75, "nahrung": 250, "gold": 16000000}
    },
    "Infanterie": {
        1: {"holz": 0, "stein": 0, "eisen": 20, "stoff": 20, "nahrung": 30, "gold": 250000}
    },
    "Kavallerie": {
        1: {"holz": 0, "stein": 0, "eisen": 20, "stoff": 10, "nahrung": 40, "gold": 325000}
    },
    "Artillerie": {
        1: {"holz": 0, "stein": 0, "eisen": 40, "stoff": 20, "nahrung": 10, "gold": 500000}
    },
    "Korvette": {
        1: {"holz": 40, "stein": 0, "eisen": 20, "stoff": 25, "nahrung": 20, "gold": 275000}
    },
    "Fregatte": {
        1: {"holz": 60, "stein": 0, "eisen": 30, "stoff": 40, "nahrung": 30, "gold": 400000}
    },
    "Linienschiff": {
        1: {"holz": 80, "stein": 0, "eisen": 45, "stoff": 60, "nahrung": 40, "gold": 550000}
    }
}

# Liste der militärischen Einheiten
militaerische_einheiten = [
    "Infanterie", "Kavallerie", "Artillerie", "Korvette", "Fregatte", "Linienschiff"
]

class Ausbau(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ausbau",
        description="Führe einen Ausbau in deinem Land durch"
    )
    @app_commands.choices(ausbau_art=[
        app_commands.Choice(name="Wirtschaft", value="Wirtschaft"),
        app_commands.Choice(name="Bevölkerung", value="Bevölkerung"),
        app_commands.Choice(name="Bergbau", value="Bergbau"),
        app_commands.Choice(name="Agrabau", value="Agrabau"),
        app_commands.Choice(name="Nebenstadt", value="Nebenstadt"),
        app_commands.Choice(name="Handelsposten", value="Handelsposten"),
        app_commands.Choice(name="Hauptstadt", value="Hauptstadt"),
        app_commands.Choice(name="Handelszentrum", value="Handelszentrum"),
        app_commands.Choice(name="Festung", value="Festung"),
        app_commands.Choice(name="Infanterie", value="Infanterie"),
        app_commands.Choice(name="Kavallerie", value="Kavallerie"),
        app_commands.Choice(name="Artillerie", value="Artillerie"),
        app_commands.Choice(name="Korvette", value="Korvette"),
        app_commands.Choice(name="Fregatte", value="Fregatte"),
        app_commands.Choice(name="Linienschiff", value="Linienschiff")
    ])
    async def ausbau(
        self,
        interaction: discord.Interaction,
        ausbau_art: app_commands.Choice[str],
        level: int,
        gebiet: int,
        anzahl: int = 1
    ):
        """
        Führe einen Ausbau in deinem Land durch.
        
        Parameters:
        -----------
        ausbau_art: Die Art des Ausbaus (Wirtschaft, Militär, etc.)
        level: Die Ausbaustufe (1-7)
        gebiet: Die Gebietsnummer, in der der Ausbau stattfinden soll
        anzahl: Die Anzahl der Einheiten (nur bei militärischen Einheiten relevant)
        """
        try:
            # Prüfe Länderzugehörigkeit
            user_country = next((role for role in interaction.user.roles if role.name != "@everyone"), None)

            if not user_country:
                await interaction.response.send_message(
                    "Du musst ein Land (Rolle) haben, um Ausbauten durchzuführen!",
                    ephemeral=True
                )
                return
            
            # Prüfe, ob es sich um eine militärische Einheit handelt
            is_military = ausbau_art.value in militaerische_einheiten
            
            # Prüfe Levelbereich und Gebiet für militärische Einheiten
            if is_military:
                # Bei militärischen Einheiten muss das Level 1 sein
                if level != 1:
                    await interaction.response.send_message(
                        f"Für militärische Einheiten muss das Level 1 sein.",
                        ephemeral=True
                    )
                    return
                
                # Bei militärischen Einheiten muss das Gebiet 0 sein
                if gebiet != 0:
                    await interaction.response.send_message(
                        f"Für militärische Einheiten muss das Gebiet 0 sein, da sie nicht an ein Gebiet gebunden sind.",
                        ephemeral=True
                    )
                    return
                    await interaction.response.send_message(
                        f"Für militärische Einheiten muss das Level 1 sein.",
                        ephemeral=True
                    )
                    return
            else:
                # Prüfe, ob die Ausbaustufe für diesen Ausbautyp verfügbar ist
                if level not in ausbau_kosten[ausbau_art.value]:
                    min_level = min(ausbau_kosten[ausbau_art.value].keys())
                    max_level = max(ausbau_kosten[ausbau_art.value].keys())
                    await interaction.response.send_message(
                        f"Die angegebene Ausbaustufe ist nicht verfügbar. "
                        f"Für {ausbau_art.value} sind Stufen von {min_level} bis {max_level} verfügbar.",
                        ephemeral=True
                    )
                    return

                # Bei nicht-militärischen Einheiten muss die Anzahl 1 sein
                if anzahl != 1:
                    await interaction.response.send_message(
                        f"Für Infrastruktur-Ausbauten muss die Anzahl 1 sein.",
                        ephemeral=True
                    )
                    return
            
            # Berechne die Kosten
            base_kosten = ausbau_kosten[ausbau_art.value][level]
            
            if is_military:
                # Multipliziere die Kosten mit der Anzahl der Einheiten
                if anzahl <= 0:
                    await interaction.response.send_message(
                        f"Die Anzahl muss größer als 0 sein.",
                        ephemeral=True
                    )
                    return
                kosten = {k: v * anzahl for k, v in base_kosten.items()}
            else:
                kosten = base_kosten
            
            # Erstelle die Bestätigungsnachricht
            kosten_str = "\n".join([
                f"- {k.capitalize()}: {v:,}".replace(",", ".") for k, v in kosten.items() if v > 0
            ])
            
            # Formatiere die Anzahl nur für militärische Einheiten
            anzahl_str = f" (Anzahl: {anzahl})" if is_military else ""
            
            embed = discord.Embed(
                title=f"🏗️ Ausbau: {ausbau_art.value} Stufe {level}{anzahl_str}",
                description=f"Ausbau in Gebiet {gebiet} für das Reich {user_country.name}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Kosten", value=kosten_str, inline=False)
            
            # Sende Bestätigungsnachricht
            await interaction.response.send_message(
                "Dein Ausbauauftrag wurde erfasst und wird in die Ausbau-Tabelle eingetragen.",
                embed=embed,
                ephemeral=True
            )
            
            # Log den Ausbau in die Google Sheet
            try:
                await self.log_ausbau_to_sheet(
                    user_country.name,
                    ausbau_art.value,
                    level,
                    kosten,
                    gebiet,
                    anzahl if is_military else 1
                )
                logger.info(f"Ausbau wurde in die Tabelle eingetragen: {ausbau_art.value} (Stufe {level}) für {user_country.name}")
                
                # Sende eine Nachricht in den Ausbau-Kanal
                try:
                    ausbau_channel_id = 1355926391228600582
                    ausbau_channel = self.bot.get_channel(ausbau_channel_id)
                    
                    if ausbau_channel:
                        # Erstelle eine schöne Embed-Nachricht für den Kanal
                        embed = discord.Embed(
                            title=f"🏗️ Neuer Ausbau: {ausbau_art.value}",
                            description=f"Das Land **{user_country.name}** hat einen neuen Ausbau in Gebiet {gebiet} durchgeführt.",
                            color=discord.Color.gold()
                        )
                        
                        # Füge weitere Details hinzu
                        embed.add_field(name="Ausbaustufe", value=f"Stufe {level}", inline=True)
                        if is_military:
                            embed.add_field(name="Anzahl", value=str(anzahl), inline=True)
                        
                        # Füge die Kosten hinzu
                        kosten_str = "\n".join([
                            f"- {k.capitalize()}: {v:,}".replace(",", ".") for k, v in kosten.items() if v > 0
                        ])
                        embed.add_field(name="Investierte Ressourcen", value=kosten_str, inline=False)
                        
                        # Setze den Zeitstempel
                        embed.timestamp = datetime.now()
                        
                        # Sende die Nachricht
                        await ausbau_channel.send(embed=embed)
                        logger.info(f"Ausbau-Nachricht in Kanal {ausbau_channel_id} gesendet")
                    else:
                        logger.error(f"Konnte Kanal mit ID {ausbau_channel_id} nicht finden")
                except Exception as e:
                    logger.error(f"Fehler beim Senden der Ausbau-Nachricht: {str(e)}")
                    
            except Exception as e:
                logger.error(f"Fehler beim Eintragen des Ausbaus in die Tabelle: {str(e)}")
                await interaction.followup.send(
                    "Hinweis: Der Ausbau wurde erfolgreich erfasst, konnte aber nicht in die Google Tabelle eingetragen werden. "
                    "Bitte kontaktiere einen Administrator.",
                    ephemeral=True
                )
            
        except Exception as e:
            logger.error(f"Fehler im Ausbau-Command: {str(e)}")
            await interaction.response.send_message(
                "Ein Fehler ist aufgetreten. Bitte versuche es später erneut.",
                ephemeral=True
            )

    async def log_ausbau_to_sheet(self, land, ausbau_art, level, kosten, gebiet, anzahl):
        """
        Trägt einen Ausbau in die Google Tabelle ein.
        
        Parameters:
        -----------
        land: Das Land, das den Ausbau durchführt
        ausbau_art: Die Art des Ausbaus
        level: Die Ausbaustufe
        kosten: Dictionary mit den Kosten (holz, stein, eisen, etc.)
        gebiet: Die Gebietsnummer
        anzahl: Die Anzahl der Einheiten (nur bei militärischen Einheiten relevant)
        """
        # Verwende die feste, bereits definierte Tabellen-ID
        spreadsheet_id = "1quKEnSHhzW_z4MCJkoQhYuorB9S5OdmMEntAPdFT1a8"
        
        # Verwende die dedizierte Funktion aus dem sheets-Modul
        from utils.sheets import log_ausbau_to_sheet as log_to_sheet
        
        try:
            # Rufe die Funktion aus dem sheets-Modul auf
            success = log_to_sheet(
                spreadsheet_id, 
                land, 
                ausbau_art, 
                level, 
                kosten, 
                gebiet, 
                anzahl
            )
            
            return success
        except Exception as e:
            logger.error(f"Fehler beim Eintragen des Ausbaus in die Tabelle über sheets-Modul: {str(e)}")
            return False

async def setup(bot):
    await bot.add_cog(Ausbau(bot))