#!/usr/bin/env python3
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent.parent / "public" / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

ASSETS = [
    (
        "hero-bg.jpg",
        "https://images.unsplash.com/photo-1605152276897-4f618f831968?ixlib=rb-1.2.1&auto=format&fit=crop&w=1600&q=80",
        (1600, 960),
        "Hero",
    ),
    (
        "about-image.jpg",
        "https://images.unsplash.com/photo-1503387762-592deb58ef4e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1400&q=80",
        (1400, 900),
        "About",
    ),
    (
        "portfolio-1.jpg",
        "https://images.unsplash.com/photo-1469474968028-56623f02e42e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1200&q=80",
        (1200, 800),
        "Project 1",
    ),
    (
        "portfolio-2.jpg",
        "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?ixlib=rb-1.2.1&auto=format&fit=crop&w=1200&q=80",
        (1200, 800),
        "Project 2",
    ),
    (
        "portfolio-3.jpg",
        "https://images.unsplash.com/photo-1505843513577-22bb7d21e455?ixlib=rb-1.2.1&auto=format&fit=crop&w=1200&q=80",
        (1200, 800),
        "Project 3",
    ),
    (
        "portfolio-4.jpg",
        "https://images.unsplash.com/photo-1483478550801-ceba5fe50e8e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1200&q=80",
        (1200, 800),
        "Project 4",
    ),
    (
        "review-1.jpg",
        "https://randomuser.me/api/portraits/men/32.jpg",
        (512, 512),
        "Александр",
    ),
    (
        "review-2.jpg",
        "https://randomuser.me/api/portraits/women/44.jpg",
        (512, 512),
        "Елена",
    ),
    (
        "review-3.jpg",
        "https://randomuser.me/api/portraits/men/75.jpg",
        (512, 512),
        "Дмитрий",
    ),
]

COLORS = [
    (17, 17, 17),
    (40, 40, 40),
    (255, 212, 0),
    (255, 229, 102),
    (108, 108, 108),
]


def create_placeholder(size, label):
    width, height = size
    image = Image.new("RGB", size, COLORS[0])
    overlay = Image.new("RGBA", size, (255, 212, 0, 38))
    image.paste(Image.new("RGB", size, (17, 17, 17)), mask=None)
    image = image.convert("RGBA")
    image.alpha_composite(overlay)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text = f"{label}"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text(
        ((width - text_width) / 2, (height - text_height) / 2),
        text,
        fill=(255, 255, 255, 220),
        font=font,
    )
    return image.convert("RGB")


def download_asset(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.content


for filename, url, size, label in ASSETS:
    target_path = ASSETS_DIR / filename
    if target_path.exists():
        continue
    try:
        data = download_asset(url)
        target_path.write_bytes(data)
        print(f"Saved {filename} from {url}")
        continue
    except Exception as error:
        print(f"Failed to download {url}: {error}. Creating placeholder.")
    placeholder = create_placeholder(size, label)
    placeholder.save(target_path, format="JPEG", quality=85)
    print(f"Created placeholder {filename}")