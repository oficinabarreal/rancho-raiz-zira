#!/usr/bin/env python3
"""Re-renderizar banners SVG a PNG usando Chromium headless (soporta emojis)."""
import json, subprocess, os
from pathlib import Path

BASE = Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
SVG_DIR = BASE / "pipeline" / "zira-frases"
PNG_DIR = SVG_DIR / "png-v2"
HTML_DIR = SVG_DIR / "html_render"
PNG_DIR.mkdir(exist_ok=True)
HTML_DIR.mkdir(exist_ok=True)

CHROMIUM = "/data/data/com.termux/files/usr/bin/chromium-browser"

manifest = json.loads((SVG_DIR / "manifest.json").read_text())

print(f"🔄 Re-renderizando {len(manifest)} banners con Chromium (con emojis!)\n")

for i, item in enumerate(manifest, 1):
    svg_path = SVG_DIR / item["archivo"]
    html_name = item["archivo"].replace(".svg", ".html")
    html_path = HTML_DIR / html_name
    png_name = item["archivo"].replace(".svg", ".png")
    png_path = PNG_DIR / png_name
    
    # Crear HTML wrapper
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ margin:0; background:#0f172a; width:1080px; height:1080px; display:flex; align-items:center; justify-content:center; }}
svg {{ width:1080px; height:1080px; }}
</style></head>
<body>
{svg_path.read_text()}
</body></html>"""
    html_path.write_text(html)
    
    # Renderizar con Chromium headless
    url = f"file://{html_path.resolve()}"
    cmd = [
        CHROMIUM, "--headless", "--no-sandbox", "--disable-gpu",
        "--window-size=1080,1080",
        f"--screenshot={png_path}",
        url,
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    if png_path.exists() and png_path.stat().st_size > 5000:
        size = png_path.stat().st_size / 1024
        print(f"  ✅ [{i}/{len(manifest)}] {png_name} ({size:.0f} KB) - {item['estilo'].upper()}")
    else:
        sz = png_path.stat().st_size if png_path.exists() else 0
        print(f"  ❌ [{i}/{len(manifest)}] {item['archivo']}: {sz} bytes")
        if result.stderr:
            err = result.stderr[-300:]
            print(f"     {err}")

print(f"\n🏁 {len(manifest)} PNGs con emojis en {PNG_DIR}/")

# Verificar que no sean blancos
from PIL import Image
import numpy as np
blancos = 0
for item in manifest:
    png_path = PNG_DIR / item["archivo"].replace(".svg", ".png")
    if png_path.exists():
        arr = np.array(Image.open(png_path))
        if arr.mean() > 250:
            blancos += 1
            print(f"  ⚠️  {png_path.name}: parece blanco (mean={arr.mean():.0f})")

print(f"Banderas blancas: {blancos}/{len(manifest)}")
