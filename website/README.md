# Website

A static site for the *Crew of the True Hand* campaign — nautical-themed, regenerated from the source markdown each time content changes.

## Regenerating

```
python3 website/generate.py
```

No dependencies — standard library only. Output goes to `website/site/`. Open `website/site/index.html` in a browser.

## Where pages come from

| Source | What it becomes |
|---|---|
| `characters/*.md` + `characters/*.jpeg` | PC detail pages and the Crew page (portraits surfaced). |
| `npcs/*.md` | NPC detail pages and the NPC index. |
| `locations/*.md` | Location detail pages and the Locations index. |
| `quests.md` | Quest detail pages (one per `- **Name**` bullet, grouped by section) and the Quest log. |
| `sessions/YYYY-MM-DD/summary.md` | Detailed session recaps — **primary content** of each session page. Lead with an italic `*In brief: ...*` line, then `##` sections. |
| `sessions/YYYY-MM-DD/player notes/<pc>.md` | Original per-PC bullet notes (currently `fiz.md`). Kept as a collapsible "Original session notes" block under the summary. |
| `sessions/YYYY-MM-DD/transcript.txt` | Raw auto-transcribed audio. Kept as a collapsible "Raw transcript" block at the bottom. |

To update the site after a new session, just drop the new files into `sessions/YYYY-MM-DD/` (`summary.md`, `transcript.txt`, `player notes/fiz.md`) and re-run the generator. Same for new NPCs / locations (add a `.md` file with frontmatter), or quest changes (edit `quests.md`).

## Entity file format (NPCs and locations)

```markdown
---
name: Molak
aliases: Molak, the innkeeper
type: Ally
location: Nightstone
first_seen: 2025-09-23
---

Body text in markdown. Names of other entities are auto-linked to their detail pages.
```

- `name` is the canonical display name.
- `aliases` is a comma-separated list of all phrasings that should auto-link to this entity. Always include the canonical name (the generator adds it if missing).
- Any other frontmatter key (`location`, `race`, `role`, etc.) is rendered as a meta row.
- `giver:` (items only) — the NPC/PC who gave the item to the crew. Use only for genuine gifts, not looted gear. Drives the `gave` graph edge and the "Gifts given" block on that NPC's page.

## Cross-linking rules

- The generator builds an alias table from PC, NPC, location, quest, and session names.
- The longest matching alias wins, with word-boundary checks (so "Hal" won't match "Halruaa" or "Halfling").
- Only the first occurrence of each entity per page is linked, to keep things readable.
- Self-links are suppressed.

## Entity graph, Connections & search

`build_graph()` (the "entity graph" section of `generate.py`) turns the whole archive into an explicit node/edge graph, derived from data already loaded — mostly serialization, not new computation. Two files are emitted into `site/`:

- **`graph.json`** — `{ "nodes": [...], "edges": [...] }`. Nodes carry `{id, kind, name, aliases, url, blurb}` (one per entity; factions are synthetic nodes with an empty `url` and no page). Edges are `{source, target, rel}` over a small closed vocabulary. It's also a compact artifact to load when answering multi-hop questions.
- **`search-index.json`** — the same nodes, slimmed to `{name, aliases, kind, url, blurb}` and filtered to real pages. Loaded by `static/search.js` for the header search box (hand-rolled token/prefix match, kind-grouped results, keyboard nav — no external library).

Edge (`rel`) vocabulary and where each comes from:

| `rel` | source → target | derived from |
|---|---|---|
| `appears_in` | any → session | `sessions:` field (materialized by `scripts/update-entity-sessions.py`) |
| `located_in` | npc → location | `location:` (via `port_for` normalization) |
| `within` | location → location | `region` / `location` / `near` (only when it resolves to a known location) |
| `held_by` | item → pc | `holder:` ("Party" produces no edge) |
| `acquired_in` | item → session | `origin:` |
| `affiliated_with` | npc → faction | `affiliation:` (synthetic faction node) |
| `can_help` | npc → item | expertise ∩ expertise_needed join |
| `depends_on` | quest → quest | `QUEST_DEPENDENCIES` |
| `session_at` | session → location | `SESSION_LOCATIONS` |
| `gave` | npc → item | `giver:` field on items |
| `governs` | npc → location | location's `ruler` / `patron` / `captain` |

The **Connections** block (`_render_connections`) uses the reverse index to add cross-reference links on NPC, location, and PC detail pages (e.g. "Figures here", "Governed by", "Also in <faction>", "Gifts given", "Carrying"). Item pages are deliberately excluded — their relations already appear as frontmatter meta rows. To add a new relation kind: emit the edge in `build_graph()`, then list it (with a label and `in`/`out` direction) under the relevant kind in `CONNECTION_SPEC`.

## Theme

Nautical D&D — parchment cards on a deep-ocean gradient, dark-wood navigation, brass-and-rope accents, Cinzel headers, Lora body text. CSS is in `website/static/style.css`.
