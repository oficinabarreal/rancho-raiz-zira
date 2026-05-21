from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

try:
    from PIL import Image, ImageFilter, ImageOps
except Exception:  # pragma: no cover - optional dependency
    Image = None
    ImageFilter = None
    ImageOps = None


@dataclass
class PhotoVariant:
    name: str
    path: str
    width: int
    height: int


class PhotoPipeline:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.base_dir = self.root / "media"

    def _ensure_dir(self, asset_id: str) -> Path:
        out = self.base_dir / asset_id
        out.mkdir(parents=True, exist_ok=True)
        return out

    def _save(self, image: Image.Image, path: Path, quality: int = 92) -> PhotoVariant:
        image.save(path, format="JPEG", quality=quality, optimize=True)
        return PhotoVariant(name=path.stem, path=str(path), width=image.width, height=image.height)

    def _prepare_image(self, source: Path) -> Image.Image:
        image = Image.open(source)
        image = ImageOps.exif_transpose(image)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        elif image.mode == "L":
            image = image.convert("RGB")
        return image

    def _fit_canvas(self, image: Image.Image, size: tuple[int, int], *, fill: bool = True) -> Image.Image:
        if fill:
            return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)
        return ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)

    def process(self, source_path: str, asset_id: str, caption: str = "") -> Dict[str, Any]:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(source_path)

        asset_dir = self._ensure_dir(asset_id)
        originals = asset_dir / "originals"
        originals.mkdir(parents=True, exist_ok=True)

        source_copy = originals / "original.jpg"
        variants: Dict[str, PhotoVariant] = {}

        if Image is None:
            shutil.copy2(source, source_copy)
            for name in ("square", "feed", "preview", "story", "ready"):
                variant_path = asset_dir / f"{name}.jpg"
                shutil.copy2(source, variant_path)
                variants[name] = PhotoVariant(name=name, path=str(variant_path), width=0, height=0)
            meta = {
                "asset_id": asset_id,
                "source_path": str(source),
                "caption": caption,
                "source_copy": str(source_copy),
                "fallback": True,
                "variants": {name: asdict(variant) for name, variant in variants.items()},
            }
            (asset_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return meta

        image = self._prepare_image(source)
        image.save(source_copy, format="JPEG", quality=95, optimize=True)

        square = self._fit_canvas(image, (1080, 1080), fill=True)
        variants["square"] = self._save(square, asset_dir / "square.jpg")

        feed = self._fit_canvas(image, (1080, 1350), fill=True)
        variants["feed"] = self._save(feed, asset_dir / "feed.jpg")

        preview = self._fit_canvas(image, (720, 720), fill=False)
        variants["preview"] = self._save(preview, asset_dir / "preview.jpg")

        story_bg = self._fit_canvas(image, (1080, 1920), fill=True).filter(ImageFilter.GaussianBlur(radius=14))
        story_fg = self._fit_canvas(image, (960, 1440), fill=False)
        story_canvas = story_bg.copy()
        offset_x = (story_canvas.width - story_fg.width) // 2
        offset_y = (story_canvas.height - story_fg.height) // 2
        story_canvas.paste(story_fg, (offset_x, offset_y))
        variants["story"] = self._save(story_canvas, asset_dir / "story.jpg")

        ready = feed if feed.width >= feed.height else square
        variants["ready"] = self._save(ready, asset_dir / "ready.jpg")

        meta = {
            "asset_id": asset_id,
            "source_path": str(source),
            "caption": caption,
            "source_copy": str(source_copy),
            "variants": {name: asdict(variant) for name, variant in variants.items()},
        }
        (asset_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return meta
