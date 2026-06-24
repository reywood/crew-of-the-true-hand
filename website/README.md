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
| `summaries/*.md` | Detailed session recaps — **primary content** of each session page. Lead with an italic `*In brief: ...*` line, then `##` sections. |
| `session notes/*.md` | Original Fiz-POV bullet notes. Kept as a collapsible "Original session notes" block under the summary. |
| `transcripts/*.txt` | Raw auto-transcribed audio. Kept as a collapsible "Raw transcript" block at the bottom. |

To update the site after a new session, just drop the new files into `session notes/` and `transcripts/` and re-run the generator. Same for new NPCs / locations (add a `.md` file with frontmatter), or quest changes (edit `quests.md`).

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

## Cross-linking rules

- The generator builds an alias table from PC, NPC, location, quest, and session names.
- The longest matching alias wins, with word-boundary checks (so "Hal" won't match "Halruaa" or "Halfling").
- Only the first occurrence of each entity per page is linked, to keep things readable.
- Self-links are suppressed.

## Theme

Nautical D&D — parchment cards on a deep-ocean gradient, dark-wood navigation, brass-and-rope accents, Cinzel headers, Lora body text. CSS is in `website/static/style.css`.
