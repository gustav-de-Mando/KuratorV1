import io
import os
import random
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Load or create font objects
def get_font(font_name, size):
    font_paths = {
        'garamond': 'assets/fonts/garamond.ttf',
        'times_new_roman': 'assets/fonts/times_new_roman.ttf'
    }
    
    # Check if font exists or use default system font
    font_path = font_paths.get(font_name.lower())
    
    try:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
        else:
            # Fallback to default font
            try:
                return ImageFont.truetype("DejaVuSerif.ttf", size)
            except IOError:
                return ImageFont.load_default()
    except Exception as e:
        print(f"Error loading font: {e}")
        return ImageFont.load_default()

def generate_parchment_background(width=800, height=1100):
    """Generate a parchment-like background texture similar to the provided template"""
    # Create a base image with a light tan color
    base_color = (240, 230, 200)
    img = Image.new('RGB', (width, height), base_color)
    draw = ImageDraw.Draw(img)
    
    # Add noise and texture to the parchment
    for y in range(height):
        for x in range(width):
            # Random noise
            noise = random.randint(-10, 10)
            # Darker edges
            edge_darken = max(0, int(30 * (1 - min(x, width-x, y, height-y) / 150)))
            # Get current pixel color
            r, g, b = base_color
            # Apply effects
            r = max(0, min(255, r + noise - edge_darken))
            g = max(0, min(255, g + noise - edge_darken))
            b = max(0, min(255, b + noise - edge_darken))
            # Set pixel
            if x % 4 == 0 and y % 4 == 0:  # Only modify some pixels for performance
                draw.point((x, y), fill=(r, g, b))
    
    # Add some "stains" to make it look aged
    for _ in range(40):
        x = random.randint(0, width)
        y = random.randint(0, height)
        radius = random.randint(5, 50)
        opacity = random.randint(5, 20)
        color = (200 - random.randint(0, 30), 190 - random.randint(0, 40), 160 - random.randint(0, 40))
        
        # Draw a semi-transparent circle
        for r in range(radius):
            draw.ellipse((x-r, y-r, x+r, y+r), fill=color + (opacity,))
    
    # Apply slight blur for a smoother look
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    return img

def generate_trade_agreement_image(initiator_name, partner_name, 
                                  initiator_country, partner_country,
                                  offer_resource, offer_amount,
                                  request_resource, request_amount,
                                  timestamp=None, vertragsbruch_klausel="", anmerkungen=""):
    """
    Erstellt ein Bild eines Handelsvertrags im klaren, formellen Stil.
    Gibt ein BytesIO-Objekt zurück, das das Bild enthält.
    """
    # Verwende aktuelle Zeit, falls nicht angegeben
    if timestamp is None:
        timestamp = datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")
    
    # Erstelle Pergament-Hintergrund
    img = generate_parchment_background()
    width, height = img.size
    draw = ImageDraw.Draw(img)
    
    # Lade Schriftarten
    title_font = get_font('garamond', 48)
    header_font = get_font('garamond', 34)
    content_font = get_font('garamond', 24)
    small_font = get_font('garamond', 18)
    
    # Titel
    title = "HANDELSVERTRAG"
    title_width = draw.textlength(title, font=title_font)
    draw.text(((width - title_width) // 2, 50), title, fill=(10, 10, 40), font=title_font)
    
    # Linie unter dem Titel
    draw.line([(width//4, 120), (3*width//4, 120)], fill=(70, 30, 10), width=2)
    
    # Unterzeichner-Header
    draw.text((50, 160), "Zwischen den ehrenwerten Herrschern", fill=(10, 10, 40), font=header_font)
    
    # Unterzeichner
    draw.text((100, 220), f"{initiator_name} von {initiator_country}", fill=(10, 10, 40), font=content_font)
    draw.text((100, 260), f"und", fill=(10, 10, 40), font=content_font)
    draw.text((100, 300), f"{partner_name} von {partner_country}", fill=(10, 10, 40), font=content_font)
    
    # Vereinbarung-Header
    draw.text((50, 370), "Wurde folgende Handelsvereinbarung getroffen:", fill=(10, 10, 40), font=header_font)
    
    # Angebot und Nachfrage
    draw.text((100, 440), f"{initiator_country} bietet:", fill=(10, 10, 40), font=content_font)
    draw.text((150, 480), f"{offer_amount} {offer_resource}", fill=(10, 10, 40), font=content_font)
    
    draw.text((100, 540), f"{partner_country} bietet:", fill=(10, 10, 40), font=content_font)
    draw.text((150, 580), f"{request_amount} {request_resource}", fill=(10, 10, 40), font=content_font)
    
    # Vertragsbruch-Klausel
    if vertragsbruch_klausel:
        draw.text((50, 650), "Vertragsbruch-Klausel:", fill=(10, 10, 40), font=content_font)
        
        # Text-Wrapping für lange Klauseln
        wrapped_text = textwrap.fill(vertragsbruch_klausel, width=50)
        y_position = 690
        for line in wrapped_text.split('\n'):
            draw.text((70, y_position), line, fill=(10, 10, 40), font=small_font)
            y_position += 25
    else:
        y_position = 650
    
    # Anmerkungen
    if anmerkungen:
        draw.text((50, y_position + 40), "Anmerkungen:", fill=(10, 10, 40), font=content_font)
        
        wrapped_anmerkungen = textwrap.fill(anmerkungen, width=50)
        y_position += 80
        for line in wrapped_anmerkungen.split('\n'):
            draw.text((70, y_position), line, fill=(10, 10, 40), font=small_font)
            y_position += 25
    
    # Unterzeichnet und Datum
    y_position = max(y_position + 70, 820)
    
    date_text = f"Unterzeichnet am {timestamp}"
    date_width = draw.textlength(date_text, font=content_font)
    draw.text(((width - date_width) // 2, y_position), date_text, fill=(10, 10, 40), font=content_font)
    
    # Unterschriftslinien
    sign_y = y_position + 70
    line_width = width // 3
    
    # Erste Unterschrift
    draw.line([(width//6, sign_y), (width//6 + line_width, sign_y)], fill=(30, 30, 30), width=1)
    name_text = initiator_name
    name_width = draw.textlength(name_text, font=small_font)
    draw.text(((width//6 + line_width//2 - name_width//2), sign_y + 10), name_text, fill=(10, 10, 40), font=small_font)
    
    # Zweite Unterschrift
    draw.line([(width//2 + width//6, sign_y), (width//2 + width//6 + line_width, sign_y)], fill=(30, 30, 30), width=1)
    name_text = partner_name
    name_width = draw.textlength(name_text, font=small_font)
    draw.text(((width//2 + width//6 + line_width//2 - name_width//2), sign_y + 10), name_text, fill=(10, 10, 40), font=small_font)
    
    # Dekorative Elemente - Siegel/Wappen
    seal_size = 100
    seal_padding = 30
    
    # Erstes Siegel links
    seal_x = width//6 + line_width//2 - seal_size//2
    seal_y = sign_y + 50
    draw.ellipse((seal_x - seal_padding, seal_y - seal_padding, 
                 seal_x + seal_size + seal_padding, seal_y + seal_size + seal_padding), 
                 outline=(120, 40, 30), width=3)
    
    # Zweites Siegel rechts
    seal_x = width//2 + width//6 + line_width//2 - seal_size//2
    draw.ellipse((seal_x - seal_padding, seal_y - seal_padding, 
                 seal_x + seal_size + seal_padding, seal_y + seal_size + seal_padding), 
                 outline=(120, 40, 30), width=3)
    
    # Generiere das Bild als Bytes-Objekt
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
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
    # Aktuelles Datum, falls kein Ablaufdatum angegeben
    current_date = datetime.now().strftime("%d.%m.%Y")
    if expiry_date is None:
        expiry_date = "unbegrenzt"
    
    # Erstelle Pergament-Hintergrund
    img = generate_parchment_background()
    width, height = img.size
    draw = ImageDraw.Draw(img)
    
    # Lade Schriftarten
    title_font = get_font('garamond', 48)
    header_font = get_font('garamond', 34)
    content_font = get_font('garamond', 24)
    small_font = get_font('garamond', 18)
    
    # Titel
    title = treaty_type.upper()
    title_width = draw.textlength(title, font=title_font)
    draw.text(((width - title_width) // 2, 50), title, fill=(10, 10, 40), font=title_font)
    
    # Linie unter dem Titel
    draw.line([(width//4, 120), (3*width//4, 120)], fill=(70, 30, 10), width=2)
    
    # Unterzeichner-Header
    draw.text((50, 160), "Zwischen den ehrenwerten Herrschern", fill=(10, 10, 40), font=header_font)
    
    # Unterzeichner
    draw.text((100, 220), f"{initiator_name} von {initiator_country}", fill=(10, 10, 40), font=content_font)
    draw.text((100, 260), f"und", fill=(10, 10, 40), font=content_font)
    draw.text((100, 300), f"{partner_name} von {partner_country}", fill=(10, 10, 40), font=content_font)
    
    # Vereinbarung-Header
    draw.text((50, 370), "Wird folgender Vertrag geschlossen:", fill=(10, 10, 40), font=header_font)
    
    # Vertragsinhalt - je nach Vertragstyp
    treaty_explanation = ""
    if treaty_type == "Nichtangriffspakt":
        treaty_explanation = "Die unterzeichnenden Parteien verpflichten sich, für die Dauer des Vertrags keine militärischen Aktionen gegeneinander durchzuführen und von feindlichen Handlungen abzusehen."
    elif treaty_type == "Schutzbündnis":
        treaty_explanation = "Im Falle eines Angriffs auf eine der unterzeichnenden Parteien verpflichtet sich die andere Partei, militärischen Beistand zu leisten und der angegriffenen Partei zur Seite zu stehen."
    elif treaty_type == "Allianzvertrag":
        treaty_explanation = "Die unterzeichnenden Parteien verpflichten sich zu einer umfassenden Allianz, die militärische, wirtschaftliche und diplomatische Zusammenarbeit umfasst. Keine Partei darf ohne Zustimmung der anderen in Konflikte eintreten."
    elif treaty_type == "Hochzeitspakt":
        treaty_explanation = "Durch die Verbindung der Herrscherhäuser in einer Hochzeit verpflichten sich die Parteien zu ewiger Freundschaft, gegenseitiger Unterstützung und der Förderung beider Reiche als vereinte Familie."
    elif treaty_type == "Großallianzvertrag":
        treaty_explanation = "Die Parteien schließen sich in einer Großallianz zusammen, die alle Aspekte der zwischenstaatlichen Beziehungen umfasst. Dies beinhaltet gemeinsame Verteidigung, wirtschaftliche Integration und eine vereinte Außenpolitik."
    
    # Vertragsinhalt
    wrapped_explanation = textwrap.fill(treaty_explanation, width=50)
    y_position = 440
    for line in wrapped_explanation.split('\n'):
        draw.text((70, y_position), line, fill=(10, 10, 40), font=content_font)
        y_position += 35
    
    # Vertragsdauer
    y_position += 20
    draw.text((70, y_position), f"Vertragsdauer: {expiry_date}", fill=(10, 10, 40), font=content_font)
    
    # Vertragsbruch-Klausel
    if vertragsbruch_klausel:
        y_position += 50
        draw.text((50, y_position), "Vertragsbruch-Klausel:", fill=(10, 10, 40), font=content_font)
        
        # Text-Wrapping für lange Klauseln
        wrapped_text = textwrap.fill(vertragsbruch_klausel, width=50)
        y_position += 40
        for line in wrapped_text.split('\n'):
            draw.text((70, y_position), line, fill=(10, 10, 40), font=small_font)
            y_position += 25
    
    # Anmerkungen
    if anmerkungen:
        y_position += 30
        draw.text((50, y_position), "Anmerkungen:", fill=(10, 10, 40), font=content_font)
        
        wrapped_anmerkungen = textwrap.fill(anmerkungen, width=50)
        y_position += 40
        for line in wrapped_anmerkungen.split('\n'):
            draw.text((70, y_position), line, fill=(10, 10, 40), font=small_font)
            y_position += 25
    
    # Unterzeichnet und Datum
    y_position = max(y_position + 50, 820)
    
    date_text = f"Unterzeichnet am {current_date}"
    date_width = draw.textlength(date_text, font=content_font)
    draw.text(((width - date_width) // 2, y_position), date_text, fill=(10, 10, 40), font=content_font)
    
    # Unterschriftslinien
    sign_y = y_position + 70
    line_width = width // 3
    
    # Erste Unterschrift
    draw.line([(width//6, sign_y), (width//6 + line_width, sign_y)], fill=(30, 30, 30), width=1)
    name_text = initiator_name
    name_width = draw.textlength(name_text, font=small_font)
    draw.text(((width//6 + line_width//2 - name_width//2), sign_y + 10), name_text, fill=(10, 10, 40), font=small_font)
    
    # Zweite Unterschrift
    draw.line([(width//2 + width//6, sign_y), (width//2 + width//6 + line_width, sign_y)], fill=(30, 30, 30), width=1)
    name_text = partner_name
    name_width = draw.textlength(name_text, font=small_font)
    draw.text(((width//2 + width//6 + line_width//2 - name_width//2), sign_y + 10), name_text, fill=(10, 10, 40), font=small_font)
    
    # Dekorative Elemente - Siegel/Wappen
    seal_size = 100
    seal_padding = 30
    
    # Erstes Siegel links
    seal_x = width//6 + line_width//2 - seal_size//2
    seal_y = sign_y + 50
    draw.ellipse((seal_x - seal_padding, seal_y - seal_padding, 
                 seal_x + seal_size + seal_padding, seal_y + seal_size + seal_padding), 
                 outline=(120, 40, 30), width=3)
    
    # Zweites Siegel rechts
    seal_x = width//2 + width//6 + line_width//2 - seal_size//2
    draw.ellipse((seal_x - seal_padding, seal_y - seal_padding, 
                 seal_x + seal_size + seal_padding, seal_y + seal_size + seal_padding), 
                 outline=(120, 40, 30), width=3)
    
    # Generiere das Bild als Bytes-Objekt
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr