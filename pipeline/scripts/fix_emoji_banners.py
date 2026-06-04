#!/usr/bin/env python3
"""
FIX: Reemplaza emoji text en todos los SVGs con formas SVG inline.
Luego convierte a PNG con cairosvg (ahora sin emoji text, funciona).
"""
import sys, os, json, subprocess
from pathlib import Path

BASE = Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
SVG_DIR = BASE / "pipeline" / "zira-frases"
PNG_DIR = SVG_DIR / "png-v3"  # fresh version

# Import the emoji components - direct file load
import importlib.util
_emoji_spec = importlib.util.spec_from_file_location("emoji_components", 
    str(BASE / "pipeline" / "scripts" / "svg_emoji_components.py"))
_emoji_mod = importlib.util.module_from_spec(_emoji_spec)
_emoji_spec.loader.exec_module(_emoji_mod)
replace_emoji_in_svg = _emoji_mod.replace_emoji_in_svg
EMOJI_SVG = _emoji_mod.EMOJI_SVG

print("🏔️  FIX: Reemplazando emoji text por SVG shapes en todos los banners...\n")

# Load manifest
manifest = json.loads((SVG_DIR / "manifest.json").read_text())

# Process each SVG
fixed_count = 0
for item in manifest:
    svg_path = SVG_DIR / item["archivo"]
    original = svg_path.read_text()
    
    # Check if emoji exists
    emoji_char = item["emoji"]
    has_emoji = emoji_char in original
    
    if has_emoji:
        fixed = replace_emoji_in_svg(original)
        svg_path.write_text(fixed)
        fixed_count += 1
        print(f"  ✅ {item['archivo']}: {emoji_char} reemplazado")
    else:
        print(f"  ⏭️  {item['archivo']}: sin emoji text")
    
    # Also update manifest to mark as SVG-emoji
    item["emoji_svg"] = True

# Save updated manifest
manifest_path = SVG_DIR / "manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

print(f"\n📊 {fixed_count}/{len(manifest)} SVGs actualizados con SVG shapes")

# ─── Convertir a PNG con cairosvg ───
print(f"\n🔄 Convirtiendo a PNG con cairosvg...")
PNG_DIR.mkdir(exist_ok=True)

success = 0
for item in manifest:
    svg_path = SVG_DIR / item["archivo"]
    png_name = item["archivo"].replace(".svg", ".png")
    png_path = PNG_DIR / png_name
    
    cmd = [
        sys.executable, "-c",
        f"import cairosvg; cairosvg.svg2png(url='{svg_path}', output_width=1080, output_height=1080, write_to='{png_path}')"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    if png_path.exists() and png_path.stat().st_size > 1000:
        size = png_path.stat().st_size / 1024
        print(f"  ✅ {png_name} ({size:.0f} KB)")
        success += 1
    else:
        err = result.stderr.strip()[-200:] if result.stderr else "unknown error"
        print(f"  ❌ {png_name}: {err}")

print(f"\n🏁 {success}/{len(manifest)} PNGs generados en {PNG_DIR}/")

# ─── Copiar a png/ para Instagram ───
if success == len(manifest):
    print(f"\n📋 Copiando a pipeline/zira-frases/png/...")
    target_dir = SVG_DIR / "png"
    for item in manifest:
        src = PNG_DIR / item["archivo"].replace(".svg", ".png")
        dst = target_dir / item["archivo"].replace(".svg", ".png")
        dst.write_bytes(src.read_bytes())
    print(f"   ✅ {success} archivos copiados")
    
    # Push to GitHub
    print(f"\n🚀 Pusheando a GitHub...")
    result = subprocess.run(
        ["git", "add", "-A", str(SVG_DIR)], 
        capture_output=True, text=True, timeout=10,
        cwd=str(BASE)
    )
    result = subprocess.run(
        ["git", "commit", "-m", "🎨 fix: SVG emoji shapes en vez de texto emoji (cairosvg compatible)"],
        capture_output=True, text=True, timeout=10,
        cwd=str(BASE)
    )
    print(f"   {result.stdout}")
    result = subprocess.run(
        ["git", "push"], 
        capture_output=True, text=True, timeout=30,
        cwd=str(BASE)
    )
    if result.returncode == 0:
        print(f"   ✅ Push exitoso")
    else:
        print(f"   ⚠️ Push: {result.stderr[:200]}")
else:
    print(f"\n⚠️  No todos los PNGs se generaron, no se copia ni pushea")
