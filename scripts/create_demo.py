from PIL import Image, ImageDraw
import os

os.makedirs('demo', exist_ok=True)

# Generate demo faces
for i, name in enumerate(['subject1', 'subject2', 'subject3']):
    img = Image.new('RGB', (400, 400), color=(220 + i*10, 210 + i*5, 200 + i*5))
    draw = ImageDraw.Draw(img)
    # Simple face
    draw.ellipse([100 + i*5, 80 + i*5, 300 - i*5, 300 - i*5], fill=(200 + i*10, 190, 180))
    draw.ellipse([160 + i*5, 170 + i*5, 190 + i*5, 200 + i*5], fill=(50, 50, 50))
    draw.ellipse([210 + i*5, 170 + i*5, 240 + i*5, 200 + i*5], fill=(50, 50, 50))
    draw.polygon([(200 + i*5, 195), (185 + i*5, 220), (215 + i*5, 220)], fill=(200, 180, 160))
    draw.arc([160 + i*5, 230, 240 + i*5, 260], start=0, end=180, fill=(150, 80, 80), width=3)
    draw.text((20, 20), name, fill=(100, 100, 100))
    img.save(f'demo/{name}.jpg')

print("Generated 3 demo faces in demo/ directory")
for f in os.listdir('demo'):
    print(f"  {f}")
