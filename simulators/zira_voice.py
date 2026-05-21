#!/usr/bin/env python3
"""Spanish TTS helpers for Zira replies."""

from __future__ import annotations

import asyncio
from pathlib import Path


async def synthesize(text: str, output: Path, voice: str = "es-ES-ElviraNeural") -> Path:
    import edge_tts

    output.parent.mkdir(parents=True, exist_ok=True)
    communicator = edge_tts.Communicate(text=text, voice=voice)
    await communicator.save(str(output))
    return output


def synthesize_sync(text: str, output: Path, voice: str = "es-ES-ElviraNeural") -> Path:
    return asyncio.run(synthesize(text, output, voice=voice))
