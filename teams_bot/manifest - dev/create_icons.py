"""
Quick script to create Teams app icons
"""
from PIL import Image, ImageDraw, ImageFont

# Color icon (192x192) - Blue with white circle and "AI" text
print("Creating color icon (192x192)...")
img_color = Image.new('RGB', (192, 192), color='#0078D4')  # Microsoft Blue
draw_color = ImageDraw.Draw(img_color)

# Draw white circle background
draw_color.ellipse([36, 36, 156, 156], fill='white')

# Draw simple "AI" text (fallback if no font available)
try:
    # Try to use a system font
    font_large = ImageFont.truetype("arial.ttf", 72)
except:
    try:
        font_large = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 72)
    except:
        # Fallback to default font
        font_large = ImageFont.load_default()

# Draw "AI" text in center
draw_color.text((96, 96), "AI", fill='#0078D4', anchor="mm", font=font_large)

# Save color icon
img_color.save('color.png')
print("✓ Created color.png")

# Outline icon (32x32) - Transparent with white outline
print("Creating outline icon (32x32)...")
img_outline = Image.new('RGBA', (32, 32), color=(0, 0, 0, 0))  # Transparent background
draw_outline = ImageDraw.Draw(img_outline)

# Draw white circle outline
draw_outline.ellipse([2, 2, 30, 30], outline='white', width=3)

# Draw simple "AI" in center
try:
    font_small = ImageFont.truetype("arial.ttf", 14)
except:
    try:
        font_small = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 14)
    except:
        font_small = ImageFont.load_default()

draw_outline.text((16, 16), "AI", fill='white', anchor="mm", font=font_small)

# Save outline icon
img_outline.save('outline.png')
print("✓ Created outline.png")

print("\n✅ Icons created successfully!")
print("   - color.png (192x192 px)")
print("   - outline.png (32x32 px)")
