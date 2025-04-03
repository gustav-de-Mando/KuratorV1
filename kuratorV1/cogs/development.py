import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import config
from utils import sheets

class DevelopmentOptions:
    INFRASTRUKTUR = "Infrastruktur"
    WIRTSCHAFT = "Wirtschaft"
    MILITAER = "Militär"
    LANDWIRTSCHAFT = "Landwirtschaft"
    BILDUNG = "Bildung"
    KULTUR = "Kultur"
    
    # Military units
    INFANTERIE = "Infanterie"
    KAVALLERIE = "Kavallerie"
    ARTILLERIE = "Artillerie"
    KORVETTE = "Korvette"
    FREGATTE = "Fregatte"
    LINIENSCHIFF = "Linienschiff"

class Development(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    development_types = [
        app_commands.Choice(name="Infrastruktur", value=DevelopmentOptions.INFRASTRUKTUR),
        app_commands.Choice(name="Wirtschaft", value=DevelopmentOptions.WIRTSCHAFT),
        app_commands.Choice(name="Militär", value=DevelopmentOptions.MILITAER),
        app_commands.Choice(name="Landwirtschaft", value=DevelopmentOptions.LANDWIRTSCHAFT),
        app_commands.Choice(name="Bildung", value=DevelopmentOptions.BILDUNG),
        app_commands.Choice(name="Kultur", value=DevelopmentOptions.KULTUR),
        app_commands.Choice(name="Infanterie", value=DevelopmentOptions.INFANTERIE),
        app_commands.Choice(name="Kavallerie", value=DevelopmentOptions.KAVALLERIE),
        app_commands.Choice(name="Artillerie", value=DevelopmentOptions.ARTILLERIE),
        app_commands.Choice(name="Korvette", value=DevelopmentOptions.KORVETTE),
        app_commands.Choice(name="Fregatte", value=DevelopmentOptions.FREGATTE),
        app_commands.Choice(name="Linienschiff", value=DevelopmentOptions.LINIENSCHIFF),
    ]
    
    @app_commands.command(name="develop", description="Entwickle dein Land durch Ausbau von Infrastruktur oder Militär")
    @app_commands.describe(
        ausbau_art="Art des Ausbaus",
        stufe="Ausbaustufe (1-7)",
        gebiet="Gebietsnummer, in der der Ausbau stattfinden soll",
        holz="Benötigte Menge Holz",
        stein="Benötigte Menge Stein",
        eisen="Benötigte Menge Eisen",
        stoff="Benötigte Menge Stoff",
        nahrung="Benötigte Menge Nahrung",
        dukaten="Benötigte Menge Dukaten",
        anzahl="Anzahl der Einheiten (nur bei militärischen Einheiten relevant)"
    )
    async def develop(
        self,
        interaction: discord.Interaction,
        ausbau_art: app_commands.Choice[str],
        stufe: int,
        gebiet: int,
        holz: int = 0,
        stein: int = 0,
        eisen: int = 0,
        stoff: int = 0,
        nahrung: int = 0,
        dukaten: int = 0,
        anzahl: int = 1
    ):
        """
        Führe einen Ausbau in deinem Land durch.
        
        Parameters:
        -----------
        ausbau_art: Die Art des Ausbaus (Wirtschaft, Militär, etc.)
        stufe: Die Ausbaustufe (1-7)
        gebiet: Die Gebietsnummer, in der der Ausbau stattfinden soll
        holz: Benötigte Menge Holz
        stein: Benötigte Menge Stein
        eisen: Benötigte Menge Eisen
        stoff: Benötigte Menge Stoff
        nahrung: Benötigte Menge Nahrung
        dukaten: Benötigte Menge Dukaten
        anzahl: Die Anzahl der Einheiten (nur bei militärischen Einheiten relevant)
        """
        # Validate input
        if stufe < 1 or stufe > 7:
            await interaction.response.send_message("Die Ausbaustufe muss zwischen 1 und 7 liegen.", ephemeral=True)
            return
        
        if gebiet < 1:
            await interaction.response.send_message("Die Gebietsnummer muss positiv sein.", ephemeral=True)
            return
        
        # Check if this is a military unit
        is_military = ausbau_art.value in [
            DevelopmentOptions.INFANTERIE, 
            DevelopmentOptions.KAVALLERIE,
            DevelopmentOptions.ARTILLERIE,
            DevelopmentOptions.KORVETTE,
            DevelopmentOptions.FREGATTE,
            DevelopmentOptions.LINIENSCHIFF
        ]
        
        # For military units, anzahl must be at least 1
        if is_military and anzahl < 1:
            await interaction.response.send_message("Die Anzahl der Einheiten muss mindestens 1 sein.", ephemeral=True)
            return
        
        # Ask user for country name
        await interaction.response.send_message(
            "Bitte gib den Namen deines Landes ein:",
            ephemeral=True
        )
        
        # Wait for country name
        try:
            def check_country(m):
                return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
            
            country_msg = await self.bot.wait_for('message', check=check_country, timeout=60.0)
            land = country_msg.content
            
            # Delete the message to keep the channel clean
            try:
                await country_msg.delete()
            except:
                pass
            
            # Prepare costs dictionary
            kosten = {
                "holz": holz,
                "stein": stein,
                "eisen": eisen,
                "stoff": stoff,
                "nahrung": nahrung,
                "dukaten": dukaten
            }
            
            # Create a formatted string for resources
            resources_str = []
            if holz > 0:
                resources_str.append(f"{holz} Holz")
            if stein > 0:
                resources_str.append(f"{stein} Stein")
            if eisen > 0:
                resources_str.append(f"{eisen} Eisen")
            if stoff > 0:
                resources_str.append(f"{stoff} Stoff")
            if nahrung > 0:
                resources_str.append(f"{nahrung} Nahrung")
            if dukaten > 0:
                resources_str.append(f"{dukaten} Dukaten")
            
            resources_text = ", ".join(resources_str) if resources_str else "Keine Ressourcen"
            
            # Create an embed with development details
            embed = discord.Embed(
                title="Ausbau durchgeführt",
                description=f"{interaction.user.mention} hat einen Ausbau in {land} durchgeführt.",
                color=discord.Color.green()
            )
            
            embed.add_field(name="Land", value=land, inline=True)
            embed.add_field(name="Ausbau", value=f"{ausbau_art.value} (Stufe {stufe})", inline=True)
            embed.add_field(name="Gebiet", value=str(gebiet), inline=True)
            
            if is_military:
                embed.add_field(name="Anzahl", value=str(anzahl), inline=True)
            
            embed.add_field(name="Kosten", value=resources_text, inline=False)
            
            # Log the development to the Google Sheet
            try:
                sheets.log_ausbau_to_sheet(
                    os.environ.get('TRADE_SHEET_ID', ''),
                    land,
                    ausbau_art.value,
                    stufe,
                    kosten,
                    gebiet,
                    anzahl
                )
            except Exception as e:
                print(f"Error logging development to sheet: {e}")
                await interaction.followup.send(f"Der Ausbau wurde durchgeführt, konnte aber nicht in die Tabelle eingetragen werden: {e}", ephemeral=True)
            
            # Send confirmation
            await interaction.followup.send(embed=embed)
            
        except asyncio.TimeoutError:
            await interaction.followup.send("Zeit abgelaufen. Bitte versuche es erneut.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Development(bot))