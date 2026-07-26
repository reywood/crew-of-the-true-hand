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
    for d in sessions/*/summary.md; do
        date=$(basename "$(dirname "$d")")
        python3 scripts/generate-session-image.py "$date"
    done

Output: hero → sessions/YYYY-MM-DD/images/hero.jpg
        beats → sessions/YYYY-MM-DD/images/<beat-slug>.jpg
The website generator (website/generate.py) embeds hero.jpg as the banner at
the top of that session's detail page and floats the beat images inline.
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
SESSIONS_DIR = ROOT / "sessions"
CHARACTERS_DIR = ROOT / "characters"
# Style-locked per-PC reference plates (see generate-character-references.py).
# Fed alongside the raw portraits as character-consistency anchors.
REFERENCES_DIR = CHARACTERS_DIR / "references"
# Max reference plates per PC to feed. 4 PCs x (this + 1 portrait) must stay
# under Gemini's 14-image reference limit; 2 -> 12 images, safe.
MAX_REFS_PER_PC = 2


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
        "eno",
        "Eno — a HALF-ELF nature cleric of Eldath (goddess of still "
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
The four portrait references (Fiz, Hal, Toz, Eno) are provided so you can \
tell the PCs apart. Include ONLY the PCs actually named in the pivotal moment \
below. Read each identity anchor carefully — the model has a habit of drifting \
Fiz into a dwarf or bald tinker and drifting Eno feminine. Both are wrong. \
Preserve race, size, sex, and costume from the identity anchors. Do NOT \
label them, do NOT add speech bubbles, do NOT add any text, letters, numbers, \
or captions anywhere in the image."""


import re


def slugify(text: str) -> str:
    """Match the slugify function in website/generate.py so beat image
    filenames line up with what the site generator expects."""
    s = text.replace("'", "").replace("’", "")
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s


# Section titles to skip when generating beat images. These sections tend to be
# bullet lists of leads and status, not story beats worth illustrating.
BEAT_SKIP_TITLES = {
    "what's next", "whats next", "loose ends", "next steps",
    "up next", "next", "leads", "loose threads",
}


def load_summary(date: str) -> str:
    path = SESSIONS_DIR / date / "summary.md"
    if not path.exists():
        print(f"ERROR: {path} does not exist.", file=sys.stderr)
        print("       Generate the summary first (see CLAUDE.md workflow).",
              file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


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


# Prepended before the reference images so the model treats them as IDENTITY
# anchors, not stamps to paste. Without this, Gemini copies a plate's pose,
# framing, and empty background straight into the scene (observed on Toz/Eno).
REFERENCE_USAGE = (
    "HOW TO USE THE CHARACTER REFERENCE IMAGES BELOW — read carefully. They "
    "exist ONLY to keep each character's IDENTITY consistent between "
    "illustrations: their face, hair, skin and colouring, costume, and gear, "
    "and their body proportions. They are NOT poses to reproduce. Do NOT copy "
    "any reference's pose, gesture, hand position, camera angle, cropping, or "
    "its plain empty background. RE-DRAW every character from scratch in a "
    "NEW pose and action that fits THIS scene and the specific moment "
    "described below — turned, leaning, crouching, fighting, reacting as the "
    "moment demands — fully sharing space and interacting with the other "
    "characters, the terrain, the props, and the lighting. Treat each "
    "reference like a turnaround sheet an illustrator glances at for likeness "
    "and then sets aside to draw a brand-new picture. A character whose pose "
    "matches its reference plate is WRONG."
)


# Lean cast lines: NAME + signature gear + role/size only. Deliberately carry
# NO physical-feature prose (hair colour, facial hair, build) — those cues
# (esp. "HAIR: WHITE") were driving drift like Fiz's phantom beard, and the
# reference plates carry appearance far better than words. Gear and role are
# kept because the plates don't reliably reproduce props, and roll-call needs
# them. Opt-in via --lean; on weak models it let identity drift (Hal lost his
# baldness), so the DEFAULT uses the full PC_PORTRAITS feature anchors.
LEAN_CAST = {
    "fiz": (
        "Fiz — a small rock gnome artificer/artillerist (an inventor, not a "
        "warrior). Signature gear: brass tinker's goggles pushed up on his "
        "forehead; a brass wand-arquebus (a stubby wand-sized cannon) that "
        "glows faint blue; a small floating brass drone-cannon hovering near "
        "him; dark leather-and-brass armour and a potion-vial belt."
    ),
    "hal": (
        "Hal — a human paladin, the tallest of the four and the only human. "
        "Signature gear: dull silver-grey plate armour and a deep crimson RED "
        "CLOAK; fights with a sword and shield or a maul."
    ),
    "toz": (
        "Toz — a small halfling storm-sorcerer and ship's captain. Signature "
        "gear: a dark blue naval TRICORN HAT and matching blue captain's coat "
        "with a red neckerchief; conjures a swirling grey whirlwind and "
        "streams of blue water at his fingertips."
    ),
    "eno": (
        "Eno — a half-elf nature cleric. Signature gear: a dark green hooded "
        "cloak, a wooden staff, and a wooden holy symbol shaped like a calm "
        "pond."
    ),
}

# Forces party completeness — the drop-a-random-PC failure of images-only.
CAST_ROLLCALL = (
    "CAST ROLL-CALL: the four player characters are Fiz, Hal, Toz, and Eno. "
    "This party travels together — assume ALL FOUR are present in the scene "
    "and MUST be depicted, each with their signature gear listed above, "
    "UNLESS the summary below clearly says one of them is absent. Never omit "
    "a party member; never invent an extra player character."
)


def _portrait_parts(refs_only: bool = False, full_text: bool = False) -> list:
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
    any_refs = any(REFERENCES_DIR.glob("*-ref-*.jpg"))
    if any_refs:
        parts.append(REFERENCE_USAGE)
    for slug, description in PC_PORTRAITS:
        refs = sorted(REFERENCES_DIR.glob(f"{slug}-ref-*.jpg"))[:MAX_REFS_PER_PC]
        for ref in refs:
            parts.append(
                types.Part.from_bytes(
                    data=ref.read_bytes(), mime_type="image/jpeg"
                )
            )

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
                print(f"WARN: no references for {slug} (refs-only)",
                      file=sys.stderr)
            continue

        portrait = CHARACTERS_DIR / f"{slug}.jpeg"
        has_portrait = portrait.exists()
        if has_portrait:
            parts.append(
                types.Part.from_bytes(
                    data=portrait.read_bytes(), mime_type="image/jpeg"
                )
            )
        if not refs and not has_portrait:
            print(f"WARN: no references or portrait for {slug}", file=sys.stderr)
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
    return parts


def build_contents(summary: str, refs_only: bool = False,
                   full_text: bool = False) -> list:
    """Multimodal input for the HERO image (session-level banner).
    Portraits + style + pivotal moment + full summary."""
    contents = _portrait_parts(refs_only, full_text)
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


def build_beat_contents(title: str, body: str, summary: str,
                        refs_only: bool = False,
                        full_text: bool = False) -> list:
    """Multimodal input for a BEAT image (one story beat within a session).
    Portraits + style + this beat only, with a smaller-scale directive."""
    contents = _portrait_parts(refs_only, full_text)
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


def _generate_one(client, model: str, aspect: str, contents: list,
                  output: Path, label: str, force: bool) -> None:
    """Call Gemini and write bytes to disk. Skips if already present unless
    force is set. Any errors bubble up so the caller decides what to do."""
    if output.exists() and not force:
        print(f"  skip: {output.name} already exists (--force to regenerate)")
        return
    print(f"  {label}: calling {model}…")
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(aspect_ratio=aspect),
        ),
    )
    try:
        image_bytes = extract_image(response)
    except RuntimeError as e:
        text_bits = []
        for candidate in getattr(response, "candidates", []) or []:
            for part in getattr(candidate.content, "parts", []) or []:
                if getattr(part, "text", None):
                    text_bits.append(part.text)
        if text_bits:
            print("  model text response:\n" + "\n".join(text_bits),
                  file=sys.stderr)
        raise
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image_bytes)
    print(f"  wrote {output.name} ({len(image_bytes) / 1024:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else "",
    )
    parser.add_argument("date", help="Session date, YYYY-MM-DD")
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite existing images for this date.",
    )
    parser.add_argument(
        "--model", default="gemini-3.1-flash-image",
        help="Gemini image model id (default: gemini-3.1-flash-image). "
             "The 3.x tier follows the reference plates far better than "
             "gemini-2.5-flash-image, which drifted features and dropped PCs.",
    )
    parser.add_argument(
        "--hero", action="store_true",
        help="Generate ONLY the session hero image (skip beat images).",
    )
    parser.add_argument(
        "--beats", action="store_true",
        help="Generate ONLY the beat images (skip the hero).",
    )
    parser.add_argument(
        "--hero-aspect", default="16:9",
        help='Hero image aspect ratio (default: 16:9).',
    )
    parser.add_argument(
        "--beat-aspect", default="3:2",
        help='Beat image aspect ratio (default: 3:2, more intimate).',
    )
    parser.add_argument(
        "--refs-only", action="store_true",
        help="Feed ONLY the character reference plates (no cast text, no raw "
             "portraits). Purest images-only control; may drop PCs.",
    )
    parser.add_argument(
        "--lean", action="store_true",
        help="Use lean cast text (name + gear only, no feature prose) instead "
             "of the default full feature anchors. Experimental — on weaker "
             "models it let identity drift (e.g. Hal losing his baldness).",
    )
    args = parser.parse_args()
    if args.refs_only and args.lean:
        print("ERROR: --refs-only and --lean are mutually exclusive.",
              file=sys.stderr)
        return 2

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY env var not set.", file=sys.stderr)
        print("       Get one at https://aistudio.google.com/apikey",
              file=sys.stderr)
        sys.exit(2)

    # Default (neither --hero nor --beats given): do both.
    do_hero = args.hero or not (args.hero or args.beats)
    do_beats = args.beats or not (args.hero or args.beats)

    summary = load_summary(args.date)
    img_dir = SESSIONS_DIR / args.date / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    client = genai.Client(api_key=api_key)
    print(f"[{args.date}]")

    if do_hero:
        hero_out = img_dir / "hero.jpg"
        try:
            _generate_one(client, args.model, args.hero_aspect,
                          build_contents(summary, args.refs_only,
                                         full_text=not args.lean),
                          hero_out, "hero", args.force)
        except RuntimeError as e:
            print(f"ERROR generating hero: {e}", file=sys.stderr)
            return 1

    if do_beats:
        beats = extract_beats(summary)
        if not beats:
            print("  no beats found in summary.")
        for i, (title, slug, body) in enumerate(beats, 1):
            beat_out = img_dir / f"{slug}.jpg"
            try:
                _generate_one(
                    client, args.model, args.beat_aspect,
                    build_beat_contents(title, body, summary, args.refs_only,
                                        full_text=not args.lean),
                    beat_out, f"beat {i}/{len(beats)}: {title}", args.force,
                )
            except RuntimeError as e:
                print(f"  ERROR generating beat '{title}': {e}",
                      file=sys.stderr)
                # Keep going — one failing beat shouldn't kill the rest.

    print("Next: python3 website/generate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
