"""Reading the archive off disk into Entity objects.

Every loader takes a Paths first argument so it can be aimed at a fixture
archive in tests rather than the real one."""

import re
from pathlib import Path

from .. import data as _data
from .entity import Entity
from .frontmatter import Field, Frontmatter, parse_frontmatter
from .quest_status import for_section
from .session import IMAGE_SUFFIXES, Session, SessionArtifacts
from .summary import SessionSummary
from .text import read, slugify

STANDING_MAP = {
    "Ally":              ("Ally",         "standing-ally"),
    "Ally (sought)":     ("Ally",         "standing-ally"),
    "Conditional ally":  ("Ally",         "standing-ally"),
    "Reluctant ally":    ("Ally",         "standing-ally"),
    "Lead":              ("Lead",         "standing-lead"),
    "Bounty":            ("Foe",          "standing-foe"),
    "Adversary":         ("Foe",          "standing-foe"),
    "Enemy (slain)":     ("Foe",          "standing-foe"),
    "Politically uneasy":("Foe",          "standing-foe"),
    "Old shipmate":      ("Crew",         "standing-crew"),
    "Acquaintance":      ("Acquaintance", "standing-other"),
    "Background figure": ("Acquaintance", "standing-other"),
    "Deceased":          ("Ghost",        "standing-ghost"),
}


PROVISIONAL = ("last known", "origin", "sought", "unknown", "wandering")


def chip_for(type_str):
    """Standing chip for an NPC's `type:`. Takes the resolved scalar."""
    return STANDING_MAP.get(type_str.strip()) if type_str else None


def port_for(npc, location_names):
    """Return canonical port name for grouping, or None for Adrift."""
    loc = npc.meta["location"].one()
    if not loc:
        return None
    if any(p in loc.lower() for p in PROVISIONAL):
        return None
    best = None
    for name in location_names:
        if name.lower() in loc.lower():
            if best is None or len(name) > len(best):
                best = name
    return best


PC_DEFS = {
    "fiz": {
        "name": "Fiz",
        "full_name": "Hisfiz \"Fiz\" Spinfizzler",
        "aliases": ["Fiz", "Hisfiz", "Hisfiz Spinfizzler", "Spinfizzler"],
        "summary": "Rock Gnome Artificer (Artillerist) from Halruaa. Stole a flying ship to see the world.",
    },
    "hal": {
        "name": "Hal",
        "full_name": "Hal Stormguard",
        "aliases": ["Hal", "Hal Stormguard", "Stormguard"],
        "summary": "Variant Human Paladin, Oath of Vengeance. Ex-militia of the Silver Marches.",
    },
    "toz": {
        "name": "Toz",
        "full_name": "Tozlo \"Toz\" Greenbottle",
        "aliases": ["Toz", "Tozlo", "Tozlo Greenbottle"],
        "summary": "Lightfoot Halfling Storm Sorcerer. Captain of the lost True Hand; his family adopted Eno as a brother.",
    },
    "eno": {
        "name": "Eno",
        "full_name": "Enoril \"Eno\" Wazek",
        "aliases": ["Eno", "Woz", "Eno Woz", "Enoril", "Enoril Wazek", "Wazek"],
        "summary": "Half-Elf Nature Cleric of Eldath. Raised in the wilds; adopted by the Greenbottles.",
    },
}


def load_pcs(paths):
    entities = []
    for slug, defn in PC_DEFS.items():
        md_path = paths.characters / f"{slug}.md"
        body = read(md_path) if md_path.exists() else ""
        img_path = paths.characters / f"{slug}.jpeg"
        image = f"images/characters/{slug}.jpeg" if img_path.exists() else None
        battle_card = (f"battle-cards/{slug}.html"
                       if (paths.battle_cards / f"{slug}.html").exists() else None)
        entities.append(Entity(
            kind="pc", slug=slug, name=defn["name"],
            aliases=defn["aliases"], body=body, image=image,
            summary=defn["summary"],
            meta=Frontmatter({"full_name": defn["full_name"],
                              "battle_card": battle_card}),
        ))
    return entities


def load_dir_entities(kind, directory):
    out = []
    if not directory.exists():
        return out
    for path in sorted(directory.glob("*.md")):
        text = read(path)
        fm, body = parse_frontmatter(text)
        meta = Frontmatter(fm)
        name = meta["name"].one() or path.stem.replace("-", " ").title()
        aliases = meta["aliases"].many()
        if name not in aliases:
            aliases = [name] + aliases
        summary = meta["summary"].prose()
        if not summary and body.strip():
            first = next((ln.strip() for ln in body.split("\n") if ln.strip()), "")
            first = re.split(r"(?<=[.!?])\s", first, maxsplit=1)[0]
            summary = first
        out.append(Entity(
            kind=kind, slug=slugify(path.stem), name=name,
            aliases=aliases, body=body, meta=meta, summary=summary,
        ))
    return out


def load_quests(paths):
    if not paths.quests_file.exists():
        return []
    text = paths.quests_file.read_text(encoding="utf-8")
    out = []
    section = None
    for raw in text.split("\n"):
        line = raw.rstrip()
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            section = m.group(1).strip()
            continue
        m = re.match(r"^- \*\*(.+?)\*\*\.?\s*[—–-]?\s*(.*)$", line)
        if not m or not section:
            continue
        # The Personal section is the crew's own business, not a tracked
        # objective; this is the single place that decides it isn't surfaced.
        if section.lower().startswith("personal"):
            continue
        name = m.group(1).strip().rstrip(".")
        desc = m.group(2).strip()
        first_sentence = re.split(r"(?<=[.!?])\s", desc, maxsplit=1)[0]
        out.append(Entity(
            kind="quest", slug=slugify(name), name=name,
            aliases=[name], body=desc,
            meta=Frontmatter({"section": section}),
            status=for_section(section),
            summary=first_sentence,
        ))
    return out


def load_campaign_state(paths):
    """Small hand-maintained record of the party's current objective and the
    open questions worth investigating — the one bit of 'where are we / what's
    the goal' data the archive doesn't otherwise capture. Current *location* is
    derived from SESSION_LOCATIONS unless the file overrides it. Returns
    {'objective': str, 'open_questions': [str], 'current_location': str|None}."""
    if not paths.campaign_state_file.exists():
        return {"objective": "", "open_questions": [], "current_location": None}
    fm, _ = parse_frontmatter(paths.campaign_state_file.read_text(encoding="utf-8"))
    fm = Frontmatter(fm)
    return {
        # The objective is a sentence, so it must be rejoined: the dialect
        # split it on its own commas into a list of fragments.
        "objective": fm["objective"].prose(),
        "open_questions": fm["open_questions"].many(),
        "current_location": fm["current_location"].one() or None,
    }


def _read_audio_subtitle(script: Path) -> str:
    """Line 2 of an audio script (`## <subtitle>`) — the podcast episode title."""
    try:
        with open(script, encoding="utf-8") as fh:
            fh.readline()  # the "# Tales of the True Hand — DATE" H1
            line2 = fh.readline().strip()
    except OSError:
        return ""
    return line2[3:].strip() if line2.startswith("## ") else ""


def _load_artifacts(sdir: Path) -> SessionArtifacts:
    """Discover what the media pipelines left in one session folder.

    These four rules — hero.* is the banner, every other image is a beat keyed
    by its summary-beat slug, audio/final.mp3 is the recap, its script's line 2
    is the episode title — are stated here and nowhere else. The site's asset
    staging copies from the result rather than walking the tree again.
    """
    hero, beats = None, {}
    img_dir = sdir / "images"
    if img_dir.exists():
        for path in sorted(img_dir.iterdir()):
            if path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            if path.stem == "hero":
                hero = path
            else:
                beats[path.stem] = path

    audio_dir = sdir / "audio"
    final = audio_dir / "final.mp3"
    script = audio_dir / "script.md"
    return SessionArtifacts(
        hero=hero,
        beats=beats,
        audio=final if final.exists() else None,
        audio_subtitle=_read_audio_subtitle(script) if script.exists() else "",
    )


def _player_notes_file(sdir: Path):
    """Fiz's POV notes if present, else whichever PC's notes exist."""
    pn_dir = sdir / "player notes"
    if not pn_dir.exists():
        return None
    fiz = pn_dir / "fiz.md"
    if fiz.exists():
        return fiz
    candidates = sorted(pn_dir.glob("*.md"))
    return candidates[0] if candidates else None


def load_sessions(paths):
    """Every session in the archive, oldest first.

    A folder under sessions/ that holds none of notes, transcript or summary is
    not a session and is skipped — the Session aggregate refuses to exist
    without one of them.
    """
    if not paths.sessions.exists():
        return []

    out = []
    for sdir in sorted(paths.sessions.iterdir()):
        if not sdir.is_dir() or sdir.name == "library":
            continue

        notes_file = _player_notes_file(sdir)
        transcript_file = sdir / "transcript.txt"
        summary_file = sdir / "summary.md"

        notes = read(notes_file) if notes_file else ""
        transcript = read(transcript_file) if transcript_file.exists() else ""
        summary_text = read(summary_file) if summary_file.exists() else ""
        if not (notes or transcript or summary_text):
            continue

        # A summary may lead with a `---` frontmatter block (currently used to
        # declare a `carried:` list of items acquired that session). Split it
        # off so the rendered body doesn't show the raw block.
        summary_fm, summary_body = (parse_frontmatter(summary_text)
                                    if summary_text else ({}, ""))
        carried = Field(summary_fm.get("carried")).many()

        out.append(Session(
            date=sdir.name,
            notes=notes,
            transcript=transcript,
            summary=SessionSummary.parse(summary_body if summary_fm else summary_text),
            carried=tuple(carried),
            artifacts=_load_artifacts(sdir),
        ))
    return out


#: Which locations each session took place in, most important first.
#: Edited in truehand/data/session_locations.toml, not here.
SESSION_LOCATIONS = _data.load("session_locations")["sessions"]
