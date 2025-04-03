import os
import uuid
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
from discord.ext import tasks
import config
from utils.image_generator import generate_treaty_image

class TreatyTypes:
    NON_AGGRESSION = "Nichtangriffspakt"
    PROTECTION = "Schutzbündnis"
    ALLIANCE = "Allianzvertrag"
    MARRIAGE = "Hochzeitspakt"
    GRAND_ALLIANCE = "Großallianzvertrag"

class Treaties(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_treaties = {}  # Store pending treaties
        self.active_treaties = {}   # Store active treaties
    
    treaty_types = [
        app_commands.Choice(name="Nichtangriffspakt", value=TreatyTypes.NON_AGGRESSION),
        app_commands.Choice(name="Schutzbündnis", value=TreatyTypes.PROTECTION),
        app_commands.Choice(name="Allianzvertrag", value=TreatyTypes.ALLIANCE),
        app_commands.Choice(name="Hochzeitspakt", value=TreatyTypes.MARRIAGE),
        app_commands.Choice(name="Großallianzvertrag", value=TreatyTypes.GRAND_ALLIANCE),
    ]
    
    async def cog_load(self):
        """Diese Methode wird aufgerufen, wenn der Cog geladen wird."""
        # Start the task to check for expired treaties
        self.check_expired_treaties.start()
    
    @app_commands.command(name="create_treaty", description="Erstelle einen Vertrag mit einem anderen Land")
    @app_commands.describe(
        partner="Der Vertragspartner",
        vertragstyp="Art des Vertrags",
        laufzeit="Laufzeit des Vertrags in Tagen (Standard: 7 Tage)",
        vertragsbruch_klausel="Optionale Klausel für den Fall eines Vertragsbruchs",
        anmerkungen="Optionale Anmerkungen zum Vertrag"
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
        """
        Erstellt einen Vertrag zwischen zwei Ländern.
        
        Parameters:
        -----------
        partner: Der Vertragspartner
        vertragstyp: Art des Vertrags (Nichtangriffspakt, Schutzbündnis, etc.)
        laufzeit: Laufzeit des Vertrags in Tagen (Standard: 7 Tage)
        vertragsbruch_klausel: Optionale Klausel für den Fall eines Vertragsbruchs
        anmerkungen: Optionale Anmerkungen zum Vertrag
        """
        # Check if the partner is a bot
        if partner.bot:
            await interaction.response.send_message("Du kannst keinen Vertrag mit einem Bot schließen.", ephemeral=True)
            return
        
        # Check if the partner is the user
        if partner.id == interaction.user.id:
            await interaction.response.send_message("Du kannst keinen Vertrag mit dir selbst schließen.", ephemeral=True)
            return
        
        # Check treaty limits for the user
        if not self.check_treaty_limit(interaction.user, vertragstyp):
            await interaction.response.send_message(
                f"Du hast bereits die maximale Anzahl an {vertragstyp.value}-Verträgen erreicht.",
                ephemeral=True
            )
            return
        
        # Create a unique ID for this treaty
        treaty_id = str(uuid.uuid4())
        
        # Get expiry date
        current_date = datetime.datetime.now()
        expiry_date = current_date + datetime.timedelta(days=laufzeit)
        expiry_str = expiry_date.strftime("%d.%m.%Y")
        
        # Ask user for country names
        await interaction.response.send_message(
            "Bitte gib den Namen deines Landes ein:",
            ephemeral=True
        )
        
        # Wait for country name
        try:
            def check_initiator_country(m):
                return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
            
            initiator_country_msg = await self.bot.wait_for('message', check=check_initiator_country, timeout=60.0)
            initiator_country = initiator_country_msg.content
            
            # Delete the message to keep the channel clean
            try:
                await initiator_country_msg.delete()
            except:
                pass
            
            # Now ask for partner country
            await interaction.followup.send(
                f"Danke! Wie lautet der Name des Landes von {partner.mention}?",
                ephemeral=True
            )
            
            def check_partner_country(m):
                return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
            
            partner_country_msg = await self.bot.wait_for('message', check=check_partner_country, timeout=60.0)
            partner_country = partner_country_msg.content
            
            # Delete the message to keep the channel clean
            try:
                await partner_country_msg.delete()
            except:
                pass
            
            # Create an embed with the treaty details
            embed = discord.Embed(
                title=f"{vertragstyp.value}",
                description=f"Ein diplomatischer Vertrag wurde von {interaction.user.mention} vorgeschlagen.",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Von", value=f"{interaction.user.mention} von {initiator_country}", inline=True)
            embed.add_field(name="An", value=f"{partner.mention} von {partner_country}", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)  # Empty field for formatting
            
            embed.add_field(name="Typ", value=vertragstyp.value, inline=True)
            embed.add_field(name="Laufzeit", value=f"{laufzeit} Tage (bis {expiry_str})", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)  # Empty field for formatting
            
            if vertragsbruch_klausel:
                embed.add_field(name="Vertragsbruch-Klausel", value=vertragsbruch_klausel, inline=False)
            
            if anmerkungen:
                embed.add_field(name="Anmerkungen", value=anmerkungen, inline=False)
            
            # Get the current timestamp
            timestamp = datetime.datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")
            embed.set_footer(text=f"Treaty ID: {treaty_id} • {timestamp}")
            
            # Create the image for the treaty
            treaty_image = generate_treaty_image(
                interaction.user.display_name, 
                partner.display_name,
                initiator_country,
                partner_country,
                vertragstyp.value,
                f"{laufzeit} Tage (bis {expiry_str})",
                vertragsbruch_klausel,
                anmerkungen
            )
            
            # Store the treaty data
            self.pending_treaties[treaty_id] = {
                "initiator": interaction.user,
                "partner": partner,
                "initiator_country": initiator_country,
                "partner_country": partner_country,
                "type": vertragstyp.value,
                "duration": laufzeit,
                "expiry_date": expiry_date,
                "embed": embed,
                "timestamp": timestamp,
                "vertragsbruch_klausel": vertragsbruch_klausel,
                "anmerkungen": anmerkungen
            }
            
            # Send a confirmation message to the user
            await interaction.followup.send(
                f"Vertragsangebot an {partner.mention} gesendet. Warte auf deren Bestätigung.",
                file=discord.File(fp=treaty_image, filename="vertrag.png"),
                ephemeral=True
            )
            
            # Send the treaty offer to the partner
            await self.send_treaty_confirmation(treaty_id, interaction.user, partner, embed)
            
        except asyncio.TimeoutError:
            await interaction.followup.send("Zeit abgelaufen. Bitte versuche es erneut.", ephemeral=True)
    
    @app_commands.command(name="list_treaties", description="Zeigt eine Liste aller aktiven Verträge an")
    async def list_treaties(self, interaction: discord.Interaction):
        """List all active treaties for the user"""
        user_treaties = {}
        
        # Group treaties by type
        for treaty_id, treaty in self.active_treaties.items():
            if treaty["initiator"].id == interaction.user.id or treaty["partner"].id == interaction.user.id:
                treaty_type = treaty["type"]
                if treaty_type not in user_treaties:
                    user_treaties[treaty_type] = []
                
                # Determine the other party
                other_party = treaty["partner"] if treaty["initiator"].id == interaction.user.id else treaty["initiator"]
                other_country = treaty["partner_country"] if treaty["initiator"].id == interaction.user.id else treaty["initiator_country"]
                
                # Add treaty info
                expiry = treaty["expiry_date"].strftime("%d.%m.%Y")
                user_treaties[treaty_type].append(f"{other_party.mention} von {other_country} (bis {expiry})")
        
        if not user_treaties:
            await interaction.response.send_message("Du hast derzeit keine aktiven Verträge.", ephemeral=True)
            return
        
        # Create an embed with the treaties
        embed = discord.Embed(
            title="Deine aktiven Verträge",
            description="Hier ist eine Liste all deiner aktiven diplomatischen Verträge:",
            color=discord.Color.blue()
        )
        
        for treaty_type, treaties in user_treaties.items():
            embed.add_field(name=treaty_type, value="\n".join(treaties), inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def check_treaty_limit(self, user: discord.Member, treaty_type: app_commands.Choice[str]) -> bool:
        """Check if the user has reached the limit for this type of treaty"""
        # Get the limit for this treaty type
        type_value = treaty_type.value
        limit = config.TREATY_LIMITS.get(type_value, 999)  # Default to a high number if not specified
        
        # Count active treaties of this type for the user
        count = 0
        for treaty in self.active_treaties.values():
            if (treaty["initiator"].id == user.id or treaty["partner"].id == user.id) and treaty["type"] == type_value:
                count += 1
        
        # Return True if the user is below the limit
        return count < limit
    
    async def send_treaty_confirmation(self, treaty_id: str, initiator: discord.Member, partner: discord.Member, embed: discord.Embed):
        """
        Sends a confirmation message to the treaty partner.
        
        Parameters:
        -----------
        treaty_id: The unique ID of the treaty
        initiator: The member who initiated the treaty
        partner: The treaty partner who needs to confirm
        embed: The embed with treaty details
        """
        # Send a DM to the treaty partner
        try:
            # Create the image for the treaty
            treaty_data = self.pending_treaties[treaty_id]
            treaty_image = generate_treaty_image(
                initiator.display_name, 
                partner.display_name,
                treaty_data["initiator_country"],
                treaty_data["partner_country"],
                treaty_data["type"],
                f"{treaty_data['duration']} Tage (bis {treaty_data['expiry_date'].strftime('%d.%m.%Y')})",
                treaty_data["vertragsbruch_klausel"],
                treaty_data["anmerkungen"]
            )
            
            # DM the partner
            dm_message = await partner.send(
                f"{initiator.mention} hat dir einen {treaty_data['type']} angeboten. Akzeptiere mit `ja` oder lehne mit `nein [Grund]` ab:",
                embed=embed,
                file=discord.File(fp=treaty_image, filename="vertrag.png")
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
                    await self.finalize_treaty(treaty_id, True)
                    await partner.send("Du hast den Vertrag akzeptiert.")
                else:
                    rejection_reason = response.content[5:].strip() if len(response.content) > 5 else None
                    await self.finalize_treaty(treaty_id, False, rejection_reason)
                    await partner.send("Du hast den Vertrag abgelehnt.")
            
            except asyncio.TimeoutError:
                await partner.send("Die Zeit für die Antwort ist abgelaufen. Der Vertrag wurde automatisch abgelehnt.")
                await self.finalize_treaty(treaty_id, False, "Zeitüberschreitung")
        
        except discord.Forbidden:
            # Cannot send DMs to the partner
            channel = await initiator.create_dm()
            await channel.send(f"{partner.mention} hat DMs deaktiviert. Der Vertrag konnte nicht gesendet werden.")
            if treaty_id in self.pending_treaties:
                del self.pending_treaties[treaty_id]
        
        except Exception as e:
            print(f"Error sending treaty confirmation: {e}")
            channel = await initiator.create_dm()
            await channel.send(f"Fehler beim Senden des Vertrags: {e}")
            if treaty_id in self.pending_treaties:
                del self.pending_treaties[treaty_id]
    
    async def finalize_treaty(self, treaty_id: str, accepted: bool, rejection_reason: str | None = None):
        """
        Finalizes a treaty by informing the initiator and activating or rejecting it.
        
        Parameters:
        -----------
        treaty_id: The unique ID of the treaty
        accepted: Whether the treaty was accepted or rejected
        rejection_reason: The reason for rejection, if applicable
        """
        # Retrieve the treaty data
        if treaty_id not in self.pending_treaties:
            return
        
        treaty_data = self.pending_treaties[treaty_id]
        initiator = treaty_data["initiator"]
        partner = treaty_data["partner"]
        
        # Send a message to the initiator
        try:
            if accepted:
                # Move the treaty from pending to active
                self.active_treaties[treaty_id] = treaty_data
                
                await initiator.send(f"{partner.mention} hat deinen Vertrag ({treaty_data['type']}) akzeptiert!")
                
                # Create a final version of the treaty image
                treaty_image = generate_treaty_image(
                    initiator.display_name, 
                    partner.display_name,
                    treaty_data["initiator_country"],
                    treaty_data["partner_country"],
                    treaty_data["type"],
                    f"{treaty_data['duration']} Tage (bis {treaty_data['expiry_date'].strftime('%d.%m.%Y')})",
                    treaty_data["vertragsbruch_klausel"],
                    treaty_data["anmerkungen"]
                )
                
                # Send the final image to both parties
                await initiator.send(file=discord.File(fp=treaty_image, filename="vertrag_final.png"))
                await partner.send(file=discord.File(fp=treaty_image, filename="vertrag_final.png"))
                
            else:
                reason_msg = f" Grund: {rejection_reason}" if rejection_reason else ""
                await initiator.send(f"{partner.mention} hat deinen Vertrag ({treaty_data['type']}) abgelehnt.{reason_msg}")
        
        except discord.Forbidden:
            print(f"Cannot send DM to {initiator.name}")
        
        except Exception as e:
            print(f"Error finalizing treaty: {e}")
        
        # Remove the treaty from pending treaties
        if treaty_id in self.pending_treaties:
            del self.pending_treaties[treaty_id]
    
    @tasks.loop(hours=24)
    async def check_expired_treaties(self):
        """Überprüft regelmäßig abgelaufene Verträge und benachrichtigt die Parteien"""
        current_time = datetime.datetime.now()
        expired_treaties = []
        
        for treaty_id, treaty in self.active_treaties.items():
            if treaty["expiry_date"] <= current_time:
                expired_treaties.append(treaty_id)
                
                # Notify the parties
                initiator = treaty["initiator"]
                partner = treaty["partner"]
                treaty_type = treaty["type"]
                
                try:
                    # Notify initiator
                    await initiator.send(
                        f"Dein {treaty_type} mit {partner.mention} von {treaty['partner_country']} ist abgelaufen."
                    )
                except:
                    pass
                
                try:
                    # Notify partner
                    await partner.send(
                        f"Dein {treaty_type} mit {initiator.mention} von {treaty['initiator_country']} ist abgelaufen."
                    )
                except:
                    pass
        
        # Remove expired treaties
        for treaty_id in expired_treaties:
            if treaty_id in self.active_treaties:
                del self.active_treaties[treaty_id]
    
    # Ensure the task doesn't start until the bot is ready
    @check_expired_treaties.before_loop
    async def before_check_expired_treaties(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Treaties(bot))