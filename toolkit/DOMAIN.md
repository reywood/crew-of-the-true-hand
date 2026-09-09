# Domain model — Crew of the True Hand

How the archive and its toolkit are carved up: the bounded contexts, what each
one owns, the aggregates and their invariants, and the vocabulary each context
speaks. Written against `toolkit/src/truehand/` as it stands.

The governing fact about this system: **the archive is a filesystem, and the
filesystem is the event log.** Every step of the workflow in `CLAUDE.md` leaves
a file behind (`transcript.txt`, `summary.md`, `images/hero.jpg`,
`audio/final.mp3`). Nothing is a database row and nothing is a message on a
bus. So "domain event" here means *a file appearing*, and the toolkit's job is
to read the current set of files, infer which events have happened, and derive
the next artifact. That is a legitimate architecture for a one-person archive
and this document does not propose replacing it — it proposes naming it.

---

## 1. Bounded contexts

Five, in the order material flows through them.

| # | Context | Owns | Lives in |
|---|---|---|---|
| 1 | **Campaign Archive** | What happened in the fiction, and who/what/where it happened to | `core/`, `data/`, the markdown tree |
| 2 | **Session Production** | Turning an evening of play into a verified record | `pipelines/factcheck.py`, plus human/agent steps in `CLAUDE.md` §1.5 |
| 3 | **Illustration** | How the crew and the world LOOK | `content/`, `pipelines/session_image.py`, `character_refs.py`, `podcast_cover.py`, `adapters/images.py` |
| 4 | **Podcast Production** | "Tales of the True Hand" as a *show* — Vandal's voice, acts, cues, mix | `pipelines/session_audio.py`, `data/audio_direction.toml`, `adapters/tts.py`, `adapters/ffmpeg.py`, `sessions/library/audio/` |
| 5 | **Website Publishing** | The reader-facing artifact: pages, chips, feed, search | `site/` |

### 1.1 Campaign Archive

**Responsibility.** Be the single source of truth about the campaign's fiction
and its record. Answer "what happened on 2026-08-12", "who is Naxene", "where
is Kryptgarden Forest", "what is the crew carrying", "what are we doing next".
Own every derived join that is a *fact about the fiction* rather than a
rendering decision.

Its language: *session, beat, in brief, loose ends, carried, PC / crew, NPC,
standing, location, port, item, holder, expertise, quest, arc, objective, open
question, alias.*

It is deliberately pure: stdlib only, no HTML, no network. That constraint is
what makes it the shared kernel every other context is allowed to depend on.

### 1.2 Session Production

**Responsibility.** Get from `recording.m4a` to a record whose *attributions
are trusted*. This context's whole reason to exist is that diarization is
wrong in combat, and every downstream artifact inherits the error.

Its language: *recording, whisply, diarization, speaker cluster, over-split
(K=8), attribution, class-mechanic fingerprint, distillation, fact-check
worksheet, verdict, the gate.*

Almost none of this vocabulary appears in code, because almost all of the work
is done by a human plus an Opus agent. The only inhabitant is
`pipelines/factcheck.py`, which renders the worksheet as a reviewable HTML page
with an audio scrubber. That is correct scoping — but note that **the context's
single most important rule (the fact-check gate) has no code representation at
all**, which is why it must be restated in prose in `CLAUDE.md` three times.

### 1.3 Illustration

**Responsibility.** Keep the crew looking like themselves across dozens of
generated images. The hard problem is *identity drift*, not composition.

Its language: *anchor (`PC_ANCHORS`), reference plate, lean cast, roll-call,
art style, aspect, hero, beat illustration, cover.*

Note `content/pc_identity.py`'s docstring: this vocabulary existed in four
drifted copies before it was consolidated. The context boundary is now stated
crisply in `toolkit/README.md`: `content/` is *how the PCs look*,
`data/party.toml` is *who they are*. That is a genuine, defensible seam and it
should be preserved.

### 1.4 Podcast Production

**Responsibility.** Produce an episode of a show. Not "make an mp3 of a
session" — a *show*, with a named narrator, a fixed act structure, signature
open and close, delivery direction, a music library with licence obligations,
and a budget.

Its language: *episode, episode title, act, cold open, title card, closing,
Vandal Lovelace, spoken line, delivery cue, delivery preset, cue (MUSIC /
STING), sting, bed, under-bed, bed span, signature theme, hearth, overlay,
chunk, manifest, cache hit, chapter mark, voice, model, credits.*

This context has a hard constraint the others don't: **TTS costs money, and the
cache key is load-bearing.** `chunk_hash` in `pipelines/session_audio.py`
covers voice + model + delivery-preset name + the preset's JSON + the text.
`data/audio_direction.toml`'s `[delivery]` table sits inside that hash;
`toolkit/tests/test_chunk_hash.py` freezes it against a value captured from the
pre-migration script, and `test_every_committed_manifest_still_resolves`
asserts no committed episode would re-bill. Treat that hash as a published
contract with past money already spent.

Also inside this context, though it currently lives in `site/feed.py`, is a
small sub-domain: **audio licensing**. `sessions/library/audio/CREDITS.md`
distinguishes assets whose licence *requires* attribution (CC-BY: The Britons)
from those where it is a courtesy (Pixabay). That is a legal fact about the
show, not a rendering choice.

### 1.5 Website Publishing

**Responsibility.** Render everything above into `website/site/` — a tree that
must be byte-reproducible (`toolkit/tests/test_golden_site.py`).

Its language: *page, nav, breadcrumb, chip, card, blurb, subhead, connections,
linkify, share meta / Open Graph, cache-buster, search index, graph.json,
feed, enclosure, episode.*

Its stated rule — `toolkit/README.md`: "Depends on `core`; never the reverse" —
holds today, and the `Relations` refactor is what made it hold.

---

## 2. Ubiquitous language: where the code disagrees with the archive

The archive's own vocabulary is set by `CLAUDE.md`. Where the code says
something else, the code is wrong — these are the mismatches worth knowing
about.

| Archive says | Code says | Where | Verdict |
|---|---|---|---|
| **episode** (of a podcast) | `session audio`, `build_episode`, `paths.session_audio()`, `site/audio/sessions/` | `cli/session.py`, `paths.py`, `pipelines/session_audio.py` | Accepted drift. The CLI verb is muscle memory; leave it. But the *aggregate* is an Episode, and internal names should say so. |
| **episode title** | `audio_subtitle` | `core/session.py`, `core/loaders.py`, `site/feed.py`, `site/pages/sessions.py` | Real mismatch. It is a title, not a subtitle. |
| **beat** (a `##` section of a summary) | `Beat` | `core/summary.py` | Correct. Keep. |
| **act** (a `## ACT ONE` of a script) | *(nothing — a bracket-matching branch in `_chapter_title`)* | `pipelines/session_audio.py` | Missing. An Act is a first-class structural unit of a script and is not the same thing as a Beat; the two do not correspond 1:1. |
| **standing** (how the crew stands with an NPC) | `chip_for()` returning `(label, css_class)` | `core/loaders.py` | Mismatch, and a layering one: `core` names a concept after its CSS chip and hands back a CSS class. Compare `QuestStatus`, which got this right. |
| **carried** (session frontmatter) | `carried` in core; "Items acquired" on the page | `core/loaders.py`, `site/pages/sessions.py` | Two names, one thing. Harmless; noted. |
| **current objective / open questions** | `state` dict, `state.get("objective")` | `core/loaders.py`, `site/pages/prep.py` | Anemic. `CampaignState` is a value object with two fields and an override. |
| **where the session took place** | `SESSION_LOCATIONS`, a module-level dict | `core/loaders.py`, read by `core/graph.py`, `site/pages/sessions.py`, `site/pages/prep.py` | Real problem. This is Session state, not ambient config. |
| **Vandal Lovelace** (the narrator) | the literal `"VANDAL:"` | `pipelines/session_audio.py` | Fine for a one-narrator show. Name the constant. |
| **crew / characters / PCs** | `kind="pc"`, `[pcs.*]`, nav "Characters", page "The Crew" | everywhere | Accepted synonyms. The archive uses all three too. |

---

## 3. Aggregates, entities, value objects

### 3.1 Campaign Archive

**`Session`** — aggregate root. `core/session.py`.

- Identity: the real-world date. Not a slug. (`slug` is a *property* returning
  the date, which is the right compromise for uniform treatment with `Entity`.)
- Invariant, enforced in `__post_init__`: a folder holding none of notes,
  transcript or summary is not a session. `load_sessions` skips such folders
  rather than constructing and catching.
- Contains: `SessionSummary` (VO), `SessionArtifacts` (VO), `carried`
  (tuple of strings — a VO list), raw `notes` / `transcript` strings.
- Derived, never stored: `blurb`, `has_audio`, `audio_name`, `has_hero`,
  `hero_name`, `beat_image(beat)`. The published-URL naming rules live here and
  nowhere else; `site/assets.py:_stage_session_media` copies what the aggregate
  reports rather than re-walking the tree.
- **Missing from the aggregate:** where it took place, and any notion of *how
  far through the pipeline it is*.

**`SessionSummary` / `Beat`** — value objects. `core/summary.py`.

Immutable, no identity, compared by value: textbook VOs. `Beat` owns the three
questions everybody used to ask ad hoc — `slug` (which matches the beat-image
filename), `is_forward_looking`, `is_illustratable`. `FORWARD_HEADINGS` is the
one heading vocabulary; `_HEADING` is deliberately as strict as
`core/markdown.md_to_html`'s so the `Beat` sequence lines up one-for-one with
the rendered `<h2>`s, which is what makes `_inject_beat_images` a zip rather
than an HTML re-parse.

**`Entity`** — `core/entity.py`. One class covering PC, NPC, Location, Item,
Quest. Strictly, NPC / Location / Item are three aggregates that happen to
share a file format, a detail-page template and a graph-node shape. Modelling
them as one `Entity` with a `kind` discriminator is **anemic by the book and
correct in practice**: their behaviour genuinely is identical, and
`Frontmatter`/`Field` already give typed access to the parts that differ. Do
not split them.

**`QuestLog` -> `Quest`** — there is no `QuestLog` object; `load_quests`
returns a list of `Entity(kind="quest")`. The aggregate boundary is real
(`quests.md` is one file, and a quest's status is *its position within that
file*), but the aggregate is not worth materialising.

**`QuestStatus`** — value object. `core/quest_status.py`. The model example of
this codebase: `label`, `css_class`, `impact`, `display_order`, `is_active` all
hang off the status, so a label is only ever a label. Note one dead branch:
`PERSONAL` can never be produced, because `load_quests` filters the Personal
section out before `for_section` is reached.

**`Frontmatter` / `Field`** — value objects. `core/frontmatter.py`. `Field` is
"read by intent, not by isinstance" — `one()`, `many()`, `prose()`, `tags()`.
`Frontmatter` lookup is total, so no reader branches on absence.
`parse_frontmatter` *is the dialect* — it defines what a file means;
`TestThisIsNotYaml` documents why real YAML cannot be substituted.

**`CampaignState`** — should be a value object (objective, open questions,
optional location override). Is a `dict`.

**`Relations`** — a derived read model, `core/relations.py`. Not an aggregate;
a frozen bundle of joins computed once per build and passed explicitly. These
joins used to be mutated onto `Entity.meta` by the site layer while
`core.graph` read them back, so correctness depended on statement order in
`build_site`.

**`Graph`** — the other derived read model, `core/graph.py`. Closed edge
vocabulary (`appears_in`, `located_in`, `within`, `held_by`, `acquired_in`,
`affiliated_with`, `can_help`, `depends_on`, `session_at`, `gave`, `governs`)
plus synthetic faction nodes. Consumed by `graph.json`, the search index, and
the Connections block.

### 3.2 Podcast Production

Nothing in this context is currently modelled. What the domain actually
contains:

**`Episode`** — aggregate root, identity = the session date. Invariants:

- Its `script.md` must have an H1 (`# Tales of the True Hand — DATE`) and a
  line-2 `## <title>`; both drive downstream artifacts (feed grouping, episode
  title).
- Every spoken line resolves to a delivery preset (today an unknown cue
  silently becomes `default`; a test catches this from outside).
- Chapter marks are monotonic in ms.
- The manifest's chunk hashes are exactly the set the current script produces.

**`EpisodeScript`** — value object. The parsed `script.md`: title, episode
title, ordered `Act`s, ordered events. The direct analogue of `SessionSummary`,
and it does not exist. Two different parsers read this document today
(`parse_script`, and `core/loaders._read_audio_subtitle` reaching into the
Archive context to grab line 2 with `fh.readline()`).

**`Act`** — entity within the script (ordered, titled, may become a chapter).

**`SpokenLine`** — value object: `(text, delivery_cue)`. Currently the tuple
`("speak", text, delivery)`.

**`DeliveryCue` -> `VoicePreset`** — value objects. `resolve_delivery` returns
a `(key, dict)` tuple; the key is inside the cache hash, the dict is the
settings.

**`Cue`** (`[MUSIC: ...]` / `[STING: ...]`) -> **`AssetClip(path, db, segment)`**
— value objects. Currently 3-tuples out of the three `resolve_*` functions.

**`BedSpan(start_ms, end_ms, kind, label)`** — value object. Currently a dict
built by an inline state machine.

**`ChapterMark(title, at_ms)`**, **`TimelineElement(path, dur_ms, kind)`** —
value objects. Currently dicts.

**`ShowDirection`** — value object loaded from `data/audio_direction.toml`.
Currently ~15 module-level constants unpacked at import time.

**`ChunkCache` / `Manifest`** — an *entity* (it has identity and a lifecycle
across runs, unlike everything else here). Owns `chunk_hash`, the manifest
read/write, chunk filenames, and the cache-hit copy.

**`AudioLibrary` + `AssetCredit`** — the shared music library and its licence
obligations. Currently parsed inside `site/feed.py` behind a module global.

### 3.3 Illustration

`PCAnchor` / `LeanCast` / `ArtStyle` / `Plate` — all value objects, all in
`content/`. `ImageResult`, `PlateResult`, `CoverResult` — result value objects
returned to the CLI for printing. This context is well-shaped: pipelines return
`(results, warnings)` and never print, backends are `Protocol`s so prompt
assembly is testable without spending quota.

### 3.4 Website Publishing

`SiteBuild` is implicit in `build_site`. `LinkIndex` (`site/linkify.py`) is a
genuine, well-documented optimisation object — its docstring explains exactly
why one shared pattern is not sufficient (32 overlapping alias pairs, e.g.
"Umberlee" inside "Umberlee eye-coin"). `Chip`, `ShareMeta`, `Breadcrumb` exist
as functions rather than types, which is right for a renderer.

---

## 4. Domain events

Events, in workflow order, with the file that *is* the event and the code that
reacts.

| Event | Evidence on disk | Produced by | Consumed by |
|---|---|---|---|
| `SessionRecorded` | `sessions/D/recording.m4a` | the table | whisply; the factcheck page's audio scrubber |
| `SessionTranscribed` | `sessions/D/transcript.txt` | whisply | `Session.transcript` -> collapsible block |
| `TranscriptDistilled` | `transcript-distilled.md` | Opus agent | the summary author |
| `FactCheckIssued` | `transcript-distilled.factcheck.md` -> `.html` | `truehand session factcheck` | the user |
| **`FactCheckReturned`** | **— nothing —** | the user, by hand | **nothing. This is the gap.** |
| `SessionSummarized` | `summary.md` | human/agent | `Session.summary`, images, script, entity sync, prep hub, threads board, feed |
| `SessionLocated` | an entry in `data/session_locations.toml` | human | `sessions.html` chips, `session_at` edges, prep hub |
| `SessionIllustrated` | `images/hero.jpg`, `images/<beat-slug>.jpg` | `truehand session image` | `SessionArtifacts`, staging, `og:image`, feed image |
| `EntityMentionsSynced` | a `sessions:` line in each entity's frontmatter | `truehand entities sync` | `appears_in` edges, "Mentioned in sessions" chips |
| `EpisodeScripted` | `audio/script.md` | human/agent | episode title, TTS, chapters |
| `EpisodeVoiced` | `audio/chunks/NNNN.mp3` + `manifest.json` | `truehand session audio` | itself, on the next run |
| `EpisodeMixed` | `audio/final.mp3` | same | inline player, badge, feed enclosure |
| `ArcAdvanced` | edits to `quests.md` / `campaign-state.md` | human | quest log, prep hub |
| `SitePublished` | `website/site/**` | `truehand site build` | the golden test, `deploy.sh` |

Two observations.

**The gate is the only event with no evidence.** Every other step leaves a
file, so the toolkit can infer state. "The user returned the marked-up
worksheet and their corrections were applied" leaves nothing, which is exactly
why `CLAUDE.md` has to shout about it in bold in three places.

**Order matters and is unenforced.** `truehand session audio` will happily
voice a script for a session that has a transcript and no distillation.

---

## 5. Context map

```
                    +---------------------------+
                    |   SESSION PRODUCTION      |
                    |  recording -> transcript  |
                    |  -> distillation -> GATE  |
                    +------------+--------------+
                                 | verified summary.md
                                 v
   +------------------------------------------------------+
   |              CAMPAIGN ARCHIVE  (core/)               |
   |   Session . Entity . QuestLog . CampaignState        |
   |   SessionSummary . Frontmatter . Relations . Graph   |
   +---+------------------+-------------------+-----------+
       | shared kernel    | shared kernel     | conformist
       v                  v                   v
 +------------+    +----------------+   +------------------+
 |ILLUSTRATION|    |    PODCAST     |   | WEBSITE          |
 |  images/   |--->|  PRODUCTION    |-->| PUBLISHING       |
 |  cover     |    |  script->audio |   |  html + feed.xml |
 +------------+    +----------------+   +------------------+
       ^ cover              |  episode title
       +--------------------+  (leaks upstream into core)
```

**Campaign Archive -> Website Publishing: Customer/Supplier, site is a
Conformist.** `site/` consumes `Session`, `Entity`, `Relations`, `Graph`,
`QuestStatus` verbatim with no translation layer. Correct: they speak the same
language and an ACL would be pure ceremony. The one-way dependency is stated in
`toolkit/README.md` and holds.

**Campaign Archive -> Illustration: shared kernel on `SessionSummary`.** Right
idea; `pipelines/session_image.load_summary` bypasses `load_sessions` and so
applies *different* document rules.

**Podcast Production -> Campaign Archive: an upstream leak.**
`core/loaders._read_audio_subtitle` opens the podcast script and slices line 2.
The Archive should not know the show's script format. This is the one place a
genuine translator is warranted, and it belongs on the Podcast side.

**Podcast Production -> Website Publishing: Published Language = `feed.xml`.**
`site/feed.py` is the translator. It currently translates from `Session` +
`SessionArtifacts` rather than from an `Episode`, and it additionally hosts the
whole audio-licensing sub-domain (`_parse_audio_credits`).

**`adapters/` is the infrastructure layer for all four downstream contexts.**
The `Protocol`s are used sparingly and for the right reason, and each says so:
`ImageBackend` because a fake backend lets prompt assembly be tested without
spending Gemini quota; `TTSBackend` because ElevenLabs costs real money on the
paid Cormac voice; `ffmpeg.py` deliberately *not* a Protocol because there is
one ffmpeg and no plausible second implementation, so an interface would be
ceremony. That judgement is exactly right.

**`data/` is a shared kernel of authored campaign values**, correctly moved out
of code. One caveat: `data/audio_direction.toml`'s `[delivery]` table is not
merely data — it is inside a cache key that has already been paid for. It is
data with a *contract*.

---

## 6. Deliberately not modelled

Recorded so nobody "fixes" them later:

- **NPC / Location / Item as separate classes.** Identical behaviour, identical
  file format, identical page. `Entity` + `Frontmatter` is the right size.
- **A `QuestLog` aggregate object.** The list works.
- **Repositories.** `Paths` + `load_*(paths)` is the repository, and it is
  already injectable for tests.
- **Domain events as objects, or an event bus.** The filesystem is the log.
- **An ACL between Podcast and Archive.** One person, one vocabulary; a single
  named translator function is enough.
- **`ffmpeg` behind an interface.** See above.
