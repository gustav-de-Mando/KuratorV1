from PIL import Image, ImageDraw, ImageFilter
import random
import numpy as np
from io import BytesIO

def generate_parchment_background(width=1000, height=1400):
    """Generate a parchment-like background texture"""
    # Base color (light tan)
    parchment = Image.new('RGB', (width, height), (215, 190, 140))
    draw = ImageDraw.Draw(parchment)
    
    # Add noise for texture
    for x in range(width):
        for y in range(height):
            # Random variation in color
            noise = random.randint(-20, 20)
            r = min(max(215 + noise, 180), 230)
            g = min(max(190 + noise, 160), 210)
            b = min(max(140 + noise, 100), 160)
            
            # Apply darker areas to edges
            edge_x = min(x, width - x) / (width / 10)
            edge_y = min(y, height - y) / (height / 10)
            edge_factor = min(edge_x, edge_y)
            if edge_factor < 1:
                darkening = (1 - edge_factor) * 40
                r = max(r - darkening, 100)
                g = max(g - darkening, 80)
                b = max(b - darkening, 50)
            
            draw.point((x, y), fill=(int(r), int(g), int(b)))
    
    # Add some random darker spots and stains
    for _ in range(100):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        radius = random.randint(3, 30)
        color_shift = random.randint(-50, -20)
        
        for i in range(x - radius, x + radius):
            for j in range(y - radius, y + radius):
                if 0 <= i < width and 0 <= j < height:
                    distance = ((i - x) ** 2 + (j - y) ** 2) ** 0.5
                    if distance <= radius:
                        # Get current pixel color
                        pixel = parchment.getpixel((i, j))
                        fade = 1 - (distance / radius)
                        # Apply darker shade
                        new_color = (
                            max(0, int(pixel[0] + color_shift * fade)),
                            max(0, int(pixel[1] + color_shift * fade)),
                            max(0, int(pixel[2] + color_shift * fade))
                        )
                        draw.point((i, j), fill=new_color)
    
    # Apply slight blur for a more natural look
    parchment = parchment.filter(ImageFilter.GaussianBlur(radius=1))
    
    # Save to BytesIO object
    img_byte_arr = BytesIO()
    parchment.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return parchment

if __name__ == "__main__":
    # Test generate
    bg = generate_parchment_background()
    bg.save("parchment_test.png")