"""Generating the 1400x1400 podcast cover.

Was scripts/generate-podcast-cover.py. Writes website/static/podcast-cover.jpg,
which the site's static-asset glob copies to site/static/ and feed.xml points
at via <itunes:image>. Rarely needed — a good cover survives many episodes.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..adapters.images import DEFAULT_IMAGE_MODEL, ImageBackend
from ..adapters.imaging import normalize_square_jpeg
from ..content.art_style import COVER_PROMPT
from ..content.pc_identity import PC_ANCHORS, PC_SLUGS
from ..errors import UserError

COVER_ASPECT = "1:1"
COVER_FILENAME = "podcast-cover.jpg"


@dataclass
class CoverResult:
    path: object
    status: str          # "written" | "skipped"
    detail: str = ""
    missing_portraits: tuple[str, ...] = ()


def build_contents(backend: ImageBackend, paths) -> tuple[list, list[str]]:
    """Prompt parts for the cover, plus the slugs whose portrait was missing."""
    parts: list = []
    missing: list[str] = []
    for slug in PC_SLUGS:
        portrait = paths.characters / f"{slug}.jpeg"
        if not portrait.exists():
            missing.append(slug)
            continue
        parts.append(backend.part_from_bytes(portrait.read_bytes(), "image/jpeg"))
        parts.append(f"Reference portrait ({slug}): {PC_ANCHORS[slug]}")
    parts.append(COVER_PROMPT)
    return parts, missing


def generate(paths, backend: ImageBackend, *, force: bool = False,
             model: str = DEFAULT_IMAGE_MODEL) -> CoverResult:
    dest = paths.static / COVER_FILENAME
    if dest.exists() and not force:
        return CoverResult(dest, "skipped", "already exists (--force to regenerate)")

    contents, missing = build_contents(backend, paths)
    if len(missing) == len(PC_SLUGS):
        raise UserError(f"no PC portraits found under {paths.characters}")

    data = backend.generate(contents, model=model, aspect=COVER_ASPECT)
    detail = normalize_square_jpeg(data, dest)
    return CoverResult(dest, "written", detail, tuple(missing))
