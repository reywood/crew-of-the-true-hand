#!/usr/bin/env python3
"""
Generate the podcast cover image for the "Tales of the True Hand" feed.

Uses Google's Gemini 2.5 Flash Image ("Nano Banana"), conditioned on the four
PC portraits so the party is recognizable on the cover. Produces a 1:1 square
suitable for podcast directories (Apple wants 1400x1400 minimum, 3000x3000
recommended; Gemini's aspect_ratio param handles orientation, and the model's
default output resolution is >=1400 on the long edge).

Requirements:
    pip install google-genai
    GEMINI_API_KEY — env var or .env file at project root.

Usage:
    python3 scripts/generate-podcast-cover.py           # skip if exists
    python3 scripts/generate-podcast-cover.py --force   # overwrite

Output: summaries/podcast-cover.jpg
The website generator copies this into site/images/podcast-cover.jpg on the
next build, where the feed.xml <itunes:image> element already points.
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai not installed.", file=sys.stderr)
    print("       pip install google-genai", file=sys.stderr)
    sys.exit(2)


ROOT = Path(__file__).resolve().parent.parent
SUMMARIES_DIR = ROOT / "summaries"
CHARACTERS_DIR = ROOT / "characters"
OUTPUT = SUMMARIES_DIR / "podcast-cover.jpg"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv(ROOT / ".env")


# Same identity anchors used by the session-image generator. Trimmed to the
# lines that keep the model from drifting on race, sex, gear silhouette.
PC_PORTRAITS = [
    (
        "fiz",
        "Fiz — a ROCK GNOME (small, ~3.5 feet tall — NOT a dwarf, NOT a "
        "halfling). Male. HAIR: WHITE / SILVER-GRAY, spiky and messy. "
        "FACE: CLEAN-SHAVEN — no beard, no stubble, no mustache. "
        "Brass tinker's goggles pushed up on his forehead; brass-fitted "
        "wand-arquebus in hand with a faint blue glow; brown leather armor "
        "with brass plating.",
    ),
    (
        "hal",
        "Hal — a Variant Human paladin. Male, mid-40s. HAIR: COMPLETELY "
        "BALD. BEARD: full thick DARK BROWN beard, chin-length. Grim. "
        "Silver-grey plate armor; deep crimson RED CLOAK. He is the ONLY "
        "human and the tallest of the four.",
    ),
    (
        "toz",
        "Toz — a LIGHTFOOT HALFLING (small, ~3 feet tall). Male. HAIR: "
        "curly DARK BROWN. Clean-shaven, cheerful grin. Wears a DARK BLUE "
        "NAVAL TRICORN HAT and matching captain's coat with brass buttons; "
        "RED NECKERCHIEF. Casts wind and water magic.",
    ),
    (
        "woz",
        "Woz — a HALF-ELF nature cleric of Eldath. MALE (never draw as "
        "feminine), mid-50s. Pointed elven ear-tips. HAIR: medium wavy "
        "MEDIUM BROWN. LIGHT SHORT STUBBLE (not a full beard). Dark green "
        "wool cloak; wooden staff; a broad-shouldered woodsman in monk's "
        "robes.",
    ),
]


COVER_PROMPT = """You are illustrating the podcast cover art for a Dungeons & \
Dragons audio recap series called "TALES OF THE TRUE HAND". The cover will be \
displayed at small sizes (as tiny as 55x55 pixels in a podcast grid) as well \
as large (1400x1400+). Design accordingly: bold silhouettes, strong central \
subject, minimal small detail near the edges.

FORMAT: SQUARE — 1:1 aspect ratio. This is podcast cover art, not a landscape \
scene. Fill the whole square.

STYLE: Pen-and-ink drawing with a warm watercolor wash. Loose crosshatch \
linework; watercolor tints in umber, sepia, burnished gold, and muted teal, \
applied thinly with paper texture showing through. Mid-20th-century \
illustrated storybook / Victorian traveler's sketchbook — NOT a polished 3D \
fantasy render, NOT a video-game cover, NOT thick opaque paint. Warm, \
inviting, hearth-lit.

COMPOSITION: A hearth-side storyteller vignette. In the FOREGROUND, silhouetted \
against a warm firelit hearth, the four heroes of the party sit or stand \
gathered close, seen from behind or in three-quarter view — they are the \
listeners around the fire, and their four silhouettes are the primary shape. \
Above and behind them, the composition opens into a stormy sky of a fantasy \
North: distant flying tower, a hint of giant silhouettes at the horizon, \
lightning webbing through cloud. A weathered wooden ship's wheel or the \
splintered ribs of a shipwreck may appear as a background/framing element on \
one side.

CHARACTERS: The four portrait references (Fiz, Hal, Toz, Woz) are provided so \
you can tell them apart. All four should appear in the foreground silhouettes, \
readable by outline: Hal tallest (bald, bearded, cloaked human); Fiz smallest \
and gnomish with spiky pale hair and goggles; Toz halfling with tricorn hat; \
Woz half-elf with hooded green cloak and staff. Read the identity anchors — \
Fiz is NOT a dwarf, Woz is NOT feminine.

TEXT: Include the title 'TALES OF THE TRUE HAND' rendered as prominent \
illuminated-manuscript display lettering across the top or the upper third of \
the square, in a gilt / burnished-gold Cinzel-like serif. It should be legible \
at thumbnail sizes. Do NOT include any other text, subtitle, byline, or \
tagline. NO episode numbers, NO dates. Only the show title."""


def _portrait_parts():
    parts = []
    for slug, description in PC_PORTRAITS:
        portrait = CHARACTERS_DIR / f"{slug}.jpeg"
        if not portrait.exists():
            print(f"WARN: portrait missing at {portrait}", file=sys.stderr)
            continue
        parts.append(types.Part.from_bytes(
            data=portrait.read_bytes(), mime_type="image/jpeg"))
        parts.append(f"Reference portrait ({slug}): {description}")
    return parts


def extract_image(response):
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                return inline.data
    raise RuntimeError("no image found in Gemini response")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true",
                        help="Overwrite the existing cover.")
    parser.add_argument("--model", default="gemini-2.5-flash-image",
                        help="Gemini image model id.")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY env var not set.", file=sys.stderr)
        sys.exit(2)

    if OUTPUT.exists() and not args.force:
        print(f"skip: {OUTPUT} already exists (--force to regenerate)")
        return 0

    client = genai.Client(api_key=api_key)
    contents = _portrait_parts() + [COVER_PROMPT]
    print(f"calling {args.model}…")
    response = client.models.generate_content(
        model=args.model,
        contents=contents,
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(aspect_ratio="1:1"),
        ),
    )
    try:
        image_bytes = extract_image(response)
    except RuntimeError as e:
        for candidate in getattr(response, "candidates", []) or []:
            for part in getattr(candidate.content, "parts", []) or []:
                if getattr(part, "text", None):
                    print("model text response:", part.text, file=sys.stderr)
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # Normalize to a real 1400x1400 JPEG. Gemini returns 1024 PNG regardless
    # of extension; Apple Podcasts requires >=1400px square JPEG or PNG in RGB.
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        if im.size != (1400, 1400):
            im = im.resize((1400, 1400), Image.LANCZOS)
        im.save(OUTPUT, "JPEG", quality=88, optimize=True)
        final_size = OUTPUT.stat().st_size
        print(f"wrote {OUTPUT} ({final_size / 1024:.0f} KB, 1400x1400 JPEG)")
    except ImportError:
        OUTPUT.write_bytes(image_bytes)
        print(f"wrote {OUTPUT} ({len(image_bytes) / 1024:.0f} KB, RAW — "
              f"install Pillow to normalize to 1400x1400 JPEG)")
    print("Next: python3 website/generate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
