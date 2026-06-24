# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A D&D 5e campaign archive for **Crew of the True Hand** — the player-side notes for a long-running campaign that appears to follow the *Storm King's Thunder* storyline (Nightstone → Triboar/Golden Fields → Waterdeep → Spine of the World, hunting the Oracle and dealing with rampaging giants). There is no code, no build, and no git history; tasks here are documentation work: writing/expanding notes, summarizing transcripts, maintaining character sheets, and answering lore/continuity questions.

## Layout

- `characters/` — One markdown file per PC plus a portrait `.jpeg`. The party is four PCs:
  - **Fiz** (Hisfiz Spinfizzler) — Rock Gnome Artificer/Artillerist, from Halruaa, stole a flying ship.
  - **Hal** (Hal Stormguard) — Variant Human Paladin, Oath of Vengeance, ex-Silver Marches militia.
  - **Toz** (Tozlo Greenbottle) — Lightfoot Halfling Storm Sorcerer, captain of the (wrecked) *True Hand*, adopted brother to Woz.
  - **Woz** (Enoril Wazek) — Half-Elf Nature Cleric of Eldath, raised in the wild, adopted by the Greenbottles.
  - Character files are structured as: header block (race/class/background/alignment/age) → `## Backstory` → `## Class Features` with per-feature stat blocks copied from sourcebook references (PHB / TCoE / SCAG with page numbers). Preserve this structure when editing.
- `session notes/` — Terse bullet-style recaps named `YYYY-MM-DD.md` for the real-world session date. Each file is a few lines to a couple dozen, often shorthand ("kill them", "up to level four"). **Written from Fiz's perspective** — first-person "I" / "me" refers to Fiz, so loot or interactions phrased that way belong to Fiz unless another PC is named. Fiz sometimes refers to himself in the third person when paired with another PC ("Toz and Fiz go in village", "Hal and Fiz talk to Naxine"), so third-person Fiz mentions are not a different narrator. Do not rewrite these into prose unless asked — the terseness is the style.
- `transcripts/` — Raw auto-transcribed audio of sessions as `YYYY-MM-DD.txt`. These are large (80–120KB), unpunctuated walls of speech with no speaker tags, and contain a lot of table chatter, dice rolls, and mechanics talk mixed with in-character dialogue. **The session-notes date may not match the transcript date** (e.g. the 2025-12-17 notes summarize that session, but `transcripts/2025-12-17.txt` is the raw recording of that same evening). Use transcripts as source-of-truth when expanding or reconciling notes, but expect signal-to-noise issues.
- `summaries/` — Generated detailed session recaps as `YYYY-MM-DD.md`. Each file leads with an italic `*In brief: ...*` line, then `##` sections, then `## What's next` / `## Loose ends`. These are derived from the corresponding session notes + transcript and are the **primary content of the session detail pages on the website**. Notes and transcripts stay around as collapsible reference material on the same page. When a new session is added, generate a new summary file (or hand-write one) so the website has something rich to render.
- `npcs/` and `locations/` — One markdown file per entity, each with frontmatter (`name`, `aliases`, `type`, `location`, `first_seen`, etc.) and a short markdown body. These are the source of truth for everyone/everywhere the website knows about.
- `quests.md` — Single-file quest log; the website parses each `- **Name**` bullet under each `## section` as a quest. Section headings determine status (Main arc / Allies / Hotspots / Side leads / Personal / Completed).
- `website/` — Static site generator (`generate.py`, stdlib only) plus theme CSS. Run `python3 website/generate.py` to regenerate `website/site/` after any source change. See `website/README.md` for the full file format and cross-linking rules.

## Working in this repo

- When summarizing a transcript into session notes, match the existing terse, bullet/short-paragraph voice rather than producing a polished prose recap.
- Keep proper-noun spellings consistent across files; the notes are inconsistent in places (e.g. "Nighstone" vs "Nightstone", "Halrua" vs "Halruaa") — don't silently "correct" a name without checking how it's spelled elsewhere first, because some are typos and some are deliberate.
- Class-feature blocks in character files quote sourcebook page numbers (e.g. `(TCoE, pg. 13)`); preserve these citations when editing.
- Transcripts are too large to read whole — use `Read` with `offset`/`limit` or `grep` for specific names/events rather than loading them in full.
- After adding a new session note, transcript, NPC, location, or quest, re-run `python3 website/generate.py` so the site picks it up. The generator wipes `website/site/` and rebuilds from scratch — never hand-edit files under `website/site/`.
- New NPCs and locations: add a single `.md` file with frontmatter (see `website/README.md` for the schema). Always include `aliases:` with every phrasing that should auto-link to that entity, including the canonical name.

## Adding a new session

When new session material arrives (notes from the player, a fresh transcript, or both), the steps are always the same. Follow them in order — the site won't look right until the summary exists and the location annotation is set.

### 1. Drop the raw sources

Use the real-world date as `YYYY-MM-DD`:
- `session notes/YYYY-MM-DD.md` if the player produced bullet notes (Fiz's POV). Optional.
- `transcripts/YYYY-MM-DD.txt` if there is an audio transcript (Whisper-style, no speaker tags, ~80–120KB). Optional.

At least one of the two must exist. If both are missing there is no session to render.

### 2. Generate the detailed summary

Write `summaries/YYYY-MM-DD.md`. This file is the **primary content** of the session's detail page on the site and the source of the `*In brief: ...*` line that becomes the row blurb on `sessions.html`.

Required format:
- Lead line: `*In brief: <one sentence>*` — this single sentence becomes the row blurb. Keep it under ~30 words and make it evocative, not generic.
- 3–5 `##` section headings for the major beats. Pick headings that reflect what actually happened that session — do not use a fixed template.
- Past-tense third-person narrative voice ("The crew…", "Fiz…", "Hal…"). Convert any first-person Fiz POV from the notes to third person. Slightly old-salt nautical tone where it lands naturally; don't force it.
- Close with `## What's next` or `## Loose ends` — bullet list of leads, unresolved threads, or where the party is headed.
- Length target: **500–800 words** when a transcript exists; 300–500 when only notes are available.

How to draw on each source:
- **Transcripts are too large to read whole.** Use `Read` with `offset`/`limit` (200-line chunks), and `grep` via Bash to find proper-noun anchors (NPC names, place names, "giant", "dragon", anything you saw in the notes or expect from the prior session's arc). Skip table chatter — dice talk, jokes about real-world stuff, "let's take a break". Focus on in-fiction events.
- **For sessions that have only a transcript** (no notes), still produce the same format. The summary is the only narrative anchor.
- **For sessions that have only notes** (no transcript), the summary will be shorter — that's fine. Just expand the notes into prose without inventing events.

Cross-references:
- Consult `npcs/` and `locations/` for canonical spellings before writing a name. Some "wrong" spellings in the notes are deliberate; check before "correcting" anything.
- If the session introduces new NPCs or locations, add `.md` files for them too (see step 4).

When uncertain, consider spawning a parallel `general-purpose` Agent per transcript-bearing session — pattern proven on the existing summaries. Brief the agent with: the campaign context, the four PCs, the session date, the file paths, the format above, and "return the markdown content directly — no preamble." Write the agent's returned text to disk yourself.

### 3. Add the session's location annotation

Open `website/generate.py` and find `SESSION_LOCATIONS` (near `session_list_page`). Add an entry mapping the new date to a list of location slugs in order of importance:

```python
SESSION_LOCATIONS = {
    ...
    "YYYY-MM-DD": ["golden-fields"],          # or ["nightstone", "ardeep-forest"]
    ...
}
```

- Use the location's slug (matches the filename in `locations/` minus `.md`).
- An empty list (`[]`) means the session was in transit / no fixed place — the row will show a dashed em-dash chip.
- If the session names a *new* location not yet in `locations/`, add the file first (see step 4) so the chip becomes a working link.

### 4. Add any new NPCs, locations, and quest updates

Pass through the summary one more time and check:
- **New NPCs introduced?** Add `npcs/<slug>.md` files. Include `aliases:` covering every phrasing that should auto-link (including the canonical name).
- **New locations visited or named?** Add `locations/<slug>.md` files. If the location should appear on the chart on `locations.html`, also add a `"<slug>": {"x": ..., "y": ...}` entry to `LOCATION_MAP_DATA` in `website/generate.py`.
- **New leads, completed objectives, or quest status changes?** Edit `quests.md`. The website parses each `- **Name**` bullet under each `## section`; section headings determine status.

### 5. Regenerate the site

```bash
python3 website/generate.py
```

The generator wipes `website/site/` and rebuilds from scratch — never hand-edit files under `website/site/`. Verify by opening `website/site/sessions.html` in a browser: the new row should appear at the top (newest first) with the right date, the right location chips, and the `*In brief:*` line as the row blurb. The new session's detail page (`session-YYYY-MM-DD.html`) should render the full summary with the original notes and raw transcript available as collapsible blocks below.

### 6. Deploy (when ready)

`./website/migrations/001-create-s3-bucket.sh` re-syncs the site to the S3 bucket. The first four steps of that script are idempotent-ish and the file-sync step (`aws s3 sync ... --delete`) handles incremental updates correctly. Only run this when the user asks; do not deploy on every regeneration.
