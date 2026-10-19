"""Fetch illustrative Unsplash photographs, never association portfolio claims."""

import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1] / 'demo-assets'
PHOTOS = {
    'nature': 'photo-1470770841072-f978cf4d019e',
    'city': 'photo-1449824913935-59a10b8d2000',
    'daily': 'photo-1441974231531-c6227db76b6e',
    'light': 'photo-1470252649378-9c29740c9fa8',
    'water': 'photo-1500375592092-40eb2168fd21',
    'architecture': 'photo-1487958449943-2429e8be8625',
}
ROOT.mkdir(parents=True, exist_ok=True)
credits = []
for name, photo in PHOTOS.items():
    url = f'https://images.unsplash.com/{photo}?auto=format&fit=crop&w=2000&q=85&fm=jpg'
    path = ROOT / f'{name}.jpg'
    if not path.exists():
        with urlopen(
            Request(url, headers={'User-Agent': 'PhotographyAssociationDemo/1.0'}), timeout=30
        ) as response:
            path.write_bytes(response.read())
    credits.append(
        {
            'file': path.name,
            'source': url,
            'provider': 'Unsplash',
            'usage': 'Illustrative layout sample. Replace with association-owned or authorized photographs before launch.',
        }
    )
    print(f'{path.name}: {path.stat().st_size} bytes')
(ROOT / 'credits.json').write_text(
    json.dumps(credits, ensure_ascii=False, indent=2), encoding='utf-8'
)
