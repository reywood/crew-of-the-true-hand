#!/usr/bin/env python3
"""Generate style-locked character reference images for the four PCs.

Gemini supports up to 14 character-consistency reference images per
generation. This script turns each PC's real portrait (characters/*.jpeg)
into TWO clean, single-character reference plates rendered in the session
art style — a full-figure sheet and a head-and-shoulders portrait — and
saves them under characters/references/. Future session-image runs feed
these back in so characters stop drifting (e.g. Fiz sprouting a beard).

Usage:
    python3 scripts/generate-character-references.py            # all 4 PCs, both plates
    python3 scripts/generate-character-references.py --only fiz # just Fiz
    python3 scripts/generate-character-references.py --force    # overwrite existing

Needs google-genai and a GEMINI_API_KEY (env var or project-root .env),
same as generate-session-image.py. Run via .venv/bin/python.
"""
import argparse
import os
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai not installed. pip install google-genai",
          file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CHARACTERS_DIR = ROOT / "characters"
REF_DIR = CHARACTERS_DIR / "references"


def load_dotenv(path: Path) -> None:
    """Minimal .env loader (stdlib only). KEY=VALUE per line, # comments."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_dotenv(ROOT / ".env")

# Identity anchors — kept verbatim in sync with generate-session-image.py's
# PC_PORTRAITS. These call out the features the model tends to get wrong
# (Fiz's clean-shaven face, Eno's masculinity, race silhouettes).
PC_ANCHORS = {
    "fiz": (
        "Fiz — a ROCK GNOME (small, about 3.5 feet tall — definitely NOT a "
        "dwarf and NOT a halfling). Male, young-looking (young for a gnome). "
        "HAIR: WHITE / SILVER-GRAY, spiky and messy, standing up wildly. "
        "FACE: CLEAN-SHAVEN — a smooth, bare, beardless face; NO BEARD, NO "
        "STUBBLE, NO MOUSTACHE, NO sideburns, EVER. His cheeks, chin and jaw "
        "are smooth bare skin. Bright BLUE eyes, pale skin, a small "
        "mischievous grin. Large pointed gnomish ears. GEAR: brass steampunk "
        "tinker's goggles with dark lenses pushed up on his forehead; brass-"
        "fitted wand-arquebus (a stubby wand-sized cannon) in hand with a "
        "faint blue glow; a small floating drone-cannon accompanies him. "
        "Wears dark brown leather armor with brass plating, fingerless brass-"
        "studded gloves, and a utility belt with pouches and small colored "
        "potion vials. Overall look: an inventor, not a warrior. Steampunk "
        "brass-and-leather aesthetic."
    ),
    "hal": (
        "Hal — a Variant Human paladin (Oath of Vengeance). Male, mid-40s, "
        "tall and broad-shouldered. HAIR: COMPLETELY BALD on top, no hair. "
        "BEARD: a full, thick DARK BROWN beard, chin-length. Serious, grim "
        "expression, brown eyes. Weathered pale skin. GEAR: dull silver-grey "
        "plate armor with a visible breastplate; a deep crimson RED CLOAK "
        "fastened at the neck with a round metal clasp. Carries a sword and "
        "shield or a maul. Ex-Silver Marches militia bearing — steady and "
        "disciplined. He is the ONLY human in the party, the tallest of the "
        "four."
    ),
    "toz": (
        "Toz — a LIGHTFOOT HALFLING (small, about 3 feet tall, halfling "
        "proportions). Male, warm ruddy-tan skin, mid-60s (middle-aged for a "
        "halfling but doesn't look old). HAIR: TOUSLED CURLY DARK BROWN hair "
        "peeking out from under his hat. FACE: clean-shaven, wide cheerful "
        "GRIN, a slightly upturned nose. GEAR: wears a DARK BLUE NAVAL "
        "TRICORN HAT and a matching dark blue naval captain's coat with brass "
        "buttons; a RED NECKERCHIEF or bandana tied at his neck. Ship's "
        "captain of the wrecked True Hand. Casts wind and water magic — a "
        "swirling grey whirlwind and streams of blue water at his fingertips. "
        "Pirate-captain aesthetic."
    ),
    "eno": (
        "Eno — a HALF-ELF nature cleric of Eldath (goddess of still waters). "
        "MALE, mid-50s, wild-raised. Pointed elven ear-tips clearly visible. "
        "HAIR: medium-length wavy MEDIUM BROWN hair. FACE: LIGHT SHORT "
        "STUBBLE (not a full beard, not clean-shaven — just several days' "
        "growth). Blue-gray eyes, weathered tanned skin, quiet serious "
        "expression. NEVER draw him as feminine, delicate, or a woman — he is "
        "a rugged, broad-shouldered man. GEAR: dark green wool cloak with a "
        "small round metal clasp at the throat; simple green-and-brown "
        "druidic robes over leather beneath; wooden holy symbol shaped like a "
        "calm pond; wooden staff. Looks like someone who has spent decades "
        "outdoors — a broad-shouldered woodsman in monk's robes."
    ),
}

# The house art style, reused so references match session illustrations.
STYLE = """STYLE (critical — match this exactly): pen-and-ink drawing with a \
LIGHT WATERCOLOR WASH over it. Loose crosshatch linework doing most of the \
work; watercolor tints (umber, sepia, burnished gold, muted teal, dusty rose) \
applied thinly, letting paper texture show through. NOT a polished full-color \
fantasy painting, NOT a video-game render, NOT thick opaque paint. Think a \
mid-20th-century illustrated storybook or a Victorian traveler's sketchbook."""

# Two reference plates per character. Each is a SINGLE figure on a plain
# parchment ground — no scenery, no other characters, no text — so the plate
# reads purely as a character-consistency anchor.
PLATES = {
    1: (
        "2:3",
        "A full-length CHARACTER REFERENCE PLATE of ONE single figure, "
        "standing in a relaxed, neutral three-quarter pose facing the viewer, "
        "the whole body visible from head to boots. Plain, empty parchment-"
        "toned background — NO scenery, NO landscape, NO other characters. "
        "Render every signature feature and piece of gear from the identity "
        "anchor clearly and correctly.",
    ),
    2: (
        "1:1",
        "A HEAD-AND-SHOULDERS PORTRAIT REFERENCE PLATE of the SAME single "
        "character, facing the viewer against a plain parchment-toned "
        "background — NO scenery, NO other characters. Emphasize the face and "
        "head with total clarity: hair shape and color, ear shape, eyes, "
        "expression, and — critically — the exact state of the facial hair "
        "described in the anchor (a clean-shaven man must have a visibly "
        "smooth bare face; a bearded man a full beard).",
    ),
}


def build_contents(slug: str, anchor: str, plate_prompt: str) -> list:
    portrait = CHARACTERS_DIR / f"{slug}.jpeg"
    parts = []
    if portrait.exists():
        parts.append(types.Part.from_bytes(
            data=portrait.read_bytes(), mime_type="image/jpeg"))
        parts.append(
            "The attached photo is the canonical portrait of this character. "
            "Preserve their identity — face, colouring, build, and gear — but "
            "re-draw them in the illustration style described below.")
    else:
        print(f"  WARN: portrait missing at {portrait}", file=sys.stderr)
    parts.append(STYLE)
    parts.append(
        "Draw ONLY this one character. Do NOT add labels, captions, text, "
        "letters, numbers, borders, or any second figure.")
    parts.append("IDENTITY ANCHOR (get every detail right):\n\n" + anchor)
    parts.append("THIS PLATE:\n\n" + plate_prompt)
    return parts


def extract_image(response) -> bytes:
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                return inline.data
    # Surface any text the model returned instead of an image.
    bits = []
    for candidate in getattr(response, "candidates", []) or []:
        for part in getattr(getattr(candidate, "content", None), "parts", []) or []:
            if getattr(part, "text", None):
                bits.append(part.text)
    raise RuntimeError("no image in response" +
                       (":\n" + "\n".join(bits) if bits else ""))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Only this PC slug (fiz/hal/toz/eno)")
    parser.add_argument("--plate", type=int, choices=(1, 2),
                        help="Only this plate number (1=full figure, 2=portrait)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing reference images")
    parser.add_argument("--model", default="gemini-3.1-flash-image")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set (env var or .env).", file=sys.stderr)
        return 2

    slugs = [args.only] if args.only else list(PC_ANCHORS)
    for s in slugs:
        if s not in PC_ANCHORS:
            print(f"ERROR: unknown PC slug '{s}'", file=sys.stderr)
            return 2
    plates = [args.plate] if args.plate else sorted(PLATES)

    REF_DIR.mkdir(parents=True, exist_ok=True)
    client = genai.Client(api_key=api_key)

    failures = 0
    for slug in slugs:
        for n in plates:
            out = REF_DIR / f"{slug}-ref-{n}.jpg"
            if out.exists() and not args.force:
                print(f"  skip: {out.name} exists (--force to regenerate)")
                continue
            aspect, plate_prompt = PLATES[n]
            print(f"  {slug} plate {n}: calling {args.model} ({aspect})…")
            try:
                resp = client.models.generate_content(
                    model=args.model,
                    contents=build_contents(slug, PC_ANCHORS[slug], plate_prompt),
                    config=types.GenerateContentConfig(
                        image_config=types.ImageConfig(aspect_ratio=aspect),
                    ),
                )
                out.write_bytes(extract_image(resp))
                print(f"  wrote {out.relative_to(ROOT)} "
                      f"({out.stat().st_size/1024:.0f} KB)")
            except Exception as e:  # noqa: BLE001 — report and continue
                print(f"  ERROR {slug} plate {n}: {e}", file=sys.stderr)
                failures += 1
    if failures:
        print(f"done with {failures} failure(s).", file=sys.stderr)
        return 1
    print("done. references in characters/references/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
