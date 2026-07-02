#!/usr/bin/env python3
"""
Generate a hero illustration for a session using Google's Gemini 2.5 Flash
Image ("Nano Banana"), conditioned on the four PC portraits so characters
stay recognizable across sessions.

Requirements:
    pip install google-genai
    GEMINI_API_KEY — provide it either as an exported environment variable
    or via a .env file at the project root (KEY=VALUE, one per line). The .env
    file is git-ignored. Get a key at https://aistudio.google.com/apikey.

Usage:
    python3 scripts/generate-session-image.py 2026-06-16
    python3 scripts/generate-session-image.py 2026-06-16 --force  # overwrite

    # regenerate all sessions that don't yet have an image:
    for d in summaries/*.md; do
        date=$(basename "$d" .md)
        python3 scripts/generate-session-image.py "$date"
    done

Output: summaries/images/YYYY-MM-DD.jpg
The website generator (website/generate.py) automatically embeds any image
it finds under summaries/images/ as a hero at the top of that session's
detail page.
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
IMAGES_DIR = SUMMARIES_DIR / "images"
CHARACTERS_DIR = ROOT / "characters"


def load_dotenv(path: Path) -> None:
    """Minimal .env loader (stdlib only). KEY=VALUE per line, # comments
    allowed, quotes around the value stripped. Existing env vars win."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # Don't clobber values already set in the real environment.
        os.environ.setdefault(key, value)


load_dotenv(ROOT / ".env")


# Portrait references. Each portrait is paired with an identity anchor
# transcribed from the actual portrait image (characters/*.jpeg). These call
# out the specific features the model tends to get wrong on the first pass —
# hair color, facial hair (or lack of), race silhouette, signature gear.
PC_PORTRAITS = [
    (
        "fiz",
        "Fiz — a ROCK GNOME (small, about 3.5 feet tall — definitely NOT a "
        "dwarf and NOT a halfling). Male, young-looking (young for a gnome). "
        "HAIR: WHITE / SILVER-GRAY, spiky and messy, standing up wildly. "
        "FACE: CLEAN-SHAVEN — NO BEARD, NO STUBBLE, NO MUSTACHE, EVER. "
        "Bright BLUE eyes, pale skin, a small mischievous grin. Large "
        "pointed gnomish ears. GEAR: brass steampunk tinker's goggles with "
        "dark lenses pushed up on his forehead; brass-fitted wand-arquebus "
        "(a stubby wand-sized cannon) in hand with a faint blue glow; a "
        "small floating drone-cannon accompanies him. Wears dark brown "
        "leather armor with brass plating, fingerless brass-studded gloves, "
        "and a utility belt with pouches and small colored potion vials. "
        "Overall look: an inventor, not a warrior. Steampunk brass-and-"
        "leather aesthetic.",
    ),
    (
        "hal",
        "Hal — a Variant Human paladin (Oath of Vengeance). Male, mid-40s, "
        "tall and broad-shouldered. HAIR: COMPLETELY BALD on top, no hair. "
        "BEARD: a full, thick DARK BROWN beard, chin-length. Serious, grim "
        "expression, brown eyes. Weathered pale skin. GEAR: dull silver-"
        "grey plate armor with a visible breastplate; a deep crimson RED "
        "CLOAK fastened at the neck with a round metal clasp. Carries a "
        "sword and shield or a maul. Ex-Silver Marches militia bearing — "
        "steady and disciplined. He is the ONLY human in the party, the "
        "tallest of the four.",
    ),
    (
        "toz",
        "Toz — a LIGHTFOOT HALFLING (small, about 3 feet tall, halfling "
        "proportions). Male, warm ruddy-tan skin, mid-60s (middle-aged for "
        "a halfling but doesn't look old). HAIR: TOUSLED CURLY DARK BROWN "
        "hair peeking out from under his hat. FACE: clean-shaven, wide "
        "cheerful GRIN, a slightly upturned nose. GEAR: wears a DARK BLUE "
        "NAVAL TRICORN HAT and a matching dark blue naval captain's coat "
        "with brass buttons; a RED NECKERCHIEF or bandana tied at his neck. "
        "Ship's captain of the wrecked *True Hand*. Casts wind and water "
        "magic — a swirling grey whirlwind and streams of blue water at his "
        "fingertips. Pirate-captain aesthetic.",
    ),
    (
        "woz",
        "Woz — a HALF-ELF nature cleric of Eldath (goddess of still "
        "waters). MALE, mid-50s, wild-raised. Pointed elven ear-tips "
        "clearly visible. HAIR: medium-length wavy MEDIUM BROWN hair. "
        "FACE: LIGHT SHORT STUBBLE (not a full beard, not clean-shaven — "
        "just several days' growth). Blue-gray eyes, weathered tanned "
        "skin, quiet serious expression. NEVER draw him as feminine, "
        "delicate, or a woman. GEAR: dark green wool cloak with a small "
        "round metal clasp at the throat; simple green-and-brown druidic "
        "robes over leather beneath; wooden holy symbol shaped like a "
        "calm pond; wooden staff. Looks like someone who has spent "
        "decades outdoors — a broad-shouldered woodsman in monk's robes.",
    ),
]


STYLE_INSTRUCTIONS = """You are illustrating a scene from a Dungeons & Dragons \
campaign recap that will sit on a parchment-toned website page.

STYLE (critical — this is the number-one thing to get right):
Pen-and-ink drawing with a LIGHT WATERCOLOR WASH over it. Loose crosshatch \
linework doing most of the work; watercolor tints (umber, sepia, burnished \
gold, muted teal, dusty rose) applied thinly, letting paper texture show \
through. NOT a polished full-color fantasy painting. NOT a video-game cover. \
NOT thick opaque paint. Think mid-20th-century illustrated storybook or a \
Victorian traveler's sketchbook — an evocative moment captured with restraint. \
Leave real negative space: parts of the image should be sparser, not \
crammed with detail from edge to edge.

COMPOSITION:
The image MUST be LANDSCAPE ORIENTATION, roughly 2:1 aspect ratio (much wider \
than it is tall — think of a book spread, not a square panel). Frame ONE \
evocative moment — the pivotal beat of the scene, not an action-pose lineup \
of every character present.

CHARACTERS:
The four portrait references (Fiz, Hal, Toz, Woz) are provided so you can \
tell the PCs apart. Include ONLY the PCs actually named in the pivotal moment \
below. Read each identity anchor carefully — the model has a habit of drifting \
Fiz into a dwarf or bald tinker and drifting Woz feminine. Both are wrong. \
Preserve race, size, sex, and costume from the identity anchors. Do NOT \
label them, do NOT add speech bubbles, do NOT add any text, letters, numbers, \
or captions anywhere in the image."""


def load_summary(date: str) -> str:
    path = SUMMARIES_DIR / f"{date}.md"
    if not path.exists():
        print(f"ERROR: {path} does not exist.", file=sys.stderr)
        print("       Generate the summary first (see CLAUDE.md workflow).",
              file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def extract_pivotal_moment(summary: str) -> str:
    """Pull the '*In brief: ...*' one-liner from the summary. This is the
    campaign author's own compressed statement of what the session was about,
    and it's a much better prompt anchor than the whole prose recap."""
    for line in summary.splitlines():
        s = line.strip()
        if s.startswith("*In brief:") and s.endswith("*"):
            return s[len("*In brief:"):-1].strip()
    return ""


def build_contents(summary: str) -> list:
    """Multimodal input: portraits + text, in the order the model reads best."""
    contents = []
    for slug, description in PC_PORTRAITS:
        portrait = CHARACTERS_DIR / f"{slug}.jpeg"
        if not portrait.exists():
            print(f"WARN: portrait missing at {portrait}", file=sys.stderr)
            continue
        contents.append(
            types.Part.from_bytes(
                data=portrait.read_bytes(), mime_type="image/jpeg"
            )
        )
        contents.append(f"Reference portrait ({slug}): {description}")

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
    return contents


def extract_image(response) -> bytes:
    """Pull the first inline_data image bytes out of a Gemini response."""
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
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else "",
    )
    parser.add_argument("date", help="Session date, YYYY-MM-DD")
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite an existing image for this date.",
    )
    parser.add_argument(
        "--model", default="gemini-2.5-flash-image",
        help="Gemini image model id (default: gemini-2.5-flash-image).",
    )
    parser.add_argument(
        "--aspect", default="16:9",
        help='Aspect ratio, e.g. "16:9", "3:2", "4:3", "1:1" (default: 16:9).',
    )
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY env var not set.", file=sys.stderr)
        print("       Get one at https://aistudio.google.com/apikey",
              file=sys.stderr)
        sys.exit(2)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    output = IMAGES_DIR / f"{args.date}.jpg"
    if output.exists() and not args.force:
        print(f"{output} already exists — use --force to regenerate.")
        return 0

    summary = load_summary(args.date)
    contents = build_contents(summary)

    print(f"Calling {args.model} for {args.date}…")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=args.model,
        contents=contents,
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(aspect_ratio=args.aspect),
        ),
    )

    try:
        image_bytes = extract_image(response)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        # Dump any text the model returned instead of an image, for debug.
        text_bits = []
        for candidate in getattr(response, "candidates", []) or []:
            for part in getattr(candidate.content, "parts", []) or []:
                if getattr(part, "text", None):
                    text_bits.append(part.text)
        if text_bits:
            print("Model text response:", file=sys.stderr)
            print("\n".join(text_bits), file=sys.stderr)
        sys.exit(1)

    output.write_bytes(image_bytes)
    print(f"Wrote {output} ({len(image_bytes) / 1024:.0f} KB)")
    print("Next: python3 website/generate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
