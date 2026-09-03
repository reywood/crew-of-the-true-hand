"""Session hero + beat illustrations.

Was scripts/generate-session-image.py. Reads the session summary, pulls the
``*In brief:*`` line as the pivotal moment for the hero image and each ``##``
section as a beat, and renders them through an injected ImageBackend.

The site generator picks up whatever it finds in sessions/<date>/images/ — no
per-session change needed there.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..adapters.images import DEFAULT_IMAGE_MODEL, ImageBackend
from ..content.art_style import STYLE_INSTRUCTIONS
from ..content.pc_identity import (
    CAST_ROLLCALL,
    LEAN_CAST,
    MAX_REFS_PER_PC,
    PC_ANCHORS,
    PC_SLUGS,
    REFERENCE_USAGE,
)
from ..core.text import slugify
from ..errors import UserError

HERO_ASPECT = "16:9"
BEAT_ASPECT = "3:2"


@dataclass
class ImageResult:
    label: str
    path: object
    status: str  # "written" | "skipped" | "failed"
    detail: str = ""


def load_summary(paths, date: str) -> str:
    path = paths.session_summary(date)
    if not path.exists():
        raise UserError(
            f"{path} does not exist.\n"
            f"  Generate the session summary first (see CLAUDE.md workflow)."
        )
    return path.read_text(encoding="utf-8")


# Section titles to skip when generating beat images. These sections tend to be
# bullet lists of leads and status, not story beats worth illustrating.
BEAT_SKIP_TITLES = {
    "what's next", "whats next", "loose ends", "next steps",
    "up next", "next", "leads", "loose threads",
}


def extract_beats(summary: str) -> list:
    """Return a list of (title, slug, body_text) for each ## section in the
    summary that is worth illustrating (i.e. not a "What's next" style list).
    Order preserves document order."""
    beats = []
    current_title = None
    current_body = []

    def maybe_flush():
        if current_title is None:
            return
        title_l = current_title.strip().lower()
        if title_l in BEAT_SKIP_TITLES:
            return
        body = "\n".join(current_body).strip()
        if not body:
            return
        # Skip sections whose body is entirely bullets — probably a list of
        # leads, not a story beat.
        non_bullet = [
            ln for ln in body.splitlines()
            if ln.strip() and not ln.strip().startswith(("-", "*"))
        ]
        if not non_bullet:
            return
        beats.append((current_title.strip(), slugify(current_title), body))

    for raw in summary.splitlines():
        m = re.match(r"^\s*##\s+(.*)$", raw)
        if m:
            maybe_flush()
            current_title = m.group(1).strip()
            current_body = []
        elif current_title is not None:
            current_body.append(raw)
    maybe_flush()
    return beats


def extract_pivotal_moment(summary: str) -> str:
    """Pull the '*In brief: ...*' one-liner from the summary. This is the
    campaign author's own compressed statement of what the session was about,
    and it's a much better prompt anchor than the whole prose recap."""
    for line in summary.splitlines():
        s = line.strip()
        if s.startswith("*In brief:") and s.endswith("*"):
            return s[len("*In brief:"):-1].strip()
    return ""


def _portrait_parts(backend, paths, refs_only: bool = False,
                    full_text: bool = False) -> list:
    """The shared PC-reference block appended to every generation.

    Three modes (the reference plates are fed in all three):

    - full_text=True (the DEFAULT, via --model's 3.x tier): plates + portrait
      + the full PC_PORTRAITS feature anchor + roll-call. Best identity and
      completeness; the 3.x models follow it without the drift that plagued
      gemini-2.5-flash-image.
    - lean (full_text=False, --lean): plates + portrait + a lean cast line
      (name, gear, role — NO feature prose) + roll-call. Experimental; on weak
      models it let identity drift (Hal losing his baldness).
    - refs_only=True: plates + a bare name label only — no cast text, no
      photo. Purest images-only control; can drop PCs (no roll-call).

    Image count stays within Gemini's 14-reference cap: 4 PCs x
    (MAX_REFS_PER_PC + 1 portrait)."""
    parts = []
    warnings: list[str] = []
    any_refs = any(paths.character_references.glob("*-ref-*.jpg"))
    if any_refs:
        parts.append(REFERENCE_USAGE)
    for slug in PC_SLUGS:
        description = PC_ANCHORS[slug]
        refs = sorted(paths.character_references.glob(f"{slug}-ref-*.jpg"))[:MAX_REFS_PER_PC]
        for ref in refs:
            parts.append(backend.part_from_bytes(ref.read_bytes(), "image/jpeg"))

        if refs_only:
            # Images-only mode: plates + a bare NAME label (no cast text, no
            # photo) so the model can still map images -> the PCs named in the
            # summary without any prose that could bias features.
            if refs:
                parts.append(
                    f"The {len(refs)} image(s) immediately above are the "
                    f"identity reference plates for the player character named "
                    f"{slug}. If {slug} is in this scene, keep their identity "
                    f"(face, hair, colouring, costume, gear) matching these "
                    f"plates — but draw them in a FRESH pose and action for "
                    f"the scene; do not copy the plate's pose or background.")
            else:
                warnings.append(f"no references for {slug} (refs-only)")
            continue

        portrait = paths.characters / f"{slug}.jpeg"
        has_portrait = portrait.exists()
        if has_portrait:
            parts.append(backend.part_from_bytes(portrait.read_bytes(), "image/jpeg"))
        if not refs and not has_portrait:
            warnings.append(f"no references or portrait for {slug}")
            continue

        # Text for this PC: lean cast line by default, full anchor with
        # --full-text. Both keep identity to the plates but re-pose freshly.
        cast_text = (description if full_text
                     else LEAN_CAST.get(slug, description))
        anchor_label = ("Identity anchor" if full_text else "Character")
        if refs:
            parts.append(
                f"The image(s) immediately above are the identity reference "
                f"plates for {slug}, drawn in the target art style. Keep this "
                f"character's identity — face, hair, facial hair, build, "
                f"colouring, costume and gear — matching these plates, but "
                f"pose and place them FRESHLY for this scene (do not copy the "
                f"plate's pose, framing, or background)"
                + (", using the photo portrait after them only for likeness. "
                   if has_portrait else ". ")
                + f"{anchor_label} ({slug}): {cast_text}"
            )
        else:
            parts.append(f"{anchor_label} ({slug}): {cast_text}")

    # Roll-call keeps the party complete (lean/full modes only; refs_only is
    # left as a pure control with no cast text).
    if not refs_only:
        parts.append(CAST_ROLLCALL)
    return parts, warnings


def build_contents(backend, paths, summary: str, refs_only: bool = False,
                   full_text: bool = False) -> list:
    """Multimodal input for the HERO image (session-level banner).
    Portraits + style + pivotal moment + full summary."""
    contents, warnings = _portrait_parts(backend, paths, refs_only, full_text)
    contents.append(STYLE_INSTRUCTIONS)

    pivotal = extract_pivotal_moment(summary)
    if pivotal:
        contents.append(
            "PIVOTAL MOMENT TO ILLUSTRATE (this is THE scene — everything "
            "else in the summary below is context for characters, setting, "
            "and props):\n\n"
            + pivotal
        )

    contents.append(
        "Supporting context — the fuller session summary. Use this to know "
        "which characters are in the scene, what the setting looks like, "
        "who else is there, and what props matter. Do NOT try to depict the "
        "whole summary. Illustrate ONLY the pivotal moment above:\n\n"
        + summary
    )
    return contents, warnings


def build_beat_contents(backend, paths, title: str, body: str, summary: str,
                        refs_only: bool = False,
                        full_text: bool = False) -> list:
    """Multimodal input for a BEAT image (one story beat within a session).
    Portraits + style + this beat only, with a smaller-scale directive."""
    contents, warnings = _portrait_parts(backend, paths, refs_only, full_text)
    contents.append(STYLE_INSTRUCTIONS)
    contents.append(
        "This is a SMALLER inline illustration for one beat within a session "
        "recap — not the session's hero banner. Compose intimately: closer to "
        "the characters, one small moment, not a sweeping panorama. Fewer "
        "figures, more focus. Only include PCs actually named in THIS BEAT's "
        "text below."
    )
    contents.append(
        f"BEAT TITLE: {title}\n\n"
        f"BEAT TEXT — illustrate ONLY this moment:\n\n{body}"
    )
    # Give the model the broader summary as background so it knows what came
    # before and after this beat (helps with continuity of costume, setting).
    contents.append(
        "Background context (do NOT depict — for continuity only):\n\n"
        + summary
    )
    return contents, warnings

def _render(backend, dest, contents, aspect, model, label, force):
    if dest.exists() and not force:
        return ImageResult(label, dest, "skipped",
                           "already exists (--force to regenerate)")
    data = backend.generate(contents, model=model, aspect=aspect)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return ImageResult(label, dest, "written", f"{len(data) / 1024:.0f} KB")


def generate(paths, backend: ImageBackend, date: str, *, hero: bool = True,
             beats: bool = True, force: bool = False,
             model: str = DEFAULT_IMAGE_MODEL, hero_aspect: str = HERO_ASPECT,
             beat_aspect: str = BEAT_ASPECT, refs_only: bool = False,
             lean: bool = False) -> tuple[list[ImageResult], list[str]]:
    """Render the hero image and/or one image per beat for *date*."""
    summary = load_summary(paths, date)
    out_dir = paths.session_images(date)
    full_text = not lean
    results: list[ImageResult] = []
    warnings: list[str] = []

    if hero:
        contents, warn = build_contents(backend, paths, summary, refs_only, full_text)
        warnings += warn
        results.append(_render(backend, out_dir / "hero.jpg", contents,
                               hero_aspect, model, "hero", force))

    if beats:
        found = extract_beats(summary)
        if not found:
            warnings.append(f"no illustratable ## sections found in {date}/summary.md")
        for title, slug, body in found:
            contents, warn = build_beat_contents(backend, paths, title, body,
                                                 summary, refs_only, full_text)
            warnings += warn
            results.append(_render(backend, out_dir / f"{slug}.jpg", contents,
                                   beat_aspect, model, f"beat: {title}", force))

    return results, warnings
