#!/usr/bin/env python3
"""Photo ingestion and light editing pipeline for Zira.

The goal is not professional retouching. The goal is to create publishable
variants quickly from a client-sent Telegram photo:

- store the original
- generate square / feed / story crops
- build a contact-sheet preview
- generate metadata for a future publish step
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps


BASE_DIR = Path(__file__).resolve().parent
PHOTO_DIR = BASE_DIR / "zira_media"
QUEUE_DIR = PHOTO_DIR / "queue"
ORIGINAL_DIR = PHOTO_DIR / "originals"
EDIT_DIR = PHOTO_DIR / "edited"
PREVIEW_DIR = PHOTO_DIR / "previews"
READY_DIR = PHOTO_DIR / "ready"
META_DIR = PHOTO_DIR / "meta"


@dataclass
class PhotoArtifact:
    kind: str
    path: str


@dataclass
class PhotoJob:
    job_id: str
    source: str
    caption: str
    created_at: str
    artifacts: List[PhotoArtifact]
    suggested_caption: str
    hashtags: List[str]
    status: str = "queued"


def ensure_dirs() -> None:
    for directory in [PHOTO_DIR, QUEUE_DIR, ORIGINAL_DIR, EDIT_DIR, PREVIEW_DIR, READY_DIR, META_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def _safe_open(path: Path) -> Image.Image:
    image = Image.open(path)
    image = ImageOps.exif_transpose(image)
    return image.convert("RGB")


def _fit_inside(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGB", size, (20, 20, 20))
    fitted = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    x = (size[0] - fitted.size[0]) // 2
    y = (size[1] - fitted.size[1]) // 2
    canvas.paste(fitted, (x, y))
    return canvas


def _crop_cover(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))


def _render_label(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, fill: Tuple[int, int, int] = (255, 255, 255)) -> None:
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 26)
    except Exception:
        font = ImageFont.load_default()
    draw.text((x, y), text, fill=fill, font=font)


def _build_contact_sheet(source: Image.Image, variants: Dict[str, Image.Image], caption: str) -> Image.Image:
    sheet = Image.new("RGB", (1600, 1200), (14, 18, 24))
    draw = ImageDraw.Draw(sheet)
    thumbs = {
        "source": _fit_inside(source, (760, 500)),
        "square": _fit_inside(variants["square"], (360, 240)),
        "feed": _fit_inside(variants["feed"], (360, 240)),
        "story": _fit_inside(variants["story"], (360, 240)),
    }

    sheet.paste(thumbs["source"], (40, 40))
    sheet.paste(thumbs["square"], (840, 40))
    sheet.paste(thumbs["feed"], (840, 320))
    sheet.paste(thumbs["story"], (840, 600))

    _render_label(draw, "Original", 40, 20)
    _render_label(draw, "Square", 840, 20)
    _render_label(draw, "Feed 4:5", 840, 300)
    _render_label(draw, "Story 9:16", 840, 580)
    _render_label(draw, "Zira photo preview", 40, 560)
    _render_label(draw, caption[:80], 40, 610)

    # add a subtle footer with the processing note
    footer = Image.new("RGBA", (1600, 180), (0, 0, 0, 0))
    footer_draw = ImageDraw.Draw(footer)
    footer_draw.rounded_rectangle((40, 20, 1560, 150), radius=28, fill=(28, 36, 46, 220))
    _render_label(footer_draw, "Ready for review, edit, and publish.", 70, 55, fill=(240, 240, 240))
    _render_label(footer_draw, "This preview is generated automatically from Telegram.", 70, 95, fill=(180, 190, 200))
    sheet.paste(footer, (0, 1000), footer)
    return sheet


def _caption_from_name(name: str) -> Tuple[str, List[str]]:
    low = name.lower()
    if any(k in low for k in ["piscina", "pileta"]):
        return "Piscina y descanso en Barreal", ["#Barreal", "#Calingasta", "#SanJuan", "#Posada"]
    if any(k in low for k in ["habitacion", "cuarto", "room"]):
        return "Habitación lista para una escapada en la cordillera", ["#Barreal", "#Alojamiento", "#Cordillera", "#Andes"]
    if any(k in low for k in ["arroyo", "rio", "river"]):
        return "Paisaje de montaña para tu próxima escapada", ["#Barreal", "#TurismoRural", "#Andes", "#SanJuan"]
    return "Barreal, San Juan. Cordillera y descanso.", ["#Barreal", "#Calingasta", "#SanJuan", "#Andes"]


def process_photo(source_path: Path, caption: str = "") -> PhotoJob:
    ensure_dirs()
    source_path = Path(source_path)
    source_name = source_path.stem
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    job_id = f"{stamp}_{source_name}"

    original_target = ORIGINAL_DIR / f"{job_id}.jpg"
    if source_path.resolve() != original_target.resolve():
        original_target.write_bytes(source_path.read_bytes())

    original = _safe_open(original_target)
    suggested_caption, hashtags = _caption_from_name(source_name)
    if caption.strip():
        suggested_caption = caption.strip()

    square = _crop_cover(original, (1080, 1080))
    feed = _crop_cover(original, (1080, 1350))
    story = _crop_cover(original, (1080, 1920))
    story = story.filter(ImageFilter.SMOOTH_MORE)

    square_path = EDIT_DIR / f"{job_id}_square.jpg"
    feed_path = EDIT_DIR / f"{job_id}_feed.jpg"
    story_path = EDIT_DIR / f"{job_id}_story.jpg"
    preview_path = PREVIEW_DIR / f"{job_id}_preview.jpg"
    ready_path = READY_DIR / f"{job_id}_ready.jpg"
    meta_path = META_DIR / f"{job_id}.json"

    square.save(square_path, quality=92, optimize=True)
    feed.save(feed_path, quality=92, optimize=True)
    story.save(story_path, quality=92, optimize=True)

    preview = _build_contact_sheet(original, {"square": square, "feed": feed, "story": story}, suggested_caption)
    preview.save(preview_path, quality=88, optimize=True)
    feed.save(ready_path, quality=92, optimize=True)

    job = PhotoJob(
        job_id=job_id,
        source=str(original_target),
        caption=caption,
        created_at=datetime.utcnow().isoformat() + "Z",
        artifacts=[
            PhotoArtifact("original", str(original_target)),
            PhotoArtifact("square", str(square_path)),
            PhotoArtifact("feed", str(feed_path)),
            PhotoArtifact("story", str(story_path)),
            PhotoArtifact("preview", str(preview_path)),
            PhotoArtifact("ready", str(ready_path)),
        ],
        suggested_caption=suggested_caption,
        hashtags=hashtags,
        status="ready_for_review",
    )

    meta_path.write_text(
        json.dumps(asdict(job), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return job


def list_jobs() -> List[Path]:
    ensure_dirs()
    return sorted(META_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

