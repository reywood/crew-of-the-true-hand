"""Generating the per-PC reference plates the session-image pipeline feeds back in.

Was scripts/generate-character-references.py. Writes
``characters/references/<slug>-ref-<n>.jpg``, which
``pipelines/session_image.py`` globs when assembling a scene prompt.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..adapters.images import DEFAULT_IMAGE_MODEL, ImageBackend
from ..content.art_style import PLATES, REFERENCE_PLATE_STYLE
from ..content.pc_identity import PC_ANCHORS, PC_SLUGS

PORTRAIT_PREAMBLE = (
    "The attached photo is the canonical portrait of this character. "
    "Preserve their identity — face, colouring, build, and gear — but "
    "re-draw them in the illustration style described below."
)
SINGLE_FIGURE_RULE = (
    "Draw ONLY this one character. Do NOT add labels, captions, text, "
    "letters, numbers, borders, or any second figure."
)


@dataclass
class PlateResult:
    slug: str
    plate: int
    path: object
    status: str  # "written" | "skipped" | "failed"
    detail: str = ""


def build_contents(backend: ImageBackend, paths, slug: str, anchor: str,
                   plate_prompt: str) -> list:
    """Assemble the prompt parts for one reference plate."""
    parts: list = []
    portrait = paths.characters / f"{slug}.jpeg"
    if portrait.exists():
        parts.append(backend.part_from_bytes(portrait.read_bytes(), "image/jpeg"))
        parts.append(PORTRAIT_PREAMBLE)
    parts.append(REFERENCE_PLATE_STYLE)
    parts.append(SINGLE_FIGURE_RULE)
    parts.append("IDENTITY ANCHOR (get every detail right):\n\n" + anchor)
    parts.append("THIS PLATE:\n\n" + plate_prompt)
    return parts


def generate(paths, backend: ImageBackend, *, only: str | None = None,
             plate: int | None = None, force: bool = False,
             model: str = DEFAULT_IMAGE_MODEL) -> list[PlateResult]:
    """Render reference plates. One failure does not abort the rest."""
    slugs = [only] if only else list(PC_SLUGS)
    numbers = [plate] if plate else sorted(PLATES)
    out_dir = paths.character_references
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[PlateResult] = []
    for slug in slugs:
        anchor = PC_ANCHORS[slug]
        for n in numbers:
            dest = out_dir / f"{slug}-ref-{n}.jpg"
            if dest.exists() and not force:
                results.append(PlateResult(slug, n, dest, "skipped",
                                           "already exists (--force to regenerate)"))
                continue
            aspect, plate_prompt = PLATES[n]
            try:
                data = backend.generate(
                    build_contents(backend, paths, slug, anchor, plate_prompt),
                    model=model, aspect=aspect,
                )
                dest.write_bytes(data)
                results.append(PlateResult(slug, n, dest, "written",
                                           f"{len(data) / 1024:.0f} KB"))
            except Exception as exc:  # noqa: BLE001 — report and keep going
                results.append(PlateResult(slug, n, dest, "failed", str(exc)))
    return results
