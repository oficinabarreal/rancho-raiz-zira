#!/usr/bin/env python3
"""Convertir SVGs de frases Zira a PNG para Instagram."""
import json
from pathlib import Path
from cairosvg import svg2png

FRASES_DIR = Path(__file__).resolve().parent.parent / "zira-frases"
PNG_DIR = FRASES_DIR / "png"
PNG_DIR.mkdir(exist_ok=True)

manifest = json.loads((FRASES_DIR / "manifest.json").read_text())

print(f"🔄 Convirtiendo {len(manifest)} banners SVG -> PNG...\n")
for item in manifest:
    svg_path = FRASES_DIR / item["archivo"]
    png_name = item["archivo"].replace(".svg", ".png")
    png_path = PNG_DIR / png_name
    
    svg2png(
        bytestring=svg_path.read_bytes(),
        write_to=str(png_path),
        output_width=1080,
        output_height=1080,
    )
    size_kb = png_path.stat().st_size / 1024
    print(f"  ✅ {png_name}  ({size_kb:.0f} KB) - {item['estilo'].upper()}")

print(f"\n🏁 {len(manifest)} PNGs en {PNG_DIR}/")
