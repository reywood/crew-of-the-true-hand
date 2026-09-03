"""Reading the archive off disk into Entity objects.

Every loader takes a Paths first argument so it can be aimed at a fixture
archive in tests rather than the real one."""

import re

from .entity import Entity
from .frontmatter import parse_frontmatter
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
    if not type_str:
        return None
    if isinstance(type_str, list):
        type_str = type_str[0] if type_str else ""
    return STANDING_MAP.get(type_str.strip())


def port_for(npc, location_names):
    """Return canonical port name for grouping, or None for Adrift."""
    loc = npc.meta.get("location", "")
    if isinstance(loc, list):
        loc = loc[0] if loc else ""
    loc = loc.strip()
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
            meta={"full_name": defn["full_name"], "battle_card": battle_card},
        ))
    return entities


def load_dir_entities(kind, directory):
    out = []
    if not directory.exists():
        return out
    for path in sorted(directory.glob("*.md")):
        text = read(path)
        fm, body = parse_frontmatter(text)
        name = fm.get("name") or path.stem.replace("-", " ").title()
        aliases_field = fm.get("aliases", "")
        if isinstance(aliases_field, list):
            aliases = aliases_field
        elif isinstance(aliases_field, str) and aliases_field:
            aliases = [aliases_field]
        else:
            aliases = []
        if name not in aliases:
            aliases = [name] + aliases
        summary = fm.get("summary") or ""
        if not summary and body.strip():
            first = next((ln.strip() for ln in body.split("\n") if ln.strip()), "")
            first = re.split(r"(?<=[.!?])\s", first, maxsplit=1)[0]
            summary = first
        out.append(Entity(
            kind=kind, slug=slugify(path.stem), name=name,
            aliases=aliases, body=body, meta=fm, summary=summary,
        ))
    return out


QUEST_SECTION_STATUS = {
    "Main arc — the giant ordning": ("Active — main arc", "active-main"),
    "Allies to recruit / leads to chase": ("Active — lead", "active"),
    "Giant hotspots (intel from Corvin / Chazlauth / Lifferloss)":
        ("Active — region", "active"),
    "Side leads / unresolved": ("Unresolved", "unresolved"),
    "Personal / character": ("Personal", "personal"),
    "Completed": ("Completed", "completed"),
}


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
        if section.lower().startswith("personal"):
            continue
        name = m.group(1).strip().rstrip(".")
        desc = m.group(2).strip()
        status_label, status_class = QUEST_SECTION_STATUS.get(
            section, (section, "active"))
        first_sentence = re.split(r"(?<=[.!?])\s", desc, maxsplit=1)[0]
        out.append(Entity(
            kind="quest", slug=slugify(name), name=name,
            aliases=[name], body=desc,
            meta={"section": section, "status_class": status_class},
            status=status_label,
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
    oq = fm.get("open_questions") or []
    if isinstance(oq, str):
        oq = [oq]
    return {
        "objective": (fm.get("objective") or "").strip() if isinstance(fm.get("objective"), str) else "",
        "open_questions": oq,
        "current_location": (fm.get("current_location") or None),
    }


def load_sessions(paths):
    # Everything for a session lives under sessions/YYYY-MM-DD/:
    #   summary.md, transcript.txt, player notes/<pc>.md,
    #   audio/{script.md, final.mp3, ...}, images/{hero.*, <beat-slug>.*}
    notes, transcripts, summaries = {}, {}, {}
    session_images, session_audio, audio_subtitles = {}, {}, {}
    beat_images_by_date = {}
    if paths.sessions.exists():
        for sdir in paths.sessions.iterdir():
            if not sdir.is_dir() or sdir.name == "library":
                continue
            date = sdir.name
            # Player notes (Fiz's POV) — prefer fiz.md, else the first note file.
            pn_dir = sdir / "player notes"
            if pn_dir.exists():
                note_file = pn_dir / "fiz.md"
                if not note_file.exists():
                    candidates = sorted(pn_dir.glob("*.md"))
                    note_file = candidates[0] if candidates else None
                if note_file and note_file.exists():
                    notes[date] = note_file
            if (sdir / "transcript.txt").exists():
                transcripts[date] = sdir / "transcript.txt"
            if (sdir / "summary.md").exists():
                summaries[date] = sdir / "summary.md"
            # Images: hero.* is the banner; every other image is a beat keyed by slug.
            img_dir = sdir / "images"
            if img_dir.exists():
                beats = {}
                for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                    for p in img_dir.glob(ext):
                        if p.stem == "hero":
                            session_images[date] = p
                        else:
                            beats[p.stem] = p
                if beats:
                    beat_images_by_date[date] = beats
            # Audio: final.mp3 plays on the site; script.md line-2 subtitle is the
            # podcast episode title.
            audio_dir = sdir / "audio"
            if audio_dir.exists():
                if (audio_dir / "final.mp3").exists():
                    session_audio[date] = audio_dir / "final.mp3"
                script = audio_dir / "script.md"
                if script.exists():
                    try:
                        with open(script, encoding="utf-8") as fh:
                            fh.readline()  # skip the H1 line
                            line2 = fh.readline().strip()
                        if line2.startswith("## "):
                            audio_subtitles[date] = line2[3:].strip()
                    except OSError:
                        pass
    dates = sorted(set(notes) | set(transcripts) | set(summaries))
    out = []
    for date in dates:
        note_text = read(notes[date]) if date in notes else ""
        transcript_text = read(transcripts[date]) if date in transcripts else ""
        summary_text = read(summaries[date]) if date in summaries else ""
        # A summary may lead with a `---` YAML frontmatter block (currently
        # used to declare a `carried:` list of items acquired that session).
        # Split it off so the rendered body doesn't show the raw block.
        summary_fm, summary_body = parse_frontmatter(summary_text) if summary_text else ({}, "")
        summary_text_render = summary_body if summary_fm else summary_text
        carried = summary_fm.get("carried") if summary_fm else None
        if isinstance(carried, str):
            carried = [carried]
        carried = carried or []
        image_path = session_images.get(date)
        audio_path = session_audio.get(date)
        # Per-section beat images: sessions/<date>/images/<beat-slug>.jpg
        beat_images = beat_images_by_date.get(date, {})
        # Card-summary one-liner: prefer the summary's "*In brief: ...*" line,
        # then fall back to the notes' first line.
        card_summary = ""
        if summary_text_render:
            for ln in summary_text_render.split("\n"):
                s = ln.strip()
                if s.startswith("*In brief:") and s.endswith("*"):
                    card_summary = s[len("*In brief:"):-1].strip()
                    break
                if s and not s.startswith("#"):
                    card_summary = s.lstrip("*").rstrip("*").strip()
                    break
        if not card_summary and note_text:
            for ln in note_text.split("\n"):
                if ln.strip():
                    card_summary = ln.strip()
                    break
        if not card_summary:
            card_summary = ("Transcript only — no written notes." if transcript_text
                            else "No content.")
        out.append(Entity(
            kind="session", slug=date, name=f"Session {date}",
            aliases=[date], body=note_text,
            meta={"transcript": transcript_text, "date": date,
                  "summary_md": summary_text_render,
                  "image_src": image_path,
                  # Site URL stays date-based even though the source is hero.<ext>.
                  "image_name": f"{date}{image_path.suffix}" if image_path else "",
                  "beat_images": beat_images,
                  "carried": carried,
                  "has_notes": bool(note_text),
                  "has_transcript": bool(transcript_text),
                  "has_summary": bool(summary_text),
                  "has_image": bool(image_path),
                  "audio_src": audio_path,
                  # audio_name is what the site URL points at; setup_output
                  # copies sessions/YYYY-MM-DD/audio/final.mp3 into
                  # site/audio/sessions/YYYY-MM-DD.mp3, so this is always
                  # date-based regardless of on-disk layout.
                  "audio_name": f"{date}.mp3" if audio_path else "",
                  "has_audio": bool(audio_path),
                  "audio_subtitle": audio_subtitles.get(date, "")},
            summary=card_summary,
        ))
    return out


SESSION_LOCATIONS = {
    # session date -> list of location slugs (in order of importance to the session)
    "2025-09-23": ["nightstone"],
    "2025-11-12": ["nightstone", "ardeep-forest"],
    "2025-12-07": ["ardeep-forest"],
    "2025-12-17": ["nightstone"],
    "2026-01-13": ["nightstone"],
    "2026-01-27": [],  # in transit aboard Zephyros's flying castle
    "2026-02-10": ["golden-fields"],
    "2026-03-08": ["golden-fields"],
    "2026-05-12": ["golden-fields"],
    "2026-06-02": ["golden-fields"],
    "2026-06-16": ["waterdeep"],
    "2026-08-12": ["waterdeep", "deep-water-inn", "the-plinth"],
}
