"""Local image normalization (Pillow).

Pillow stays *softly* optional, matching the behaviour of the podcast-cover
script: without it the raw model bytes are written and the caller is told to
install it. That is deliberate — a slightly-wrong cover beats no cover.
"""

from __future__ import annotations

import io
from pathlib import Path

#: Apple Podcasts wants a square JPEG of at least 1400px in RGB. Gemini
#: returns a 1024px PNG regardless of the requested extension.
COVER_SIZE = (1400, 1400)
JPEG_QUALITY = 88


def normalize_square_jpeg(data: bytes, dest: Path,
                          size: tuple[int, int] = COVER_SIZE) -> str:
    """Write *data* to *dest* as a square RGB JPEG. Returns a status note.

    Falls back to writing the bytes unchanged if Pillow is not installed.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image
    except ImportError:
        dest.write_bytes(data)
        return (f"{len(data) / 1024:.0f} KB, RAW — install Pillow "
                f"(pip install -e 'toolkit[image]') to normalize to "
                f"{size[0]}x{size[1]} JPEG")

    im = Image.open(io.BytesIO(data)).convert("RGB")
    if im.size != size:
        im = im.resize(size, Image.LANCZOS)
    im.save(dest, "JPEG", quality=JPEG_QUALITY, optimize=True)
    return f"{dest.stat().st_size / 1024:.0f} KB, {size[0]}x{size[1]} JPEG"
