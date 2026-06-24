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
