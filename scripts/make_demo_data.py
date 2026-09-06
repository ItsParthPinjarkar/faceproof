"""
Generate demo data for testing without API keys.
"""
import os
import json
import tempfile
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import hashlib

def generate_demo_face(path: str = 'demo/subject.jpg', label: str = 'Demo Person'):
    """Generate a synthetic face image for demo/testing."""
    os.makedirs('demo', exist_ok=True)

    img = Image.new('RGB', (400, 400), color=(240, 230, 220))
    draw = ImageDraw.Draw(img)

    # Draw a simple face
    # Head circle
    draw.ellipse([100, 80, 300, 300], fill=(220, 200, 180), outline=(150, 130, 110))
    # Eyes
    draw.ellipse([150, 160, 180, 190], fill=(50, 50, 50))
    draw.ellipse([220, 160, 250, 190], fill=(50, 50, 50))
    # Eye whites
    draw.ellipse([148, 158, 182, 192], fill=(255, 255, 255))
    draw.ellipse([218, 158, 252, 192], fill=(255, 255, 255))
    # Nose
    draw.polygon([(200, 195), (185, 220), (215, 220)], fill=(200, 180, 160))
    # Mouth
    draw.arc([160, 230, 240, 260], start=0, end=180, fill=(150, 80, 80), width=3)
    # Label
    draw.text((20, 20), label, fill=(100, 100, 100))

    img.save(path)
    print(f"Generated demo face: {path}")
    return path

def generate_demo_dataset():
    """Generate a full demo dataset with multiple faces."""
    os.makedirs('demo', exist_ok=True)
    faces = ['subject1', 'subject2', 'subject3']

    for i, name in enumerate(faces):
        path = f'demo/{name}.jpg'
        img = Image.new('RGB', (400, 400), color=(220 + i*10, 210 + i*5, 200 + i*5))
        draw = ImageDraw.Draw(img)
        draw.ellipse([100 + i*5, 80 + i*5, 300 - i*5, 300 - i*5], fill=(200 + i*10, 190, 180))
        draw.ellipse([160 + i*5, 170 + i*5, 190 + i*5, 200 + i*5], fill=(50, 50, 50))
        draw.ellipse([210 + i*5, 170 + i*5, 240 + i*5, 200 + i*5], fill=(50, 50, 50))
        img.save(path)

    # Create demo search results
    demo_results = {
        'search_results': [
            {'url': 'https://example.com/demo-post-1', 'title': 'Demo Post 1', 'domain': 'example.com', 'snippet': 'Demo result 1', 'match_type': 'visual_match', 'platform': 'Demo', '_is_demo': True},
            {'url': 'https://example.com/demo-post-2', 'title': 'Demo Post 2', 'domain': 'example.com', 'snippet': 'Demo result 2', 'match_type': 'visual_match', 'platform': 'Demo', '_is_demo': True}
        ]
    }
    with open('demo/demo_results.json', 'w') as f:
        json.dump(demo_results, f, indent=2)

    print(f"Generated {len(faces)} demo faces and search results")

if __name__ == '__main__':
    generate_demo_dataset()
