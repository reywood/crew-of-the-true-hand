#!/usr/bin/env python3
"""
Static site generator for the Crew of the True Hand campaign site.

Reads source content from the repo root:
  characters/*.md      Player character sheets (existing format, no frontmatter)
  npcs/*.md            NPC entries (frontmatter + body)
  locations/*.md       Location entries (frontmatter + body)
  quests.md            Quest list, parsed by section + bullet
  session notes/*.md   Session summary notes (Fiz's POV)
  transcripts/*.txt    Raw session transcripts ("detailed account")

Writes generated HTML to website/site/. Cross-links names mentioned in any
rendered body to their detail page.

Re-run after adding or editing source files:
    python3 website/generate.py
"""

import datetime as _dt
import html
import re
import shutil
import subprocess
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = Path(__file__).resolve().parent
SITE = WEB / "site"
STATIC = WEB / "static"

CHAR_DIR = ROOT / "characters"
NPC_DIR = ROOT / "npcs"
LOC_DIR = ROOT / "locations"
ITEM_DIR = ROOT / "items"
NOTES_DIR = ROOT / "session notes"
TRANS_DIR = ROOT / "transcripts"
SUMMARIES_DIR = ROOT / "summaries"
AUDIO_SCRIPTS_DIR = SUMMARIES_DIR / "audio-scripts"
AUDIO_LIBRARY_DIR = SUMMARIES_DIR / "audio" / "library"
AUDIO_CREDITS_FILE = AUDIO_LIBRARY_DIR / "CREDITS.md"
QUESTS_FILE = ROOT / "quests.md"

# Public base URL for absolute links inside the podcast RSS feed.
# The S3 site is served at http://crew-of-the-true-hand.s3-website-us-east-1.amazonaws.com;
# override at build-time with SITE_BASE_URL if the canonical domain changes.
import os as _os
SITE_BASE_URL = _os.environ.get(
    "SITE_BASE_URL",
    "http://crew-of-the-true-hand.s3-website-us-east-1.amazonaws.com",
).rstrip("/")


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def slugify(s):
    s = s.replace("'", "").replace("’", "")
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s


def read(p):
    return Path(p).read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text):
    """Minimal YAML-ish frontmatter parser.

    Handles two list forms in addition to plain scalar values:
      - Inline comma-list:   aliases: Foo, Bar, Baz
      - YAML-style bullets:  carried:
                             - Item one
                             - Item two

    A field with no value on its own line and dashed bullets on the
    following lines becomes a list. Anything else is a scalar (or an
    inline comma-list)."""
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        return {}, text
    body = text[m.end():]
    fm = {}
    lines = m.group(1).split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" not in line:
            i += 1
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        # Empty value + following bullet lines = list.
        if not v:
            items = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j].lstrip()
                if nxt.startswith("- "):
                    items.append(nxt[2:].strip())
                    j += 1
                elif nxt.startswith("-") and len(nxt) > 1 and nxt[1] != " ":
                    # tolerate "-item" with no space
                    items.append(nxt[1:].strip())
                    j += 1
                else:
                    break
            fm[k] = items
            i = j
            continue
        if "," in v:
            v = [x.strip() for x in v.split(",") if x.strip()]
        fm[k] = v
        i += 1
    return fm, body


# --------------------------------------------------------------------------
# minimal markdown
# --------------------------------------------------------------------------

def md_inline(s):
    s = html.escape(s)
    parts = re.split(r"(`[^`]+`)", s)
    for i, p in enumerate(parts):
        if p.startswith("`") and p.endswith("`"):
            parts[i] = f"<code>{p[1:-1]}</code>"
        else:
            p = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", p)
            p = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", p)
            p = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', p)
            parts[i] = p
    return "".join(parts)


def md_to_html(text):
    if not text:
        return ""
    out, para, list_items = [], [], None

    def flush_para():
        nonlocal para
        if para:
            out.append("<p>" + " ".join(md_inline(line) for line in para) + "</p>")
            para = []

    def flush_list():
        nonlocal list_items
        if list_items is not None:
            out.append("<ul>" + "".join(
                f"<li>{md_inline(it)}</li>" for it in list_items) + "</ul>")
            list_items = None

    def flush():
        flush_para()
        flush_list()

    for raw in text.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if re.match(r"^---+$", line):
            flush()
            out.append("<hr>")
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            n = len(m.group(1))
            out.append(f"<h{n}>{md_inline(m.group(2))}</h{n}>")
            continue
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m:
            flush_para()
            if list_items is None:
                list_items = []
            list_items.append(m.group(1))
            continue
        flush_list()
        para.append(line)
    flush()
    return "\n".join(out)


# --------------------------------------------------------------------------
# entity model
# --------------------------------------------------------------------------

class Entity:
    def __init__(self, kind, slug, name, aliases=None, body="",
                 meta=None, image=None, status=None, summary=None):
        self.kind = kind  # 'pc', 'npc', 'location', 'quest', 'session'
        self.slug = slug
        self.name = name
        self.aliases = aliases or []
        self.body = body
        self.meta = meta or {}
        self.image = image
        self.status = status
        self.summary = summary

    @property
    def href(self):
        prefix = {"pc": "pc", "npc": "npc", "location": "loc", "item": "item",
                  "quest": "quest", "session": "session"}[self.kind]
        return f"{prefix}-{self.slug}.html"


# --------------------------------------------------------------------------
# linkifier
# --------------------------------------------------------------------------

def build_link_map(entities):
    """alias -> href. First registration wins (PCs are added first)."""
    table = {}
    for e in entities:
        for n in [e.name] + list(e.aliases or []):
            n = n.strip()
            if not n or n in table:
                continue
            table[n] = e.href
    return table


def linkify_html(rendered, current_href, link_map):
    aliases = [a for a, h in link_map.items() if h != current_href]
    if not aliases:
        return rendered
    aliases.sort(key=lambda x: -len(x))
    pattern = re.compile(
        r"(?<![A-Za-z0-9])(" + "|".join(re.escape(a) for a in aliases) + r")(?![A-Za-z0-9])"
    )
    linked = set()
    parts = re.split(r"(<[^>]+>)", rendered)
    in_anchor = False
    in_code = False
    no_link_depth = 0
    for i, part in enumerate(parts):
        if part.startswith("<") and part.endswith(">"):
            t = part.lower()
            if t.startswith("<a "):
                in_anchor = True
            elif t == "</a>":
                in_anchor = False
            elif t.startswith("<code") or t.startswith("<pre"):
                in_code = True
            elif t in ("</code>", "</pre>"):
                in_code = False
            elif 'class="no-link"' in t or "class='no-link'" in t or ' no-link"' in t or ' no-link\'' in t:
                no_link_depth += 1
            elif no_link_depth > 0 and t.startswith("</"):
                no_link_depth -= 1
            continue
        if in_anchor or in_code or no_link_depth > 0 or not part:
            continue

        def repl(m):
            alias = m.group(1)
            href = link_map[alias]
            if href in linked:
                return alias
            linked.add(href)
            return f'<a class="entity-link" href="{href}">{alias}</a>'

        parts[i] = pattern.sub(repl, part)
    return "".join(parts)


# --------------------------------------------------------------------------
# standing chips + sea-chart grouping
# --------------------------------------------------------------------------

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


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------

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
        "summary": "Lightfoot Halfling Storm Sorcerer. Captain of the lost True Hand; adopted brother to Woz.",
    },
    "woz": {
        "name": "Woz",
        "full_name": "Enoril \"Eno\" Wazek",
        "aliases": ["Woz", "Eno", "Eno Woz", "Enoril", "Enoril Wazek", "Wazek"],
        "summary": "Half-Elf Nature Cleric of Eldath. Raised in the wilds; adopted by the Greenbottles.",
    },
}


def load_pcs():
    entities = []
    for slug, defn in PC_DEFS.items():
        md_path = CHAR_DIR / f"{slug}.md"
        body = read(md_path) if md_path.exists() else ""
        img_path = CHAR_DIR / f"{slug}.jpeg"
        image = f"images/characters/{slug}.jpeg" if img_path.exists() else None
        entities.append(Entity(
            kind="pc", slug=slug, name=defn["name"],
            aliases=defn["aliases"], body=body, image=image,
            summary=defn["summary"],
            meta={"full_name": defn["full_name"]},
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


def load_quests():
    if not QUESTS_FILE.exists():
        return []
    text = QUESTS_FILE.read_text(encoding="utf-8")
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


def load_sessions():
    notes = {p.stem: p for p in NOTES_DIR.glob("*.md")} if NOTES_DIR.exists() else {}
    transcripts = {p.stem: p for p in TRANS_DIR.glob("*.txt")} if TRANS_DIR.exists() else {}
    summaries = {p.stem: p for p in SUMMARIES_DIR.glob("*.md")} if SUMMARIES_DIR.exists() else {}
    # Hero images generated by scripts/generate-session-image.py
    images_dir = SUMMARIES_DIR / "images"
    session_images = {}
    if images_dir.exists():
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            for p in images_dir.glob(ext):
                session_images[p.stem] = p
    # Audio recaps generated by scripts/generate-session-audio.py
    # New layout: summaries/audio/YYYY-MM-DD/final.mp3 per session, with
    # persistent per-chunk TTS output under chunks/ and a manifest.json for
    # cache invalidation. Fall back to the legacy flat summaries/audio/*.mp3
    # path for anything that hasn't been migrated.
    audio_dir = SUMMARIES_DIR / "audio"
    session_audio = {}
    if audio_dir.exists():
        for entry in audio_dir.iterdir():
            if entry.is_dir():
                final = entry / "final.mp3"
                if final.exists():
                    session_audio[entry.name] = final
        for p in audio_dir.glob("*.mp3"):
            session_audio.setdefault(p.stem, p)
    # Audio-script subtitles (line 2 `## <subtitle>` in each script file) —
    # used as the podcast episode title. Optional.
    audio_subtitles = {}
    if AUDIO_SCRIPTS_DIR.exists():
        for p in AUDIO_SCRIPTS_DIR.glob("*.md"):
            try:
                with open(p, encoding="utf-8") as fh:
                    fh.readline()  # skip the H1 line
                    line2 = fh.readline().strip()
                if line2.startswith("## "):
                    audio_subtitles[p.stem] = line2[3:].strip()
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
        # Per-section beat images: summaries/images/<date>/<beat-slug>.jpg
        beat_images = {}
        beats_dir = SUMMARIES_DIR / "images" / date
        if beats_dir.exists() and beats_dir.is_dir():
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                for p in beats_dir.glob(ext):
                    beat_images[p.stem] = p
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
                  "image_name": image_path.name if image_path else "",
                  "beat_images": beat_images,
                  "carried": carried,
                  "has_notes": bool(note_text),
                  "has_transcript": bool(transcript_text),
                  "has_summary": bool(summary_text),
                  "has_image": bool(image_path),
                  "audio_src": audio_path,
                  # audio_name is what the site URL points at; setup_output
                  # normalizes every source (either summaries/audio/YYYY-MM-DD/final.mp3
                  # or the legacy flat summaries/audio/YYYY-MM-DD.mp3) into
                  # site/audio/sessions/YYYY-MM-DD.mp3, so this is always
                  # date-based regardless of on-disk layout.
                  "audio_name": f"{date}.mp3" if audio_path else "",
                  "has_audio": bool(audio_path),
                  "audio_subtitle": audio_subtitles.get(date, "")},
            summary=card_summary,
        ))
    return out


# --------------------------------------------------------------------------
# layout
# --------------------------------------------------------------------------

NAV = [
    ("index.html", "Home"),
    ("sessions.html", "Sessions"),
    ("characters.html", "Characters"),
    ("npcs.html", "NPCs"),
    ("locations.html", "Locations"),
    ("items.html", "Items"),
    ("quests.html", "Quests"),
]


def render_nav(current=None):
    items = []
    for href, label in NAV:
        cls = ' class="active"' if href == current else ""
        items.append(f'<a href="{href}"{cls}>{label}</a>')
    return '<nav class="site-nav">' + "".join(items) + "</nav>"


def page(title, body, current_nav=None, breadcrumb=None):
    nav = render_nav(current_nav)
    bc = f'<div class="breadcrumb">{breadcrumb}</div>' if breadcrumb else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — Crew of the True Hand</title>
<link rel="stylesheet" href="static/style.css">
<script defer src="static/podcast-subscribe.js"></script>
</head>
<body>
<header class="site-header">
  <div class="site-title"><a href="index.html"><span class="anchor">⚓</span> Crew of the <em>True Hand</em></a></div>
  {nav}
</header>
<main class="content">
{bc}
{body}
</main>
<footer class="site-footer">
  <div class="rope-divider"></div>
  <p>Tales from the sea and the giant-haunted North.</p>
</footer>
</body>
</html>
"""


def chunk_transcript(text):
    text = text.strip()
    if not text:
        return []
    text_n = re.sub(r"\s+", " ", text)
    sentences = re.split(r"(?<=[.!?])\s+", text_n)
    out = []
    for i in range(0, len(sentences), 6):
        chunk = " ".join(sentences[i:i+6]).strip()
        if chunk:
            out.append(chunk)
    return out


# --------------------------------------------------------------------------
# page builders
# --------------------------------------------------------------------------

def write_page(filename, content):
    (SITE / filename).write_text(content, encoding="utf-8")


def setup_output():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    (SITE / "static").mkdir()
    if STATIC.exists():
        for f in STATIC.glob("*"):
            shutil.copy2(f, SITE / "static" / f.name)
    img_dir = SITE / "images" / "characters"
    img_dir.mkdir(parents=True, exist_ok=True)
    if CHAR_DIR.exists():
        for img in CHAR_DIR.glob("*.jpeg"):
            shutil.copy2(img, img_dir / img.name)
    # Podcast cover image generated by scripts/generate-podcast-cover.py
    cover_src = SUMMARIES_DIR / "podcast-cover.jpg"
    if cover_src.exists():
        (SITE / "images").mkdir(parents=True, exist_ok=True)
        shutil.copy2(cover_src, SITE / "images" / "podcast-cover.jpg")
    # Session audio recaps generated by scripts/generate-session-audio.py.
    # Per-session final MP3s live at summaries/audio/YYYY-MM-DD/final.mp3 in
    # the new layout; legacy flat summaries/audio/YYYY-MM-DD.mp3 files are
    # still picked up for anything not yet migrated. We rename each copied
    # file to YYYY-MM-DD.mp3 at the site so URL paths stay stable.
    audio_src = SUMMARIES_DIR / "audio"
    if audio_src.exists():
        audio_dst = SITE / "audio" / "sessions"
        audio_dst.mkdir(parents=True, exist_ok=True)
        for entry in audio_src.iterdir():
            if entry.is_dir():
                final = entry / "final.mp3"
                if final.exists():
                    shutil.copy2(final, audio_dst / f"{entry.name}.mp3")
        for mp3 in audio_src.glob("*.mp3"):
            target = audio_dst / mp3.name
            if not target.exists():
                shutil.copy2(mp3, target)
    # Session hero images generated by scripts/generate-session-image.py
    session_img_dir = SITE / "images" / "sessions"
    session_img_dir.mkdir(parents=True, exist_ok=True)
    session_src = SUMMARIES_DIR / "images"
    if session_src.exists():
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            for img in session_src.glob(ext):
                shutil.copy2(img, session_img_dir / img.name)
        # Per-date beat image subdirectories.
        for beats_src in session_src.iterdir():
            if not beats_src.is_dir():
                continue
            beats_dst = session_img_dir / beats_src.name
            beats_dst.mkdir(parents=True, exist_ok=True)
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                for img in beats_src.glob(ext):
                    shutil.copy2(img, beats_dst / img.name)


QUEST_IMPACT_SCORE = {
    # Higher = more central to the campaign's spine. Completed drops out.
    "Active — main arc": 4,
    "Active — lead":     3,
    "Active — region":   3,
    "Unresolved":        2,
    "Personal":          1,
    "Completed":         0,
}


# Quest dependency graph. Key = source quest name; value = list of quest names
# it helps achieve. Both directions (forward "helps" and backward "supported by")
# are computed from this single table so we only encode each edge once.
# The Personal section (Fiz/Toz/Woz) is not surfaced as quests, so no edges
# should reference those; keep dependencies within the surfaced quest set.
QUEST_DEPENDENCIES = {
    "Find Harshnag":                      ["Reach the Oracle"],
    "Get to Silverymoon via the Harpers": ["Find Harshnag"],
    "Visit the Eye of Annam":             ["Reach the Oracle"],
    "Old Gnawbone":                       ["Reach the Oracle"],
    "Vexalanthus":                        ["Reach the Oracle"],
    "Vandal Lovelace":                    ["Find Harshnag"],
    "Naxene":                             ["Find Harshnag"],
}


def _normalize_tag_list(value):
    """Coerce a frontmatter field (string, list, or None) to a lowercased,
    stripped list of tag strings."""
    if not value:
        return []
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",")]
    else:
        parts = [str(p).strip() for p in value]
    return [p.lower() for p in parts if p]


def _attach_item_expertise(items, npcs):
    """Cross-reference items and NPCs by expertise tags. Populates:
      item.meta['helpers']       — list of NPC Entities that could help
      npc.meta['can_help_with']  — list of item Entities they could help with
    """
    for item in items:
        item.meta.setdefault("helpers", [])
    for npc in npcs:
        npc.meta.setdefault("can_help_with", [])
    for item in items:
        needs = set(_normalize_tag_list(item.meta.get("expertise_needed")))
        if not needs:
            continue
        for npc in npcs:
            exp = set(_normalize_tag_list(npc.meta.get("expertise")))
            if needs & exp:
                item.meta["helpers"].append(npc)
                npc.meta["can_help_with"].append(item)


def _attach_quest_deps(quests):
    """Walk QUEST_DEPENDENCIES, resolve each side to a quest Entity, and
    stash the forward and reverse lists on each quest's meta. Warns to
    stderr if any name in the table does not match a real quest."""
    import sys as _sys
    by_name = {q.name: q for q in quests}
    helps = {q.name: [] for q in quests}
    supports = {q.name: [] for q in quests}
    for src_name, targets in QUEST_DEPENDENCIES.items():
        if src_name not in by_name:
            print(f"WARN: dep source quest not found: {src_name!r}",
                  file=_sys.stderr)
            continue
        for tgt_name in targets:
            if tgt_name not in by_name:
                print(f"WARN: dep target quest not found: {tgt_name!r} "
                      f"(referenced by {src_name!r})", file=_sys.stderr)
                continue
            helps[src_name].append(by_name[tgt_name])
            supports[tgt_name].append(by_name[src_name])
    for q in quests:
        q.meta["helps"] = helps[q.name]
        q.meta["supported_by"] = supports[q.name]


def _quest_recency(quest) -> str:
    """Latest YYYY-MM-DD referenced in a quest's body — the parenthetical
    session dates at the end of each quest bullet in quests.md. Returns
    empty string if the quest carries no date."""
    dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", quest.body or "")
    return max(dates) if dates else ""


def _top_active_quests(quests, limit=6):
    """Rank active quests by (impact × recency). Completed quests drop out;
    impact wins ties, most-recent-session wins within an impact tier."""
    ranked = []
    for q in quests:
        impact = QUEST_IMPACT_SCORE.get(q.status, 0)
        if impact == 0:
            continue
        recency = _quest_recency(q) or "0000-00-00"
        ranked.append((impact, recency, q))
    ranked.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return ranked[:limit]


def index_page(pcs, npcs, locations, quests, sessions):
    top_quests = _top_active_quests(quests, limit=6)
    recent = sessions[::-1][:3] if sessions else []

    cards = """
<section class="hero">
  <h1>The Crew of the <em>True Hand</em></h1>
  <p class="tagline">A four-soul company aboard borrowed sails, chasing the cause of giants run wild across the North.</p>
</section>
"""

    if top_quests:
        cards += """
<section class="home-quests">
  <h2>What's on your plate</h2>
  <p class="muted small home-quests-note">Ranked by story impact, then by the last session that touched it.</p>
  <ul class="home-quest-list">"""
        for _impact, recency, q in top_quests:
            status_class = q.meta.get("status_class", "active")
            last_touched = ""
            if recency and recency != "0000-00-00":
                last_touched = (
                    f'<a class="home-quest-touch" href="session-{recency}.html">'
                    f'last touched · session {recency}</a>'
                )
            summary = md_inline(q.summary or "")

            deps_html = ""
            helps = q.meta.get("helps") or []
            supported_by = q.meta.get("supported_by") or []
            dep_lines = []
            if helps:
                links = " · ".join(
                    f'<a href="{d.href}">{html.escape(d.name)}</a>'
                    for d in helps
                )
                dep_lines.append(
                    f'<span class="home-quest-dep"><span class="dep-arrow">&rarr;</span> '
                    f'helps: {links}</span>'
                )
            if supported_by:
                links = " · ".join(
                    f'<a href="{d.href}">{html.escape(d.name)}</a>'
                    for d in supported_by
                )
                dep_lines.append(
                    f'<span class="home-quest-dep"><span class="dep-arrow">&larr;</span> '
                    f'steps toward this: {links}</span>'
                )
            if dep_lines:
                deps_html = f'<p class="home-quest-deps">{" ".join(dep_lines)}</p>'

            cards += f"""
    <li class="home-quest">
      <div class="home-quest-head">
        <a class="home-quest-name" href="{q.href}">{html.escape(q.name)}</a>
        <span class="status-chip status-{status_class}">{html.escape(q.status or "")}</span>
      </div>
      <p class="home-quest-line">{summary}</p>
      {deps_html}
      {last_touched}
    </li>"""
        cards += """
  </ul>
  <p class="home-more"><a href="quests.html">See the full quest log &rsaquo;</a></p>
</section>
"""

    if recent:
        cards += "<section class='recent'><h2>Most recent sessions</h2><ul class='session-list'>"
        for s in recent:
            cards += f'<li><a href="{s.href}">{html.escape(s.name)}</a> — {html.escape(s.summary)}</li>'
        cards += "</ul></section>"

    # Podcast CTA — surface "Tales of the True Hand" to first-time visitors.
    cards += """
<section class="home-podcast">
  <h2><span aria-hidden="true">&#9836;</span> Listen: Tales of the True Hand</h2>
  <p>A storyteller-voiced audio recap of every session, narrated by Vandal Lovelace beside the hearth.</p>
  <p class="podcast-cta"><a href="sessions.html" class="podcast-link">Play an episode</a>
  <span class="podcast-cta-tail">— or subscribe by adding <code>feed.xml</code> to your podcast app of choice.</span></p>
</section>
"""

    # Directory / navigation grid — moved beneath the actionable content so
    # active players see quests and sessions first. Still useful as a
    # browsing directory for casual visitors.
    active_quests = [q for q in quests if q.status and "Active" in q.status]
    cards += f"""
<section class="home-directory">
<h2>Browse the archive</h2>
<div class="grid grid-2">
  <a class="card" href="characters.html">
    <h2><span class="icon">⚓</span> The Crew</h2>
    <p>{len(pcs)} player characters, each with their own port of call.</p>
  </a>
  <a class="card" href="quests.html">
    <h2><span class="icon">🧭</span> Quests</h2>
    <p>{len(active_quests)} active threads, side leads, and completed jobs.</p>
  </a>
  <a class="card" href="sessions.html">
    <h2><span class="icon">📜</span> Sessions</h2>
    <p>{len(sessions)} logged sessions, from the wreck off Nightstone to the streets of Waterdeep.</p>
  </a>
  <a class="card" href="npcs.html">
    <h2><span class="icon">🪶</span> NPCs</h2>
    <p>{len(npcs)} catalogued friends, foes, and folk worth remembering.</p>
  </a>
  <a class="card" href="locations.html">
    <h2><span class="icon">🗺</span> Locations</h2>
    <p>{len(locations)} ports and waypoints across Faerûn.</p>
  </a>
</div>
</section>
"""
    return page("Home", cards, current_nav="index.html")


def pc_list_page(pcs, link_map):
    cards = []
    for pc in pcs:
        img = (f'<img class="portrait" src="{pc.image}" alt="{html.escape(pc.name)}">'
               if pc.image else "")
        cards.append(f"""
<a class="card pc-card" href="{pc.href}">
  {img}
  <h3>{html.escape(pc.meta.get("full_name", pc.name))}</h3>
  <p>{html.escape(pc.summary)}</p>
</a>""")
    body = "<h1>The Crew</h1>\n<section class='grid grid-2'>" + "".join(cards) + "</section>"
    return page("The Crew", linkify_html(body, "characters.html", link_map),
                current_nav="characters.html")


def detail_page_pc(pc, link_map):
    rendered = md_to_html(pc.body)
    linked = linkify_html(rendered, pc.href, link_map)
    img = (f'<img class="portrait portrait-large" src="{pc.image}" alt="{html.escape(pc.name)}">'
           if pc.image else "")
    body = f"""<article class="detail">
  {img}
  <p class="muted">{html.escape(pc.summary)}</p>
  <div class="detail-body">
  {linked}
  </div>
</article>"""
    bc = f'<a href="characters.html">Characters</a> &rsaquo; {html.escape(pc.name)}'
    return page(pc.name, body, current_nav="characters.html", breadcrumb=bc)


def list_page_generic(title, current, items, link_map, kind):
    cards = []
    for e in sorted(items, key=lambda x: x.name.lower()):
        cards.append(f"""
<a class="card {kind}-card" href="{e.href}">
  <h3>{html.escape(e.name)}</h3>
  <p>{html.escape(e.summary or "")}</p>
</a>""")
    body = f"<h1>{html.escape(title)}</h1>\n<section class='grid grid-3'>" + "".join(cards) + "</section>"
    return page(title, linkify_html(body, current, link_map), current_nav=current)


LOCATION_MAP_DATA = {
    # On-chart pins: x%, y% of the map image (faerun.png, 1573×1000).
    # Coords are the brass dot position. Region labels (no dot) are centered on
    # the coord. Most positions come from faerun.csv (pixel coords ÷ map size).
    #
    "waterdeep":           {"x": 34.9, "y": 78.3, "dir": "w"},
    "nightstone":          {"x": 43.3, "y": 79.3, "dir": "se"},
    "ardeep-forest":       {"x": 42.8, "y": 76.6, "dir": "nw"},  # west of dot to clear Nightstone
    "golden-fields":       {"x": 44.3, "y": 71.8, "dir": "ne"},  # north of dot to clear Ardeep
    "triboar":             {"x": 42.2, "y": 43.8},
    "kryptgarden-forest":  {"x": 36.7, "y": 58.1},
    "silverymoon":         {"x": 58.4, "y": 27.0},
    "silver-marches":      {"x": 71.8, "y": 15.9},  # region label
    "spine-of-the-world":  {"x": 38.8, "y": 9.3},   # region label across top
    "bryn-shandar":        {"x": 19.5, "y": 11.1, "dir": "se"},  # "Bryn Shander" in CSV
    # Not on the canon map — campaign-specific wreck site, placed offshore in
    # the Sea of Swords, west of Nightstone. Label hangs further west into
    # the open sea.
    "the-true-hand":       {"x": 38.0, "y": 83.0, "dir": "w"},
    #
    # Off-chart cartouches (south of frame, mythic, or fictional):
    "athkatla":            {"cartouche": "Far South"},
    "halruaa":             {"cartouche": "Far South"},
    "eye-of-annam":        {"cartouche": "Beyond the Charts"},
    "pearl-isles":         {"cartouche": "Beyond the Charts"},
    "darkar":              {"cartouche": "Whereabouts Unknown"},
    "darkhope":            {"cartouche": "Whereabouts Unknown"},
}
CARTOUCHE_ORDER = ["Far South", "Beyond the Charts", "Whereabouts Unknown"]

MAP_IMAGE = '<img class="map-image" src="static/faerun.png" alt="A map of the Sword Coast" loading="lazy">'


def locations_chart_page(locations, link_map):
    pins = []
    cartouches = {n: [] for n in CARTOUCHE_ORDER}
    for loc in locations:
        data = LOCATION_MAP_DATA.get(loc.slug, {})
        if "x" in data:
            pins.append((loc, data["x"], data["y"], data.get("dir", "e")))
        elif "cartouche" in data:
            cartouches[data["cartouche"]].append(loc)

    chunks = [
        '<h1>The Chart</h1>',
        '<p class="subhead"><em>A working chart of the Sword Coast. Mark not for scale.</em></p>',
        '<div class="map-plate">',
        MAP_IMAGE,
    ]
    for loc, x, y, label_dir in pins:
        is_region = loc.slug in ("spine-of-the-world", "silver-marches")
        classes = ["map-pin"]
        if is_region:
            classes.append("map-pin-region")
        elif label_dir != "e":
            classes.append(f"map-pin-dir-{label_dir}")
        cls = " ".join(classes)
        chunks.append(
            f'<a class="{cls}" href="{loc.href}" style="left:{x}%;top:{y}%">'
            f'<span class="map-pin-dot"></span>'
            f'<span class="map-pin-label">{html.escape(loc.name)}</span>'
            f'</a>'
        )
    chunks.append('</div>')

    chunks.append('<aside class="map-cartouches">')
    for cname in CARTOUCHE_ORDER:
        members = cartouches[cname]
        if not members:
            continue
        chunks.append('<div class="cartouche">')
        chunks.append(f'<h4>{html.escape(cname)}</h4>')
        chunks.append('<ul>')
        for loc in sorted(members, key=lambda l: l.name.lower()):
            chunks.append(f'<li><a href="{loc.href}">{html.escape(loc.name)}</a></li>')
        chunks.append('</ul>')
        chunks.append('</div>')
    chunks.append('</aside>')

    chunks.append('<section class="location-roster">')
    chunks.append('<h2>All Locations</h2>')
    chunks.append('<ul class="location-list">')
    for loc in sorted(locations, key=lambda l: l.name.lower()):
        loc_type = loc.meta.get("type", "")
        if isinstance(loc_type, list):
            loc_type = loc_type[0] if loc_type else ""
        type_html = (f'<span class="loc-type">{html.escape(loc_type)}</span>'
                     if loc_type else "")
        chunks.append(
            f'<li><a href="{loc.href}">{html.escape(loc.name)}</a>{type_html}</li>'
        )
    chunks.append('</ul>')
    chunks.append('</section>')

    body = "\n".join(chunks)
    return page("Locations", linkify_html(body, "locations.html", link_map),
                current_nav="locations.html")


def _location_strip_qualifier(loc):
    """'Silverymoon (last known)' -> 'Silverymoon'; 'Waterdeep, Trades Ward' kept."""
    if not loc:
        return ""
    return re.sub(r"\s*\([^)]*\)\s*", "", loc).strip()


def _affiliations(meta):
    aff = meta.get("affiliation", "")
    if isinstance(aff, list):
        return [a for a in aff if a]
    if isinstance(aff, str) and aff.strip():
        return [a.strip() for a in aff.split(",") if a.strip()]
    return []


def npc_table_page(npcs, link_map):
    blocks = []
    for npc in sorted(npcs, key=lambda n: n.name.lower()):
        chip = chip_for(npc.meta.get("type", ""))
        chip_html = '<span class="muted">—</span>'
        if chip:
            label, cls = chip
            chip_html = (
                f'<span class="standing-chip {cls}">{html.escape(label)}</span>'
            )
        loc = npc.meta.get("location", "")
        if isinstance(loc, list):
            loc = ", ".join(loc)
        loc = (loc or "").strip()
        met = _location_strip_qualifier(loc)
        affiliations = _affiliations(npc.meta)
        aff_html = (
            html.escape(", ".join(affiliations))
            if affiliations
            else '<span class="muted">—</span>'
        )
        met_html = html.escape(met) if met else '<span class="muted">—</span>'
        summary = html.escape(npc.summary or "")
        desc_html = (
            summary if summary else '<span class="muted">No notes yet.</span>'
        )

        blocks.append(
            '<tbody class="npc-block">'
            '<tr class="npc-main">'
            f'<td class="col-name"><a href="{npc.href}">{html.escape(npc.name)}</a></td>'
            f'<td class="col-affil">{aff_html}</td>'
            f'<td class="col-met">{met_html}</td>'
            f'<td class="col-status">{chip_html}</td>'
            '</tr>'
            '<tr class="npc-desc">'
            f'<td colspan="4">{desc_html}</td>'
            '</tr>'
            '</tbody>'
        )

    body = (
        '<h1>The Roster</h1>\n'
        '<p class="subhead"><em>Everyone the crew has met, heard tell of, or owes a debt to.</em></p>\n'
        '<div class="roster-wrap">\n'
        '<table class="roster-table">\n'
        '<thead><tr>'
        '<th class="col-name">Name</th>'
        '<th class="col-affil">Affiliations</th>'
        '<th class="col-met">First Encountered</th>'
        '<th class="col-status">Status</th>'
        '</tr></thead>\n'
        + "\n".join(blocks) + '\n'
        '</table>\n'
        '</div>'
    )
    return page("NPCs", linkify_html(body, "npcs.html", link_map),
                current_nav="npcs.html")


def _npc_card(npc, show_last_seen):
    chip = chip_for(npc.meta.get("type", ""))
    chip_html = ""
    if chip:
        label, cls = chip
        chip_html = f'<span class="standing-chip {cls}">{html.escape(label)}</span>'
    last_seen_html = ""
    if show_last_seen:
        loc = npc.meta.get("location", "")
        if isinstance(loc, list):
            loc = ", ".join(loc)
        loc = loc.strip() if loc else "—"
        last_seen_html = f'<p class="last-seen">Last seen: {html.escape(loc)}</p>'
    summary = html.escape(npc.summary or "")
    return (
        f'<a class="card npc-card" href="{npc.href}">'
        f'<div class="npc-card-head"><h3>{html.escape(npc.name)}</h3>{chip_html}</div>'
        f'{last_seen_html}'
        f'<p>{summary}</p>'
        f'</a>'
    )


def npc_chart_page(npcs, locations, link_map):
    loc_by_name = {l.name: l for l in locations}
    location_names = list(loc_by_name.keys())

    grouped = {}
    adrift = []
    for npc in npcs:
        port = port_for(npc, location_names)
        if port is None:
            adrift.append(npc)
        else:
            grouped.setdefault(port, []).append(npc)

    ordered = sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0].lower()))

    chunks = [
        '<h1>The Roster</h1>',
        '<p class="subhead"><em>By port, as the chart was last drawn.</em></p>',
    ]
    for port_name, entries in ordered:
        port = loc_by_name[port_name]
        port_type = port.meta.get("type", "")
        if isinstance(port_type, list):
            port_type = port_type[0] if port_type else ""
        port_type = (port_type or "").strip().lower()
        count = len(entries)
        souls = "soul" if count == 1 else "souls"
        gloss = " · ".join(p for p in [port_type, f"{count} {souls}"] if p)
        chunks.append('<section class="chart-port">')
        chunks.append('<header class="chart-port-header">')
        chunks.append(
            f'<a class="chart-port-name" href="{port.href}">{html.escape(port_name)}</a>'
        )
        chunks.append(f'<span class="chart-port-gloss">{html.escape(gloss)}</span>')
        chunks.append('</header>')
        chunks.append('<div class="chart-port-grid">')
        for npc in sorted(entries, key=lambda n: n.name.lower()):
            chunks.append(_npc_card(npc, show_last_seen=False))
        chunks.append('</div>')
        chunks.append('</section>')

    if adrift:
        count = len(adrift)
        souls = "soul" if count == 1 else "souls"
        chunks.append('<section class="chart-adrift">')
        chunks.append('<header class="chart-port-header chart-adrift-header">')
        chunks.append('<span class="chart-port-name">Adrift</span>')
        chunks.append(
            f'<span class="chart-port-gloss">{count} {souls}, no fixed port</span>'
        )
        chunks.append('</header>')
        chunks.append('<div class="chart-port-grid">')
        for npc in sorted(adrift, key=lambda n: n.name.lower()):
            chunks.append(_npc_card(npc, show_last_seen=True))
        chunks.append('</div>')
        chunks.append('</section>')

    body = "\n".join(chunks)
    return page("NPCs", linkify_html(body, "npcs.html", link_map),
                current_nav="npcs.html")


def _render_mentioned_in(dates, session_lookup):
    """Render a 'Mentioned in sessions' block below the h1 of a detail page.
    dates: iterable of YYYY-MM-DD strings; sorted+deduped internally.
    session_lookup: dict {date: session Entity} for hrefs."""
    seen = sorted({d for d in dates if d})
    if not seen:
        return ""
    chips = []
    for d in seen:
        s = session_lookup.get(d)
        if s:
            chips.append(f'<a class="session-chip" href="{s.href}">{html.escape(d)}</a>')
        else:
            chips.append(f'<span class="session-chip session-chip-missing">{html.escape(d)}</span>')
    return (
        '<aside class="mentioned-in">'
        '<span class="mentioned-in-label">Mentioned in sessions:</span> '
        + " ".join(chips)
        + '</aside>'
    )


def _extract_session_dates(value):
    """Normalize a frontmatter sessions field into a list of YYYY-MM-DD."""
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [s.strip() for s in str(value).split(",") if s.strip()]


def _render_expertise_link_block(label, entries):
    """Render a small cross-reference block used on item + NPC pages."""
    if not entries:
        return ""
    links = ", ".join(
        f'<a href="{ent.href}">{html.escape(ent.name)}</a>'
        for ent in entries
    )
    return (
        '<aside class="expertise-link">'
        f'<span class="expertise-label">{html.escape(label)}:</span> {links}'
        '</aside>'
    )


def detail_page_generic(e, list_href, list_label, link_map, session_lookup=None):
    rendered = md_to_html(e.body)
    linked = linkify_html(rendered, e.href, link_map)
    meta_rows = []
    # 'sessions' is rendered separately as the mentioned-in block, so skip it
    # here to avoid showing it twice. Same for the computed cross-reference
    # lists (helpers / can_help_with) — they get their own rendering below.
    skip = {"name", "aliases", "summary", "transcript", "has_notes",
            "has_transcript", "date", "status_class", "section", "sessions",
            "helpers", "can_help_with"}
    for k, v in e.meta.items():
        if k in skip:
            continue
        if isinstance(v, list):
            v = ", ".join(v)
        if not v:
            continue
        label = k.replace("_", " ").title()
        val_html = linkify_html(html.escape(v), e.href, link_map)
        meta_rows.append(
            f'<div class="meta-row"><span class="meta-label">{html.escape(label)}:</span> '
            f'<span class="meta-value">{val_html}</span></div>'
        )
    meta_block = (f'<aside class="meta-block">{"".join(meta_rows)}</aside>'
                  if meta_rows else "")

    sessions_block = _render_mentioned_in(
        _extract_session_dates(e.meta.get("sessions")),
        session_lookup or {},
    )

    # Cross-reference by expertise (populated by _attach_item_expertise):
    #   items get "Who could help" (NPCs with matching expertise)
    #   NPCs get "Could help with" (items whose expertise_needed matches)
    helpers_block = _render_expertise_link_block(
        "Who could help", e.meta.get("helpers") or [])
    can_help_block = _render_expertise_link_block(
        "Could help with", e.meta.get("can_help_with") or [])

    body = f"""<article class="detail">
  <h1>{html.escape(e.name)}</h1>
  {sessions_block}
  {helpers_block}
  {can_help_block}
  {meta_block}
  <div class="detail-body">
  {linked}
  </div>
</article>"""
    bc = f'<a href="{list_href}">{html.escape(list_label)}</a> &rsaquo; {html.escape(e.name)}'
    return page(e.name, body, current_nav=list_href, breadcrumb=bc)


ITEM_STATUS_ORDER = ["Unresolved", "Active", "Consumed", "Lost", "Sold"]
ITEM_STATUS_CLASS = {
    "Unresolved": "unresolved",
    "Active":     "active",
    "Consumed":   "completed",
    "Lost":       "completed",
    "Sold":       "completed",
}


def item_list_page(items, link_map):
    """Group items by status, unresolved first so mysteries lead."""
    grouped = {}
    for it in items:
        status = it.meta.get("status", "Active")
        if isinstance(status, list):
            status = status[0] if status else "Active"
        grouped.setdefault(status, []).append(it)

    chunks = [
        '<h1>The Ledger</h1>',
        '<p class="subhead"><em>Everything the crew has hauled ashore. Unresolved mysteries lead.</em></p>',
    ]
    order = ITEM_STATUS_ORDER + [s for s in grouped if s not in ITEM_STATUS_ORDER]
    for status in order:
        bucket = grouped.get(status, [])
        if not bucket:
            continue
        cls = ITEM_STATUS_CLASS.get(status, "active")
        chunks.append(
            f'<h2 class="status-heading"><span class="status-chip status-{cls}">{html.escape(status)}</span></h2>'
        )
        chunks.append('<ul class="item-list">')
        for it in sorted(bucket, key=lambda x: x.name.lower()):
            holder = it.meta.get("holder", "")
            if isinstance(holder, list):
                holder = ", ".join(holder)
            typ = it.meta.get("type", "")
            if isinstance(typ, list):
                typ = typ[0] if typ else ""
            meta_bits = []
            if typ:
                meta_bits.append(f'<span class="item-type">{html.escape(typ)}</span>')
            if holder:
                meta_bits.append(f'<span class="item-holder">held by {html.escape(holder)}</span>')
            meta_line = f'<span class="item-meta">{" · ".join(meta_bits)}</span>' if meta_bits else ""
            summary = md_inline(it.summary or "")
            chunks.append(
                f'<li><a class="item-name" href="{it.href}">{html.escape(it.name)}</a>'
                f'{meta_line}'
                f'<p class="item-blurb">{summary}</p></li>'
            )
        chunks.append('</ul>')

    body = "\n".join(chunks)
    return page("Items", linkify_html(body, "items.html", link_map),
                current_nav="items.html")


def quest_list_page(quests, link_map):
    order = ["Active — main arc", "Active — lead", "Active — region",
             "Unresolved", "Completed"]
    grouped = {}
    for q in quests:
        grouped.setdefault(q.status, []).append(q)
    chunks = ["<h1>Quest Log</h1>"]
    for status in order:
        items = grouped.get(status, [])
        if not items:
            continue
        status_class = items[0].meta.get("status_class", "active")
        chunks.append(
            f'<h2 class="status-heading"><span class="status-chip status-{status_class}">{html.escape(status)}</span></h2>')
        chunks.append("<ul class='quest-list'>")
        for q in items:
            helps = q.meta.get("helps") or []
            supported_by = q.meta.get("supported_by") or []
            dep_lines = []
            if helps:
                links = " · ".join(
                    f'<a href="{d.href}">{html.escape(d.name)}</a>'
                    for d in helps
                )
                dep_lines.append(
                    f'<span class="quest-dep quest-dep-helps">'
                    f'<span class="dep-arrow">&rarr;</span> helps: {links}'
                    f'</span>'
                )
            if supported_by:
                links = " · ".join(
                    f'<a href="{d.href}">{html.escape(d.name)}</a>'
                    for d in supported_by
                )
                dep_lines.append(
                    f'<span class="quest-dep quest-dep-supports">'
                    f'<span class="dep-arrow">&larr;</span> steps toward this: {links}'
                    f'</span>'
                )
            deps_html = (
                f'<div class="quest-list-deps">{"".join(dep_lines)}</div>'
                if dep_lines else ""
            )
            chunks.append(
                f'<li><a href="{q.href}"><strong>{html.escape(q.name)}</strong></a> — '
                f'{md_inline(q.summary or "")}{deps_html}</li>'
            )
        chunks.append("</ul>")
    body = "\n".join(chunks)
    return page("Quests", linkify_html(body, "quests.html", link_map),
                current_nav="quests.html")


def _render_dep_line(label, arrow_class, deps):
    """Render one directional dependency line, e.g.
       → Helps achieve: [Reach the Oracle]"""
    if not deps:
        return ""
    links = ", ".join(
        f'<a href="{d.href}">{html.escape(d.name)}</a>'
        for d in deps
    )
    return (
        f'<p class="dep-line">'
        f'<span class="dep-arrow {arrow_class}">&rarr;</span> '
        f'<span class="dep-label">{html.escape(label)}:</span> {links}'
        f'</p>'
    )


def detail_page_quest(q, link_map, session_lookup=None):
    rendered = md_to_html(q.body)
    linked = linkify_html(rendered, q.href, link_map)
    status_class = q.meta.get("status_class", "active")
    chip = f'<span class="status-chip status-{status_class}">{html.escape(q.status or "")}</span>'

    helps = q.meta.get("helps") or []
    supported_by = q.meta.get("supported_by") or []
    deps_html = ""
    if helps or supported_by:
        forward = _render_dep_line("Helps achieve", "dep-forward", helps)
        backward = _render_dep_line("Steps toward this", "dep-backward",
                                    supported_by)
        deps_html = f'<aside class="quest-deps">{forward}{backward}</aside>'

    # Quests carry their session dates inline in the body as (YYYY-MM-DD)
    # parentheticals, so extract from there rather than a frontmatter field.
    session_dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", q.body or "")
    sessions_block = _render_mentioned_in(session_dates, session_lookup or {})

    body = f"""<article class="detail">
  <h1>{html.escape(q.name)}</h1>
  <p class="meta-line">{chip} <span class="muted">{html.escape(q.meta.get("section", ""))}</span></p>
  {sessions_block}
  {deps_html}
  <div class="detail-body">
  {linked}
  </div>
</article>"""
    bc = f'<a href="quests.html">Quests</a> &rsaquo; {html.escape(q.name)}'
    return page(q.name, body, current_nav="quests.html", breadcrumb=bc)


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
}


def session_list_page(sessions, locations, link_map):
    loc_by_slug = {l.slug: l for l in locations}
    rows = []
    for s in sorted(sessions, key=lambda x: x.meta.get("date", x.slug), reverse=True):
        date = s.meta.get("date", s.slug)
        loc_slugs = SESSION_LOCATIONS.get(date, [])
        loc_chips = []
        for slug in loc_slugs:
            loc = loc_by_slug.get(slug)
            if loc:
                loc_chips.append(
                    f'<a class="session-row-loc" href="{loc.href}">{html.escape(loc.name)}</a>'
                )
        if not loc_chips:
            loc_chips.append(
                '<span class="session-row-loc session-row-loc-none">—</span>'
            )
        locs_html = "".join(loc_chips)
        audio_badge = ('<span class="session-row-audio" title="Audio recap available" aria-label="Audio recap available">&#9836;</span>'
                       if s.meta.get("has_audio") else '')
        rows.append(f"""
<li class="session-row">
  <div class="session-row-meta">
    <div class="session-row-date-line">
      <a class="session-row-date" href="{s.href}">{html.escape(date)}</a>{audio_badge}
    </div>
    <div class="session-row-locs">{locs_html}</div>
  </div>
  <p class="session-row-summary">{html.escape(s.summary or "")}</p>
</li>""")
    body = ('<h1>Sessions</h1>\n'
            '<p class="subhead"><em>Newest to oldest. Click a date to read the full account.</em></p>\n'
            '<p class="podcast-cta"><span class="copy-feed-wrap">'
            f'<a href="feed.xml" class="podcast-link js-copy-feed" data-feed-url="{SITE_BASE_URL}/feed.xml">'
            '<span aria-hidden="true">&#9836;</span> Subscribe to the podcast'
            '</a></span> <span class="podcast-cta-tail">— copies the feed link so you can paste it into your podcast app of choice.</span></p>\n'
            '<ol class="session-log">' + "".join(rows) + '</ol>')
    return page("Sessions", linkify_html(body, "sessions.html", link_map),
                current_nav="sessions.html")


def _inject_beat_images(summary_html: str, date: str, beat_images: dict) -> str:
    """After each <h2>Title</h2> in the rendered summary, insert a
    <figure class="beat-image beat-{right,left}"> if we have an image whose
    slug matches slugify(title). Alternates float side for a book feel."""
    if not beat_images:
        return summary_html

    pattern = re.compile(r"(<h2>)(.*?)(</h2>)", re.DOTALL)
    side_iter = iter(["beat-right", "beat-left"] * 20)

    def replace(m):
        opener, inner, closer = m.groups()
        # inner is already HTML — strip tags AND unescape entities
        # (linkified h2s carry <a>…</a> and apostrophes render as &#x27;).
        title_text = re.sub(r"<[^>]+>", "", inner)
        title_text = html.unescape(title_text).strip()
        slug = slugify(title_text)
        img_path = beat_images.get(slug)
        if not img_path:
            return m.group(0)
        side = next(side_iter)
        img_name = img_path.name
        return (
            f'{opener}{inner}{closer}'
            f'<figure class="beat-image {side}">'
            f'<img src="images/sessions/{date}/{html.escape(img_name)}" '
            f'alt="{html.escape(title_text)}" loading="lazy">'
            f'</figure>'
        )

    return pattern.sub(replace, summary_html)


def detail_page_session(s, link_map):
    summary_md = s.meta.get("summary_md", "")
    summary_html = (md_to_html(summary_md) if summary_md
                    else "<p><em>No summary available for this session.</em></p>")
    summary_html = _inject_beat_images(
        summary_html, s.meta.get("date", s.slug),
        s.meta.get("beat_images") or {},
    )

    note_text = s.body or ""
    notes_section = ""
    if note_text:
        notes_section = f"""
<section class="session-notes">
  <details>
    <summary>Original session notes (Fiz's POV)</summary>
    <div class="notes-body">{md_to_html(note_text)}</div>
  </details>
</section>"""

    transcript_text = s.meta.get("transcript", "")
    transcript_blocks = chunk_transcript(transcript_text)
    if transcript_blocks:
        ts_inner = "".join(f"<p>{html.escape(p)}</p>" for p in transcript_blocks)
        ts_section = f"""
<section class="raw-transcript">
  <details>
    <summary>Raw transcript ({len(transcript_blocks)} chunks of auto-transcribed audio)</summary>
    <p class="muted small">Lightly chunked. Expect overlap with table chatter.</p>
    <div class="transcript-body">{ts_inner}</div>
  </details>
</section>"""
    else:
        ts_section = ""

    audio_html = ""
    if s.meta.get("has_audio"):
        audio_name = s.meta.get("audio_name", f"{s.meta.get('date', s.slug)}.mp3")
        audio_html = (
            f'  <figure class="session-audio">\n'
            f'    <figcaption><span class="session-audio-badge no-link">Tales of the True Hand</span>'
            f' <span class="session-audio-caption no-link">Listen to this session as told by Vandal Lovelace.</span></figcaption>\n'
            f'    <audio controls preload="none" src="audio/sessions/{html.escape(audio_name)}"></audio>\n'
            f'  </figure>\n'
        )

    hero_html = ""
    if s.meta.get("has_image"):
        img_name = s.meta.get("image_name", f"{s.meta.get('date', s.slug)}.jpg")
        hero_html = (
            f'  <figure class="session-hero">'
            f'<img src="images/sessions/{html.escape(img_name)}" '
            f'alt="Illustration for {html.escape(s.name)}" loading="lazy">'
            f'</figure>\n'
        )

    carried = s.meta.get("carried") or []
    carried_html = ""
    if carried:
        items = "".join(f'<li>{md_inline(it)}</li>' for it in carried)
        carried_html = f"""
  <aside class="carried">
    <h2>Items acquired</h2>
    <ul>{items}</ul>
  </aside>
"""

    body = f"""<article class="detail">
  <h1>{html.escape(s.name)}</h1>
{audio_html}{hero_html}{carried_html}  <section class="session-summary">
  {summary_html}
  </section>
  {notes_section}
  {ts_section}
</article>"""
    body = linkify_html(body, s.href, link_map)
    bc = f'<a href="sessions.html">Sessions</a> &rsaquo; {html.escape(s.name)}'
    return page(s.name, body, current_nav="sessions.html", breadcrumb=bc)


# --------------------------------------------------------------------------
# podcast RSS feed
# --------------------------------------------------------------------------

def _mp3_duration_seconds(path):
    """Best-effort MP3 duration via ffprobe. Returns int seconds, or 0."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=15, check=True,
        ).stdout.strip()
        return int(float(out))
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
            FileNotFoundError, ValueError):
        return 0


def _hms(seconds):
    if seconds <= 0:
        return "00:00"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _extract_in_brief(summary_md):
    for ln in (summary_md or "").split("\n"):
        s = ln.strip()
        if s.startswith("*In brief:") and s.endswith("*"):
            return s[len("*In brief:"):-1].strip()
    return ""


# Cache for the parsed audio-library credits so we only read CREDITS.md once.
_AUDIO_CREDITS_CACHE = None


def _parse_audio_credits():
    """Parse summaries/audio/library/CREDITS.md into a list of asset dicts.

    Each asset is a ``## <name>`` section carrying a ``**License**:`` line.
    We split the required-attribution assets (CC-BY and friends, whose license
    is a license condition) from the voluntary ones (Pixabay Content License,
    where attribution is a courtesy, not a requirement).

    Returns a dict with two lists of plain-text credit strings:
      {"required": [...], "voluntary": [...]}
    Both are ordered as they appear in CREDITS.md.
    """
    global _AUDIO_CREDITS_CACHE
    if _AUDIO_CREDITS_CACHE is not None:
        return _AUDIO_CREDITS_CACHE

    result = {"required": [], "voluntary": []}
    try:
        text = AUDIO_CREDITS_FILE.read_text(encoding="utf-8")
    except OSError:
        _AUDIO_CREDITS_CACHE = result
        return result

    # Split into ``## <name>`` sections (skip the file's own preamble).
    sections = re.split(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    # re.split with one capture group yields: [preamble, name1, body1, name2, body2, ...]
    for i in range(1, len(sections), 2):
        name = sections[i].strip()
        body = sections[i + 1] if i + 1 < len(sections) else ""

        lic_m = re.search(r"^\s*[-*]\s*\*\*License\*\*:\s*(.+?)\s*$",
                          body, flags=re.MULTILINE)
        license_line = lic_m.group(1).strip() if lic_m else ""
        # Strip markdown link syntax <...> from the trailing license URL.
        license_line = re.sub(r"\s*—\s*<[^>]+>\s*$", "", license_line).strip()

        # Attribution is required when the license itself demands it. Pixabay's
        # Content License does not; Creative Commons "Attribution" (CC BY) does.
        requires = bool(re.search(r"attribution", license_line, re.IGNORECASE)) \
            and "pixabay" not in license_line.lower()

        if requires:
            # Pull the required-attribution blockquote (the ``> ...`` lines that
            # follow the "Required attribution wording" note).
            quote_lines = []
            capture = False
            for ln in body.split("\n"):
                if re.search(r"required attribution wording", ln, re.IGNORECASE):
                    capture = True
                    continue
                if capture:
                    m = re.match(r"^\s*>\s?(.*)$", ln)
                    if m:
                        if m.group(1).strip():
                            quote_lines.append(m.group(1).strip())
                    elif quote_lines:
                        break
            wording = " — ".join(quote_lines) if quote_lines else name
            result["required"].append(f"{wording}  (used in {name})")
        else:
            # Voluntary credit: use the plain-text fallback line if present.
            fb_m = re.search(r"Plain-text fallback:\s*\*?(.+?)\*?\s*$",
                             body, flags=re.MULTILINE)
            if fb_m:
                result["voluntary"].append(fb_m.group(1).strip().rstrip("."))

    _AUDIO_CREDITS_CACHE = result
    return result


def _audio_credits_text():
    """Human-readable attribution block appended to every podcast episode.

    CC-BY (and similar) assets carry their license-mandated attribution wording;
    Pixabay assets get a single courtesy roll-up line (attribution not required).
    Returns a plain-text string (no trailing newline) or "" if nothing to credit.
    """
    credits = _parse_audio_credits()
    lines = []
    if credits["required"] or credits["voluntary"]:
        lines.append("Music & SFX credits:")
    for c in credits["required"]:
        lines.append(f"• {c}")
    if credits["voluntary"]:
        lines.append("Additional sound effects & ambience (Pixabay Content "
                     "License, attribution not required): "
                     + "; ".join(credits["voluntary"]) + ".")
    return "\n".join(lines)


def podcast_feed(sessions):
    channel_title = "Tales of the True Hand"
    channel_desc = ("Weekly recaps of the Crew of the True Hand — a D&D 5e "
                    "campaign following Storm King's Thunder — told by "
                    "Vandal Lovelace, bard and hearth-storyteller.")
    channel_link = f"{SITE_BASE_URL}/sessions.html"
    feed_url = f"{SITE_BASE_URL}/feed.xml"
    cover_url = f"{SITE_BASE_URL}/images/podcast-cover.jpg"

    with_audio = [s for s in sessions if s.meta.get("has_audio")]
    with_audio.sort(key=lambda x: x.meta.get("date", x.slug), reverse=True)

    # License-mandated + courtesy attribution for the shared audio library.
    # The music/SFX library is common to every episode, so the same credit
    # block is carried on every item's <description>/<content:encoded>.
    credits_text = _audio_credits_text()
    credits = _parse_audio_credits()

    items_xml = []
    latest_pub = None
    for s in with_audio:
        date = s.meta.get("date", s.slug)
        audio_name = s.meta.get("audio_name") or f"{date}.mp3"
        audio_path = s.meta.get("audio_src")
        try:
            size = audio_path.stat().st_size if audio_path else 0
        except OSError:
            size = 0
        duration = _mp3_duration_seconds(audio_path) if audio_path else 0

        subtitle = s.meta.get("audio_subtitle") or ""
        ep_title = f"{date} — {subtitle}" if subtitle else f"{date}"
        in_brief = _extract_in_brief(s.meta.get("summary_md", ""))
        ep_blurb = in_brief or (s.summary or "")
        # Plain-text description carries the blurb + the credits block.
        ep_desc = ep_blurb
        if credits_text:
            ep_desc = f"{ep_blurb}\n\n{credits_text}" if ep_blurb else credits_text

        # Richer HTML variant for readers that honour <content:encoded>.
        content_html_parts = []
        if ep_blurb:
            content_html_parts.append(f"<p>{html.escape(ep_blurb)}</p>")
        if credits["required"] or credits["voluntary"]:
            content_html_parts.append("<p><strong>Music &amp; SFX credits:</strong></p>")
            if credits["required"]:
                lis = "".join(
                    f"<li>{html.escape(c)}</li>" for c in credits["required"]
                )
                content_html_parts.append(f"<ul>{lis}</ul>")
            if credits["voluntary"]:
                vol = "; ".join(html.escape(v) for v in credits["voluntary"])
                content_html_parts.append(
                    "<p>Additional sound effects &amp; ambience (Pixabay Content "
                    f"License, attribution not required): {vol}.</p>"
                )
        content_html = "".join(content_html_parts)

        try:
            y, m, d = [int(x) for x in date.split("-")]
            pub_dt = _dt.datetime(y, m, d, 12, 0, 0, tzinfo=_dt.timezone.utc)
        except (ValueError, TypeError):
            pub_dt = _dt.datetime.now(_dt.timezone.utc)
        pub_str = format_datetime(pub_dt)
        if latest_pub is None or pub_dt > latest_pub:
            latest_pub = pub_dt

        episode_page = f"{SITE_BASE_URL}/{s.href}"
        enclosure_url = f"{SITE_BASE_URL}/audio/sessions/{audio_name}"
        guid = enclosure_url

        item_image = ""
        if s.meta.get("has_image"):
            img_name = s.meta.get("image_name") or f"{date}.jpg"
            item_image = (
                f'    <itunes:image href="{SITE_BASE_URL}/images/sessions/{html.escape(img_name)}"/>\n'
            )

        items_xml.append(f"""  <item>
    <title>{html.escape(ep_title)}</title>
    <link>{html.escape(episode_page)}</link>
    <guid isPermaLink="false">{html.escape(guid)}</guid>
    <pubDate>{pub_str}</pubDate>
    <description>{html.escape(ep_desc)}</description>
    <itunes:summary>{html.escape(ep_desc)}</itunes:summary>
    <content:encoded><![CDATA[{content_html}]]></content:encoded>
    <itunes:duration>{_hms(duration)}</itunes:duration>
    <itunes:explicit>false</itunes:explicit>
    <itunes:episodeType>full</itunes:episodeType>
{item_image}    <enclosure url="{html.escape(enclosure_url)}" length="{size}" type="audio/mpeg"/>
  </item>""")

    last_build = format_datetime(latest_pub or _dt.datetime.now(_dt.timezone.utc))

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
  <title>{html.escape(channel_title)}</title>
  <link>{html.escape(channel_link)}</link>
  <atom:link href="{html.escape(feed_url)}" rel="self" type="application/rss+xml"/>
  <language>en-us</language>
  <description>{html.escape(channel_desc)}</description>
  <itunes:summary>{html.escape(channel_desc)}</itunes:summary>
  <itunes:author>Vandal Lovelace</itunes:author>
  <itunes:owner>
    <itunes:name>Crew of the True Hand</itunes:name>
    <itunes:email>noreply@crew-of-the-true-hand.local</itunes:email>
  </itunes:owner>
  <itunes:image href="{html.escape(cover_url)}"/>
  <itunes:category text="Leisure">
    <itunes:category text="Games"/>
  </itunes:category>
  <itunes:explicit>false</itunes:explicit>
  <itunes:type>episodic</itunes:type>
  <lastBuildDate>{last_build}</lastBuildDate>
{chr(10).join(items_xml)}
</channel>
</rss>
"""


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    pcs = load_pcs()
    npcs = load_dir_entities("npc", NPC_DIR)
    locations = load_dir_entities("location", LOC_DIR)
    items = load_dir_entities("item", ITEM_DIR)
    quests = load_quests()
    _attach_quest_deps(quests)
    _attach_item_expertise(items, npcs)
    sessions = load_sessions()
    session_lookup = {s.slug: s for s in sessions}

    all_entities = pcs + npcs + locations + items + quests + sessions
    link_map = build_link_map(all_entities)

    setup_output()

    write_page("index.html", index_page(pcs, npcs, locations, quests, sessions))

    write_page("characters.html", pc_list_page(pcs, link_map))
    for pc in pcs:
        write_page(pc.href, detail_page_pc(pc, link_map))

    write_page("npcs.html", npc_table_page(npcs, link_map))
    for e in npcs:
        write_page(e.href, detail_page_generic(
            e, "npcs.html", "NPCs", link_map, session_lookup))

    write_page("locations.html", locations_chart_page(locations, link_map))
    for e in locations:
        write_page(e.href, detail_page_generic(
            e, "locations.html", "Locations", link_map, session_lookup))

    write_page("items.html", item_list_page(items, link_map))
    for e in items:
        write_page(e.href, detail_page_generic(
            e, "items.html", "Items", link_map, session_lookup))

    write_page("quests.html", quest_list_page(quests, link_map))
    for q in quests:
        write_page(q.href, detail_page_quest(q, link_map, session_lookup))

    write_page("sessions.html", session_list_page(sessions, locations, link_map))
    for s in sessions:
        write_page(s.href, detail_page_session(s, link_map))

    write_page("feed.xml", podcast_feed(sessions))
    n_episodes = sum(1 for s in sessions if s.meta.get("has_audio"))
    print(f"  Podcast feed: /feed.xml with {n_episodes} episodes")

    total = 7 + len(pcs) + len(npcs) + len(locations) + len(items) + len(quests) + len(sessions)
    print(f"Generated {total} pages into {SITE}")
    print(f"  PCs: {len(pcs)}, NPCs: {len(npcs)}, Locations: {len(locations)},"
          f" Items: {len(items)}, Quests: {len(quests)}, Sessions: {len(sessions)}")


if __name__ == "__main__":
    main()
