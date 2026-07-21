# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A D&D 5e campaign archive for **Crew of the True Hand** — the player-side notes for a long-running campaign that appears to follow the *Storm King's Thunder* storyline (Nightstone → Triboar/Golden Fields → Waterdeep → Spine of the World, hunting the Oracle and dealing with rampaging giants). There is no code, no build, and no git history; tasks here are documentation work: writing/expanding notes, summarizing transcripts, maintaining character sheets, and answering lore/continuity questions.

## Layout

- `characters/` — One markdown file per PC plus a portrait `.jpeg`. The party is four PCs:
  - **Fiz** (Hisfiz Spinfizzler) — Rock Gnome Artificer/Artillerist, from Halruaa, stole a flying ship.
  - **Hal** (Hal Stormguard) — Variant Human Paladin, Oath of Vengeance, ex-Silver Marches militia.
  - **Toz** (Tozlo Greenbottle) — Lightfoot Halfling Storm Sorcerer, captain of the (wrecked) *True Hand*; his family adopted Eno as a brother.
  - **Eno** (Enoril Wazek) — Half-Elf Nature Cleric of Eldath, raised in the wild, adopted by the Greenbottles.
  - Character files are structured as: header block (race/class/background/alignment/age) → `## Backstory` → `## Class Features` with per-feature stat blocks copied from sourcebook references (PHB / TCoE / SCAG with page numbers). Preserve this structure when editing.
- `sessions/YYYY-MM-DD/` — **All files for one session live together in this folder**, keyed by the real-world session date. Contents (all optional except that at least one of summary/transcript/notes must exist to render a page):
  - `summary.md` — Generated detailed session recap. Leads with an italic `*In brief: ...*` line, then `##` sections, then `## What's next` / `## Loose ends`. Derived from the notes + transcript and the **primary content of the session detail page on the website**. When a new session is added, generate this (or hand-write it) so the website has something rich to render.
  - `recording.m4a` — Raw session audio (git-ignored; large, ~80–90MB for a 3-hour session). The source for transcription (step 1.5). Not needed if a `transcript.txt` is supplied directly.
  - `transcript.txt` — The session transcript. New sessions are **diarized**: whisply output (step 1.5), one utterance per line as `[HH:MM:SS.mmm] [SPEAKER_0X] text`, proper nouns auto-corrected via `sessions/library/whisply-corrections.yaml`. Older sessions may still be the pre-diarization form (unpunctuated wall, no speaker tags). Machine-produced either way — expect signal-to-noise issues, and note that speaker tags **bleed badly in fast combat**. Kept as a collapsible block on the session page.
  - `transcript-distilled.md` — A complete, fact-by-fact reconstruction of the session (every action, line of dialogue, item, roll) with a speaker→character key and per-PC attribution. Far more precise than `summary.md`; the source of truth for reconciling who-did-what. Its companion `transcript-distilled.factcheck.md` is the QA worksheet (the riskiest attributions paired with transcript evidence for manual review). See step 1.5. These are references, not website artifacts.
  - `whisply/` — whisply's raw multi-format output (`recording/recording_en_annotated.txt`, `.json`, `.rttm`, `.html`); the annotated `.txt` is what gets promoted to `transcript.txt`.
  - `player notes/<pc>.md` — Terse bullet-style recaps, a few lines to a couple dozen, often shorthand ("kill them", "up to level four"). Currently only `fiz.md` exists (all notes so far are Fiz's); another PC's notes would go alongside as e.g. `hal.md`. **Fiz's are written from his perspective** — first-person "I" / "me" refers to Fiz, so loot or interactions phrased that way belong to Fiz unless another PC is named. Fiz sometimes refers to himself in the third person when paired with another PC ("Toz and Fiz go in village", "Hal and Fiz talk to Naxine"), so third-person Fiz mentions are not a different narrator. Do not rewrite these into prose unless asked — the terseness is the style. Kept as a collapsible block on the session page.
  - `images/` — Gemini-generated illustrations (see step 2.5): `hero.jpg` is the 16:9 banner; every other file is a beat illustration named `<slugified-section-title>.jpg`. Site generator copies `hero.<ext>` → `site/images/sessions/YYYY-MM-DD.<ext>` and beats → `site/images/sessions/YYYY-MM-DD/<slug>.<ext>`.
  - `audio/` — The "Tales of the True Hand" audio recap (see steps 2.7/2.8). The script AND its generated artifacts live together here:
    - `script.md` — the storyteller-voiced audio script, the **single editable source of truth** for this session's audio. Uses format `# Tales of the True Hand — YYYY-MM-DD` / `## <subtitle>` / `[COLD OPEN]` / `[TITLE]` / `## ACT ONE/TWO/…` / `## CLOSING`, with every spoken line prefixed `VANDAL: *(delivery cue)* …`. The narrator is Vandal Lovelace; he only actually met the crew at 2026-06-16, so earlier sessions are framed as retelling. Signature open: *"Well met, friend. Draw close to the fire. I am Vandal Lovelace, and this is a Tale of the True Hand."* Signature close: *"I am Vandal Lovelace. This has been a Tale of the True Hand."*
    - `final.mp3` (the stitched output, what the site plays), `manifest.json` (voice, model, per-chunk hashes for TTS cache invalidation), and `chunks/NNNN.mp3` (persistent per-speech-line TTS output — reused on re-runs so tweaking the script or music layering costs zero ElevenLabs credits unless the tweak actually changes a spoken line).
    - Site generator copies `final.mp3` → `site/audio/sessions/YYYY-MM-DD.mp3` for the podcast feed and inline player, and reads `script.md`'s line-2 `## <subtitle>` for the episode title.

  Note: the notes/transcript/summary dates historically don't always match up neatly (e.g. `2025-12-17/transcript.txt` is the raw recording that `2025-12-17/summary.md` recaps) — now that they share a folder this is moot, but the transcript can still cover an evening whose beats span the notes.
- `sessions/library/audio/` — Third-party music / SFX assets shared across every session, referenced from scripts via `[MUSIC: ...]` and `[STING: ...]` cue lines. `CREDITS.md` in that directory MUST record every asset's source, license, and attribution wording BEFORE it can be used. `NEEDED.md` tracks what's still open on the shopping list. Assets currently in place cover all Tier-1 cue slots (signature theme, hearth bed, chime, bridge, low-chord, minor swell).
  - `website/static/podcast-cover.jpg` — 1400×1400 JPEG podcast cover; regenerate with `scripts/generate-podcast-cover.py` (Gemini + Pillow). The static-asset glob copies it to `site/static/podcast-cover.jpg`; `feed.xml`'s `<itunes:image>` points there.
- `npcs/` and `locations/` — One markdown file per entity, each with frontmatter (`name`, `aliases`, `type`, `location`, `first_seen`, etc.) and a short markdown body. These are the source of truth for everyone/everywhere the website knows about. NPCs may carry an `expertise: dragons, Draconic, ...` field — the site cross-references those tags against items' `expertise_needed:` to surface "Who could help" / "Could help with" blocks on each detail page.
- `items/` — One markdown file per magical, mysterious, or narratively significant item the crew has acquired. Frontmatter: `name`, `aliases`, `type` (Magic item / Weapon / Focus / Book / Mystery / Trophy / Keepsake / Memento), `holder` (PC name or "Party"), `status` (Unresolved / Active / Consumed / Lost), `origin` (session date), and optional `expertise_needed:` tags. Everyday loot (coin, generic potions/scrolls, consumables) stays in the session's `carried:` list without getting its own file — see the criteria in the item-catalog thread.
- `quests.md` — Single-file quest log; the website parses each `- **Name**` bullet under each `## section` as a quest. Section headings determine status (Main arc / Allies / Hotspots / Side leads / Personal / Completed).
- `campaign-state.md` — Tiny hand-maintained record of the party's **current objective** and **open questions**, in YAML frontmatter (`objective:`, `open_questions:` list, optional `current_location:` slug override). It's the one bit of "where are we / what's the goal right now" the archive doesn't otherwise capture; it drives the **prep hub** (`next.html`, "Where We Left Off") and its companion **open-threads board** (`threads.html`). Current *location* is auto-derived from the most recent session's `SESSION_LOCATIONS` entry unless `current_location:` overrides it. The prep hub composes existing data (top quests, the latest recap's In-brief, each session's harvested `## What's next`/`## Loose ends` bullets, item→expert leads, NPCs at the current location, crew holdings) — no per-session generator changes needed.
- `website/` — Static site generator (`generate.py`, stdlib only) plus theme CSS. Run `python3 website/generate.py` to regenerate `website/site/` after any source change. See `website/README.md` for the full file format and cross-linking rules.
- `battle-cards/` — Printable single-page combat reference HTML cards, one per PC (`fiz.html` exists; `hal.html`, `toz.html`, `eno.html` to come). Self-contained: inline CSS, inline SVG dice, no external assets. See `battle-cards/README.md` for the layout model, dice notation, chip taxonomy, character voices, and the step-by-step recipe for building a new one. Use `fiz.html` as the working template — copy it, then swap content.
- `TODO.md` — Running list of open work across the whole archive (site, content, audio pipeline, distribution, infrastructure). Read this before proposing new features so you don't duplicate what's already scoped out; add new items here rather than sprinkling `TODO:` comments across code.

## Working in this repo

- When summarizing a transcript into session notes, match the existing terse, bullet/short-paragraph voice rather than producing a polished prose recap.
- Keep proper-noun spellings consistent across files; the notes are inconsistent in places (e.g. "Nighstone" vs "Nightstone", "Halrua" vs "Halruaa") — don't silently "correct" a name without checking how it's spelled elsewhere first, because some are typos and some are deliberate.
- Class-feature blocks in character files quote sourcebook page numbers (e.g. `(TCoE, pg. 13)`); preserve these citations when editing.
- Transcripts are too large to read whole — use `Read` with `offset`/`limit` or `grep` for specific names/events rather than loading them in full.
- After adding a new session note, transcript, NPC, location, or quest, re-run `python3 website/generate.py` so the site picks it up. The generator wipes `website/site/` and rebuilds from scratch — never hand-edit files under `website/site/`.
- New NPCs and locations: add a single `.md` file with frontmatter (see `website/README.md` for the schema). Always include `aliases:` with every phrasing that should auto-link to that entity, including the canonical name.
- Python environment: `website/generate.py` is **stdlib-only** — no install needed to build/deploy the site. The audio/image scripts under `scripts/` need third-party packages tracked in `requirements.txt` (`google-genai`, `elevenlabs`, `pillow`); set them up once with `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`. The `.venv/` is git-ignored; run those scripts via `.venv/bin/python`.

## Adding a new session

When new session material arrives (notes from the player, a fresh transcript, or both), the steps are always the same. Follow them in order — the site won't look right until the summary exists and the location annotation is set.

### 1. Drop the raw sources

Use the real-world date as `YYYY-MM-DD` and create the session folder `sessions/YYYY-MM-DD/`:
- `sessions/YYYY-MM-DD/player notes/fiz.md` if the player produced bullet notes (Fiz's POV). Optional.
- `sessions/YYYY-MM-DD/recording.m4a` if there is raw session audio — the transcript is generated from it in step 1.5. Optional.
- `sessions/YYYY-MM-DD/transcript.txt` if a transcript is supplied directly (skips step 1.5). Optional.

At least one of {recording, transcript, notes} must exist. If all are missing there is no session to render.

### 1.5. Transcribe, distill, and fact-check (when there's a recording)

Turns `recording.m4a` into the diarized `transcript.txt` plus the `transcript-distilled.md` fact record. If a `transcript.txt` was supplied directly, skip to step 2.

**Transcribe with whisply.** Use the existing venv `/Users/sean/whisply-env` (it has the `mlx-whisper` extra — a plain `pip install whisply` venv fails with "Missing dependencies for device 'mlx'"):

```
set -a && . ./.env && set +a          # loads HF_TOKEN
/Users/sean/whisply-env/bin/whisply run \
  -f sessions/YYYY-MM-DD/recording.m4a -o sessions/YYYY-MM-DD/whisply \
  --device mlx --model large-v3-turbo --language en \
  --annotate --num_speakers 8 --hf_token "$HF_TOKEN" \
  --post_correction sessions/library/whisply-corrections.yaml --export all
```

- `--annotate` runs speaker **diarization** via gated pyannote models. It needs `HF_TOKEN` in `.env` with **gated-repo read access** (a classic Read token, or fine-grained with "Read access to public gated repos" ticked) AND you must click **Agree** on `pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0`. Otherwise it 403s at the diarization stage — *after* the full transcription. Pre-flight with a quick `hf_hub_download(repo, 'config.yaml')` check before the ~13-min run.
- `--num_speakers 8`, not 5. The table is 5 people (4 PCs + DM) on one shared mic; a diarization sweep showed the true count (5) merges overlapping players in combat, while **8 keeps all four PCs on distinct clusters**. It over-splits — each PC spans ~1–2 clusters and the DM dominates one — which the distillation re-merges by content.
- `--post_correction sessions/library/whisply-corrections.yaml` auto-fixes mangled proper nouns (word-boundary, case-insensitive; `patterns:` for regex variants). Extend that file as new mis-hearings show up.

Then **promote** the annotated output and clean up whisply's scratch file:

```
cp sessions/YYYY-MM-DD/whisply/recording/recording_en_annotated.txt sessions/YYYY-MM-DD/transcript.txt
rm -f sessions/YYYY-MM-DD/recording_converted.wav   # ~350MB scratch whisply leaves behind
```

**Distill.** Spawn an Opus `general-purpose` Agent to write `sessions/YYYY-MM-DD/transcript-distilled.md` — a complete, chronological, fact-by-fact account (every action, line, item, roll) with per-PC attribution. Brief it with: the campaign context and the four PCs' **class-mechanic fingerprints** (Fiz = Artificer/Artillerist; Hal = Paladin, **Extra Attack + javelins**; Toz = Storm Sorcerer, **Tempestuous Magic / gust of wind / Shape Water / light crossbow**; Eno = Nature Cleric, **Spirit Guardians / Shillelagh / Dampen Elements / Healing Word**); the K=8 over-split note (build a **many-to-one cluster→character map** from content, DM dominant on one cluster + a bleed cluster, two PCs split across two clusters each); and the rule that **in combat the tags bleed badly — cross-check every attribution against class mechanics (Extra Attack, weapon type, spell list), which win over the raw tag.** Feed it `transcript.txt`, `player notes/fiz.md`, and (on a re-pass) the prior distilled file as an event-completeness reference.

**Fact-check.** The distillation also emits `sessions/YYYY-MM-DD/transcript-distilled.factcheck.md` — the 12–15 riskiest "who did what" claims (combat/overlap first, then skill checks), each with its `[timestamp] [SPEAKER_0X]` transcript evidence and a blank ✔/✘ column. Hand it to the user; they mark ✘ on anything wrong; apply their corrections back into `transcript-distilled.md`. This systematically catches the mis-attributions diarization makes in fast combat (on 2026-06-16 the javelin, crossbow, and Shape Water calls were all initially wrong).

Write the summary (step 2) **from** `transcript-distilled.md` when it exists — its attributions are the reconciled truth.

### 2. Generate the detailed summary

Write `sessions/YYYY-MM-DD/summary.md`. This file is the **primary content** of the session's detail page on the site and the source of the `*In brief: ...*` line that becomes the row blurb on `sessions.html`.

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

### 2.5. Generate a hero image (optional)

```
python3 scripts/generate-session-image.py YYYY-MM-DD           # hero + all beats
python3 scripts/generate-session-image.py YYYY-MM-DD --hero    # hero only
python3 scripts/generate-session-image.py YYYY-MM-DD --beats   # beats only
```

Calls Google's Gemini 2.5 Flash Image ("Nano Banana") with all four PC portraits (`characters/*.jpeg`) as reference and the session summary as the scene description.

- **Hero**: `sessions/YYYY-MM-DD/images/hero.jpg` (16:9 landscape banner shown above the summary).
- **Beats**: one image per `##` section of the summary, saved to `sessions/YYYY-MM-DD/images/<slugified-section-title>.jpg` (3:2 inline illustrations floated alternately left/right within each section, matching the beat's title via slug lookup). Sections whose title is "What's next" / "Loose ends" / "Next steps" (or which contain only bullet lists) are skipped.

The site generator picks up any files it finds in those paths and embeds them automatically — no `generate.py` change needed per session.

Requires the Python deps from `requirements.txt` (`.venv/bin/pip install -r requirements.txt` — `google-genai` covers this step) and a `GEMINI_API_KEY` (get one at https://aistudio.google.com/apikey — the free tier is plenty). The key can be either an exported env var or a `.env` file at the project root (`GEMINI_API_KEY=...`, one line). `.env` is git-ignored.

Skip this step if you don't want an image, or add it later. The session page renders fine either way.

### 2.6. Refresh entity session mentions

```
python3 scripts/update-entity-sessions.py           # apply
python3 scripts/update-entity-sessions.py --dry-run # preview
```

Scans every session summary (`sessions/*/summary.md`) and writes a `sessions: YYYY-MM-DD, YYYY-MM-DD, …` line into the frontmatter of each NPC, location, and item markdown file — word-boundary, case-sensitive matches against the entity's `aliases:` list. The site generator reads that field and renders a *"Mentioned in sessions"* chip row at the top of each NPC/location/item detail page, with clickable jumps to the matching session pages. Quests get the same treatment automatically from the `(YYYY-MM-DD)` parentheticals already inside each bullet in `quests.md` — no per-quest field needed.

Re-run this whenever a summary is added, expanded, or an entity gets a new alias.

### 2.7. Write an audio script (optional)

Write `sessions/YYYY-MM-DD/audio/script.md` in the "Tales of the True Hand" storyteller register. Use `sessions/2026-06-16/audio/script.md` as the canonical template — copy its structure and delivery-cue vocabulary rather than inventing new ones. Key rules:
- Line 1: `# Tales of the True Hand — YYYY-MM-DD` (the H1 is required and drives the podcast feed episode grouping).
- Line 2: `## <subtitle>` — becomes the episode title in the podcast feed (e.g. `## The Cambion at the Gate`).
- Sections: `[COLD OPEN — 25s]` / `[TITLE — 8s]` / `## ACT ONE …` (3–5 acts) / `[CLOSING — 30s]`.
- Every spoken line begins `VANDAL: *(delivery cue)* …`. Draw cues from the vocabulary in existing scripts: `hushed, urgent, cold, chilling, quoted, bright, theatrical, storyteller, signature, warm, amused, sly, dropping, quickening, dropping into serious, softer, closing, telling, personal, unfolding, leaning, taut, murmured, drawing close, wondering, reflective, measured, grave`. The audio generator maps these to ElevenLabs stability / style presets.
- Include `[MUSIC: …]` and `[STING: …]` cue lines between sections. These are ignored by the TTS layer but keep the script readable.
- Target ~5,000–7,500 characters of Vandal spoken text (~6–7 minutes at TTS pace).
- Vandal was only present at the 2026-06-16 session. For every other date frame it as retelling — *"an account I have since gathered"* — not personal witness.

For a batch of sessions, spawning parallel `general-purpose` Agents with the reference script and the summary path is the proven pattern.

### 2.8. Generate the session audio (optional)

```
.venv/bin/python scripts/generate-session-audio.py YYYY-MM-DD --voice tEo3d4j7gzVojBL5Z4Pt --force
```

Reads `sessions/YYYY-MM-DD/audio/script.md`, calls ElevenLabs TTS chunk-by-chunk with prosody-continuity via `previous_text` / `next_text`, layers in music/stings from `sessions/library/audio/` for `[MUSIC: ...]` and `[STING: ...]` cues, stitches with ffmpeg's concat filter, and writes into `sessions/YYYY-MM-DD/audio/`. The default voice ID above is Cormac ("Irish Fantasy Storyteller") — a professional voice, so it requires a **paid** ElevenLabs plan; the free tier can't use it via API. Needs `ELEVENLABS_API_KEY` in the same `.env` used by the image script (git-ignored). Watch the character budget: each script is 5–7k chars.

**TTS caching**: each speech chunk's hash is `sha256(voice_id + model_id + delivery_preset + text)`. On re-run, chunks whose hash still matches the manifest are reused — no ElevenLabs call. Editing a single line in the script re-TTSes only that chunk. Change `--voice` or `--model` (or edit `DELIVERY_PRESETS` in the script) to invalidate everything; pass `--force-tts` to invalidate the cache explicitly. Music-only tweaks are free — re-runs after only music/library changes cost zero credits.

Flags worth knowing:
- `--force` — rebuild `final.mp3` even if it exists (chunks still cached).
- `--force-tts` — invalidate the TTS cache and re-call for every speech chunk.
- `--no-music` — skip all music/sting layering; voice only.
- `--dry-run` — parse the script and print events without calling TTS.

The site generator picks up `final.mp3` from each session folder, copies it to `site/audio/sessions/YYYY-MM-DD.mp3` (name normalized), renders an inline `<audio>` player on that session's detail page, adds a small ♬ badge on the sessions list row, and lists it as an episode in `site/feed.xml`. No `generate.py` change needed per session.

Music/sting layering scope (v2): STING cues → the matching asset in the library. Discrete MUSIC cues (signature theme, minor swell, outro theme) play inline at ducked volume. **Sustained under-beds** (`[MUSIC: settles under, becomes bed]`, `[MUSIC: low ember bed; …]`) are NOT mixed under speech in v2 — they're silently skipped. Wiring sidechain-mixed beds is v3 work; see `TODO.md`.

### 2.9. Regenerate the podcast cover (rare)

```
.venv/bin/python scripts/generate-podcast-cover.py --force
```

Runs Gemini image + Pillow normalization to write `website/static/podcast-cover.jpg` as a 1400×1400 JPEG. Only needed if the show's cover art changes; a good cover survives many episodes.

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
- **Arc moved forward?** Update `campaign-state.md` — refresh `objective:` and `open_questions:` to match where the crew now stands (and set `current_location:` only to override the auto-derived location, e.g. mid-journey). This keeps the `next.html` prep hub current. The new session's `## What's next` / `## Loose ends` bullets flow into `threads.html` automatically.

### 5. Regenerate the site

```bash
python3 website/generate.py
```

The generator wipes `website/site/` and rebuilds from scratch — never hand-edit files under `website/site/`. Verify by opening `website/site/sessions.html` in a browser: the new row should appear at the top (newest first) with the right date, the right location chips, and the `*In brief:*` line as the row blurb. The new session's detail page (`session-YYYY-MM-DD.html`) should render the full summary with the original notes and raw transcript available as collapsible blocks below.

### 6. Deploy (when ready)

For an existing bucket (which is the normal case now), just run the deploy script:

```bash
./website/bin/deploy.sh
```

It wraps `aws s3 sync website/site/ s3://crew-of-the-true-hand/ --delete` with the bucket name and `--delete` baked in (override via the `BUCKET` / `SITE_DIR` env vars). Running the bare `aws s3 sync` one-liner directly still works if you prefer.

`./website/migrations/001-create-s3-bucket.sh` exists for the first-time provisioning path. Do NOT re-run the full script for redeploys — it uses `set -euo pipefail` and aborts on the `create-bucket` call ("BucketAlreadyOwnedByYou") before it ever reaches the sync step. The deploy script (or the bare sync) is the only step you need. Only deploy when the user asks; do not deploy on every regeneration.
