#!/usr/bin/env python3
"""Mezcla audio contextual en los Reels legacy y los híbridos de Zira."""

import subprocess, os, json, sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
AUDIO = Path("/data/data/com.termux/files/home/ranchoraiz_reels/audio")
REELS = PROJECT / "assets" / "reels"
ZIRA = PROJECT / "assets" / "zira" / "posts"
OUT = PROJECT / "assets" / "reels" / "con_audio"

OUT.mkdir(parents=True, exist_ok=True)

# Mapeo: archivo_video -> archivo_audio (según ARTE_OPENCODE.md)
MAPA = {
    "pileta_reel.mp4":         "RiverMeditation.mp3",
    "atardecer_reel.mp4":      "AutumnSunset.mp3",
    "montanas_reel.mp4":       "GreenLeaves.mp3",
    "noche_reel.mp4":          "PaperWings.mp3",
    "brand_reel.mp4":          "AcousticGuitar1.mp3",
    "ranchoraiz_storytelling.mp4": "OpenRoad.mp3",
    # Híbridos de Zira
    "zira_hybrid_pileta2.mp4":      "RiverMeditation.mp3",
    "zira_hybrid_atardecer_reel.mp4": "AutumnSunset.mp3",
    "zira_hybrid_montanas_reel.mp4": "GreenLeaves.mp3",
    "zira_hybrid_noche_reel.mp4":    "PaperWings.mp3",
}

def mix_audio(video_path, audio_file, output_path):
    """Mezcla audio al video, recortando/loopando al duration del video."""
    # Obtener duración del video
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
        capture_output=True, text=True, timeout=15)
    duration = float(dur.stdout.strip())
    
    # Mezclar audio a 25% volumen
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_file),
        "-filter_complex",
        f"[1:a]volume=0.25,aloop=loop=-1:size=2e9[a1];[0:a][a1]amix=inputs=2:duration=first[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if output_path.exists() and output_path.stat().st_size > 0:
        size_kb = output_path.stat().st_size / 1024
        print(f"  ✅ {output_path.name} ({size_kb:.0f} KB)")
        return True
    else:
        print(f"  ❌ {output_path.name}: {result.stderr[-200:]}")
        return False

print("🎵 Mezclando audio contextual en Reels...")
print("="*50)

ok = 0
for video_name, audio_name in MAPA.items():
    # Determinar source
    src_reel = REELS / video_name
    src_zira = ZIRA / video_name
    src = src_reel if src_reel.exists() else src_zira
    
    if not src.exists():
        print(f"  ⏭️ {video_name}: no encontrado")
        continue
    
    audio_file = AUDIO / audio_name
    if not audio_file.exists():
        print(f"  ⏭️ {video_name}: audio {audio_name} no encontrado")
        continue
    
    output = OUT / video_name
    print(f"\n🎬 {video_name} ← {audio_name}")
    if mix_audio(src, audio_file, output):
        ok += 1

print(f"\n{'='*50}")
print(f"🏁 {ok}/{len(MAPA)} videos con audio mezclado en {OUT}")
