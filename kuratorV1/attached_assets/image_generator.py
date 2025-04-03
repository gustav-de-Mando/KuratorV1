import os
import textwrap
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

def generate_parchment_background(width=800, height=1100):
    """Generate a parchment-like background texture similar to the provided template"""
    # Base color (warm beige/tan like in the template)
    parchment = Image.new('RGB', (width, height), (226, 214, 181))
    draw = ImageDraw.Draw(parchment)

    # Add subtle noise for texture
    for x in range(0, width, 2):
        for y in range(0, height, 2):
            noise = int(8 * (x*y) % 9 / 10) - 4
            r = min(max(226 + noise, 218), 232)
            g = min(max(214 + noise, 206), 220)
            b = min(max(181 + noise, 173), 187)
            draw.point((x, y), fill=(int(r), int(g), int(b)))

    # Add darker edges/vignette effect for aged look
    for x in range(width):
        for y in range(height):
            # Calculate distance from edge
            distance_x = min(x, width - x) / (width / 6)
            distance_y = min(y, height - y) / (height / 6)
            distance = min(distance_x, distance_y)

            if distance < 1:
                # Create stronger darkening effect at edges
                darken = int(25 * (1 - distance))
                pixel = parchment.getpixel((x, y))
                # Apply slight yellow-brown tint to darkened areas
                new_r = max(0, pixel[0] - darken)
                new_g = max(0, pixel[1] - int(darken * 0.9))  # Less darkening on green
                new_b = max(0, pixel[2] - int(darken * 1.2))  # More darkening on blue
                parchment.putpixel((x, y), (new_r, new_g, new_b))

    return parchment

# Versuche, Schriftarten zu laden, ansonsten verwende Standardschriftart
# Verwende Arial-Schriftart, die bereits im Projekt vorhanden ist
try:
    # Schriftart-Pfad
    font_path = os.path.join(os.path.dirname(__file__), "../assets/fonts/arial.ttf")

    # Absolute Pfadangabe für besseres Debugging
    arial_path = os.path.abspath(font_path)

    print(f"Verwende Schriftart von: {arial_path}")

    # Prüfen, ob die Datei existiert und lesbar ist
    if os.path.exists(arial_path) and os.access(arial_path, os.R_OK):
        # Kleinere Schriftgrößen für kompakteres Layout
        title_font = ImageFont.truetype(arial_path, 36)      # Titel
        subtitle_font = ImageFont.truetype(arial_path, 24)   # Untertitel
        main_font = ImageFont.truetype(arial_path, 18)       # Haupttext
        signature_font = ImageFont.truetype(arial_path, 16)  # Unterschriften

        print("Arial-Schriftart erfolgreich geladen.")
    else:
        # Wenn die Datei nicht existiert oder nicht lesbar ist, verwende Standardschrift
        print(f"Arial-Schriftart nicht gefunden oder nicht lesbar: {arial_path}")
        raise FileNotFoundError(f"Schriftart nicht gefunden: {arial_path}")

except Exception as e:
    print(f"Fehler beim Laden der Schriftarten: {e}")
    # Fallback zu Standardschriftarten mit fester Größe
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()
    main_font = ImageFont.load_default()
    signature_font = ImageFont.load_default()

def generate_trade_agreement_image(initiator_name, partner_name, 
                                  initiator_country, partner_country,
                                  offer_resource, offer_amount,
                                  request_resource, request_amount,
                                  timestamp=None, vertragsbruch_klausel="", anmerkungen=""):
    """
    Erstellt ein Bild eines Handelsvertrags im klaren, formellen Stil.
    Gibt ein BytesIO-Objekt zurück, das das Bild enthält.
    """
    # Erstelle ein Pergament-ähnliches Bild
    width, height = 800, 1100

    # Generiere Pergament-Hintergrund
    background = generate_parchment_background(width, height)
    image = background

    # Erstelle ein Draw-Objekt
    draw = ImageDraw.Draw(image)

    # Rahmen (doppelt)
    draw.rectangle(((20, 20), (width-20, height-20)), outline=(139, 101, 57), width=2)
    draw.rectangle(((30, 30), (width-30, height-30)), outline=(139, 101, 57), width=1)

    # Titel in Großbuchstaben, gemäß der Vorlage
    title = "HANDELSVERTRAG"
    title_width = draw.textlength(title, font=title_font)
    draw.text(((width - title_width) // 2, 60), title, font=title_font, fill=(0, 0, 0))

    # Horizontale Linie unter dem Titel
    line_y = 120
    draw.line([(width//4, line_y), (width*3//4, line_y)], fill=(0, 0, 0), width=2)

    # Datum (neben dem Vertrag, wie im Beispiel)
    if timestamp is None:
        timestamp = datetime.now()
    date_str = f"Ausgestellt am {timestamp.strftime('%d.%m.%Y')}"
    date_width = draw.textlength(date_str, font=subtitle_font)
    draw.text((width - 100 - date_width, 120), date_str, font=subtitle_font, fill=(0, 0, 0))

    # Länder-Überschrift
    header_y = 220
    header_text = "ZWISCHEN DEN REICHEN"
    header_width = draw.textlength(header_text, font=subtitle_font)
    draw.text(((width - header_width) // 2, header_y), header_text, font=subtitle_font, fill=(0, 0, 0))

    # Länder
    countries_y = 260
    countries_text = f"{initiator_country} UND {partner_country}"
    countries_width = draw.textlength(countries_text, font=subtitle_font)
    draw.text(((width - countries_width) // 2, countries_y), countries_text, font=subtitle_font, fill=(0, 0, 0))

    # Standardklausel für Vertragsbruch, falls keine angegeben wurde
    standard_klausel = (
        "Der Schuldige muss das Doppelte des Wertes oder eine gleichwertige Entschädigung zahlen. "
        "Ein Vertragsbruchkrieg (§2.1.1) kann erklärt werden. "
        "Vertragsbrüche werden von der Spielleitung geprüft. "
        "Sanktionen können wirtschaftlicher, militärischer oder territorialer Natur sein."
    )

    # Verwende die angegebene Klausel oder die Standardklausel
    klausel_text = vertragsbruch_klausel if vertragsbruch_klausel else standard_klausel

    # Vertragstext
    agreement_text = f"""
Mit diesem Vertrag vereinbaren die beiden ehrenwerten Reiche einen Handelsaustausch zu den folgenden Bedingungen:

Das Reich {initiator_country} liefert:
{offer_amount} Einheiten {offer_resource}

Das Reich {partner_country} liefert im Gegenzug:
{request_amount} Einheiten {request_resource}

Beide Parteien bestätigen hiermit die Einhaltung der vereinbarten Handelsbedingungen. Dieser Vertrag wird wirksam mit der Unterschrift beider Herrscher und gilt fortan als bindendes Dokument zwischen den beiden Reichen.

Vertragsbruchklausel:
{klausel_text}
"""

    # Wenn Anmerkungen vorhanden sind, füge sie dem Vertragstext hinzu
    if anmerkungen:
        agreement_text += f"\nAnmerkungen:\n{anmerkungen}"

    # Text mit engerem Zeilenumbruch
    wrapper = textwrap.TextWrapper(width=80)  # Increased width for more text per line
    agreement_lines = []

    for line in agreement_text.split('\n'):
        if line.strip() == '':
            agreement_lines.append('')
        else:
            # Spezielle Behandlung für Überschriften
            if "liefert:" in line or "Vertragsbruchklausel:" in line or "Anmerkungen:" in line:
                agreement_lines.append(line)
            else:
                agreement_lines.extend(wrapper.wrap(line))

    # Zeichne den Vertragstext
    y_position = 320
    line_height = 28  # Reduziert für kompaktere Darstellung

    for line in agreement_lines:
        if line == '':
            y_position += line_height // 2
        else:
            draw.text((70, y_position), line, font=main_font, fill=(0, 0, 0))
            y_position += line_height

    # Platz für Unterschriften
    sig_y = 700 #moved down

    # Linke Unterschrift
    sig_line_length = 300
    left_sig_x = 100
    draw.line([(left_sig_x, sig_y), (left_sig_x + sig_line_length, sig_y)], fill=(0, 0, 0), width=1)

    signature_left = f"{initiator_name}"
    draw.text((left_sig_x + sig_line_length // 2 - draw.textlength(signature_left, font=signature_font) // 2, 
              sig_y - 30), signature_left, font=signature_font, fill=(0, 0, 0))

    initiator_title = f"Herrscher von {initiator_country}"
    draw.text((left_sig_x + sig_line_length // 2 - draw.textlength(initiator_title, font=signature_font) // 2, 
              sig_y + 10), initiator_title, font=signature_font, fill=(0, 0, 0))

    # Rechte Unterschrift
    right_sig_x = width - 100 - sig_line_length
    draw.line([(right_sig_x, sig_y), (right_sig_x + sig_line_length, sig_y)], fill=(0, 0, 0), width=1)

    signature_right = f"{partner_name}"
    draw.text((right_sig_x + sig_line_length // 2 - draw.textlength(signature_right, font=signature_font) // 2, 
              sig_y - 30), signature_right, font=signature_font, fill=(0, 0, 0))

    partner_title = f"Herrscher von {partner_country}"
    draw.text((right_sig_x + sig_line_length // 2 - draw.textlength(partner_title, font=signature_font) // 2, 
              sig_y + 10), partner_title, font=signature_font, fill=(0, 0, 0))

    # Einfaches rundes Siegel in der Mitte
    seal_position = (width // 2, sig_y)
    seal_radius = 30
    draw.ellipse((seal_position[0] - seal_radius, seal_position[1] - seal_radius, 
                 seal_position[0] + seal_radius, seal_position[1] + seal_radius), 
                 outline=(139, 0, 0), width=2)

    # Speichere das Bild in einem BytesIO-Objekt
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr

def generate_treaty_image(initiator_name, partner_name, 
                          initiator_country, partner_country,
                          treaty_type, expiry_date=None,
                          vertragsbruch_klausel="", anmerkungen=""):
    """
    Erstellt ein Bild eines Vertrags im formellen diplomatischen Stil.
    Gibt ein BytesIO-Objekt zurück, das das Bild enthält.
    """
    # Erstelle ein Pergament-ähnliches Bild
    width, height = 800, 1100

    # Generiere Pergament-Hintergrund
    background = generate_parchment_background(width, height)
    image = background

    # Erstelle ein Draw-Objekt
    draw = ImageDraw.Draw(image)

    # Rahmen (doppelt)
    draw.rectangle(((20, 20), (width-20, height-20)), outline=(139, 101, 57), width=2)
    draw.rectangle(((30, 30), (width-30, height-30)), outline=(139, 101, 57), width=1)

    # Titel in Großbuchstaben, gemäß der Vorlage
    title = "VERTRAG"
    title_width = draw.textlength(title, font=title_font)
    draw.text(((width - title_width) // 2, 60), title, font=title_font, fill=(0, 0, 0))

    # Horizontale Linie unter dem Titel
    line_y = 120
    draw.line([(width//4, line_y), (width*3//4, line_y)], fill=(0, 0, 0), width=2)

    # Vertragstyp unter Linie, falls gewünscht
    treaty_titles = {
        "Nichtangriffspakt": "NICHTANGRIFFSPAKT",
        "Schutzbündnis": "SCHUTZBÜNDNIS",
        "Allianzvertrag": "ALLIANZVERTRAG",
        "Hochzeitspakt": "HOCHZEITSPAKT",
        "Großallianzvertrag": "GROßALLIANZVERTRAG"
    }

    subtitle = treaty_titles.get(treaty_type, treaty_type.upper())
    subtitle_width = draw.textlength(subtitle, font=subtitle_font)
    draw.text(((width - subtitle_width) // 2, 140), subtitle, font=subtitle_font, fill=(0, 0, 0))

    # Datum (neben dem Vertrag, wie im Beispiel für beide Verträge)
    date_str = f"Ausgestellt am {datetime.now().strftime('%d.%m.%Y')}"
    date_width = draw.textlength(date_str, font=subtitle_font)
    draw.text((width - 100 - date_width, 120), date_str, font=subtitle_font, fill=(0, 0, 0))

    # Länder-Überschrift
    header_y = 220
    header_text = "ZWISCHEN DEN HOHEN REICHEN"
    header_width = draw.textlength(header_text, font=subtitle_font)
    draw.text(((width - header_width) // 2, header_y), header_text, font=subtitle_font, fill=(0, 0, 0))

    # Länder
    countries_y = 260
    countries_text = f"{initiator_country} UND {partner_country}"
    countries_width = draw.textlength(countries_text, font=subtitle_font)
    draw.text(((width - countries_width) // 2, countries_y), countries_text, font=subtitle_font, fill=(0, 0, 0))

    # Standardklausel für Vertragsbruch, falls keine angegeben wurde
    standard_klausel = (
        "Der Schuldige muss das Doppelte des Wertes oder eine gleichwertige Entschädigung zahlen. "
        "Ein Vertragsbruchkrieg (§2.1.1) kann erklärt werden. "
        "Vertragsbrüche werden von der Spielleitung geprüft. "
        "Sanktionen können wirtschaftlicher, militärischer oder territorialer Natur sein."
    )

    # Verwende die angegebene Klausel oder die Standardklausel
    klausel_text = vertragsbruch_klausel if vertragsbruch_klausel else standard_klausel

    # Spezifische Texte je nach Vertragstyp
    treaty_texts = {
        "Nichtangriffspakt": f"""
Die ehrenwerten Reiche {initiator_country} und {partner_country} vereinbaren hiermit,
dass sie von militärischen Handlungen gegeneinander absehen und den Frieden zwischen 
ihren Ländern bewahren werden. Dieser feierliche Pakt ist bindend und ehrhaft.

Beide Parteien verpflichten sich, keine direkten kriegerischen Handlungen gegeneinander 
zu unternehmen und den gegenseitigen Respekt zu wahren.
""",
        "Schutzbündnis": f"""
Hiermit vereinbaren die Reiche {initiator_country} und {partner_country} ein Schutzbündnis. 
Das ehrenwerte Reich {initiator_country} verpflichtet sich, das Reich {partner_country} 
bei einem Angriff durch eine dritte Partei zu unterstützen.

Beide Parteien stehen einander bei und werden im Falle eines Angriffs Beistand leisten,
um die Sicherheit und Souveränität des jeweils anderen Reiches zu wahren.
""",
        "Allianzvertrag": f"""
Die ehrenwerten Reiche {initiator_country} und {partner_country} schließen hiermit einen
Allianzvertrag. Diese Allianz verpflichtet beide Parteien zur gegenseitigen Unterstützung
in militärischen Konflikten und zur Förderung gemeinsamer Interessen.

Beide Parteien versprechen, in Zeiten der Not einander beizustehen und gemeinsam
die Sicherheit und den Wohlstand ihrer Reiche zu verteidigen.
""",
        "Hochzeitspakt": f"""
Im Namen der ehrenwerten Reiche {initiator_country} und {partner_country} wird hiermit ein
heiliger Hochzeitspakt geschlossen. Dieser Bund vereint nicht nur zwei edle Häuser,
sondern auch die Geschicke zweier großer Nationen.

Durch diesen Pakt werden die Bande der Freundschaft und der Treue gestärkt, und
beide Reiche versprechen, einander in allen Angelegenheiten loyal zur Seite zu stehen.
""",
        "Großallianzvertrag": f"""
Die mächtigen Reiche {initiator_country} und {partner_country} schließen hiermit einen
Großallianzvertrag. Diese umfassende Allianz verpflichtet beide Parteien zu voller
militärischer, diplomatischer und wirtschaftlicher Zusammenarbeit.

Beide Parteien schwören feierlich, in allen Konflikten gemeinsam zu handeln und
ihre Ressourcen, Armeen und diplomatische Macht zu vereinen, um ihre gemeinsamen
Ziele zu erreichen und ihre Feinde zu bezwingen.
"""
    }

    # Standardtext für unbekannte Vertragstypen
    default_text = f"""
Die ehrenwerten Reiche {initiator_country} und {partner_country} schließen hiermit einen
feierlichen Vertrag. Beide Parteien verpflichten sich zur Einhaltung der vereinbarten
Bedingungen und zur Wahrung des gegenseitigen Respekts.

Dieser Vertrag soll die Beziehungen zwischen den beiden Reichen stärken und
eine Grundlage für künftige Zusammenarbeit bilden.
"""

    # Vertragstext mit entsprechendem Inhalt
    treaty_text = treaty_texts.get(treaty_type, default_text)

    # Vollständiger Vertragstext
    agreement_text = f"{treaty_text}\n\nVertragsbruchklausel:\n{klausel_text}"

    # Ablaufdatum hinzufügen, falls vorhanden
    if expiry_date:
        expiry_str = expiry_date.strftime("%d.%m.%Y")
        agreement_text += f"\n\nDieser Vertrag ist gültig bis zum {expiry_str}."

    # Wenn Anmerkungen vorhanden sind, füge sie dem Vertragstext hinzu
    if anmerkungen:
        agreement_text += f"\n\nAnmerkungen:\n{anmerkungen}"

    # Text mit engerem Zeilenumbruch
    wrapper = textwrap.TextWrapper(width=80)  # Increased width for more text per line
    agreement_lines = []

    for line in agreement_text.split('\n'):
        if line.strip() == '':
            agreement_lines.append('')
        else:
            # Spezielle Behandlung für Überschriften
            if "liefert:" in line or "Vertragsbruchklausel:" in line or "Anmerkungen:" in line:
                agreement_lines.append(line)
            else:
                agreement_lines.extend(wrapper.wrap(line))

    # Zeichne den Vertragstext
    y_position = 320  # Erhöht von 260 auf 320, um Platz für die Überschriften zu lassen
    line_height = 28  # Reduziert für kompaktere Darstellung

    for line in agreement_lines:
        if line == '':
            y_position += line_height // 2
        else:
            draw.text((70, y_position), line, font=main_font, fill=(0, 0, 0))
            y_position += line_height

    # Platz für Unterschriften
    sig_y = 850 #moved down

    # Linke Unterschrift
    sig_line_length = 300
    left_sig_x = 100
    draw.line([(left_sig_x, sig_y), (left_sig_x + sig_line_length, sig_y)], fill=(0, 0, 0), width=1)

    signature_left = f"{initiator_name}"
    draw.text((left_sig_x + sig_line_length // 2 - draw.textlength(signature_left, font=signature_font) // 2, 
              sig_y - 30), signature_left, font=signature_font, fill=(0, 0, 0))

    initiator_title = f"Herrscher von {initiator_country}"
    draw.text((left_sig_x + sig_line_length // 2 - draw.textlength(initiator_title, font=signature_font) // 2, 
              sig_y + 10), initiator_title, font=signature_font, fill=(0, 0, 0))

    # Rechte Unterschrift
    right_sig_x = width - 100 - sig_line_length
    draw.line([(right_sig_x, sig_y), (right_sig_x + sig_line_length, sig_y)], fill=(0, 0, 0), width=1)

    signature_right = f"{partner_name}"
    draw.text((right_sig_x + sig_line_length // 2 - draw.textlength(signature_right, font=signature_font) // 2, 
              sig_y - 30), signature_right, font=signature_font, fill=(0, 0, 0))

    partner_title = f"Herrscher von {partner_country}"
    draw.text((right_sig_x + sig_line_length // 2 - draw.textlength(partner_title, font=signature_font) // 2, 
              sig_y + 10), partner_title, font=signature_font, fill=(0, 0, 0))

    # Einfaches rundes Siegel in der Mitte
    seal_position = (width // 2, sig_y)
    seal_radius = 30
    draw.ellipse((seal_position[0] - seal_radius, seal_position[1] - seal_radius, 
                 seal_position[0] + seal_radius, seal_position[1] + seal_radius), 
                 outline=(139, 0, 0), width=2)

    # Speichere das Bild in einem BytesIO-Objekt
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr