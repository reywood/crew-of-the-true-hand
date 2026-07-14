# TODO

Running list of open work on the Crew of the True Hand archive — site, content, audio, distribution. Add new items here rather than sprinkling `TODO:` comments across code. Roughly ordered by impact within each section; move items to `## Done` at the bottom (or delete) when they land.

When picking something up, note enough context that the reader can start work without spelunking — links to relevant files, a sentence or two on why it matters, and rough effort if you know it.

## Content

### Battle cards for Hal, Toz, Woz

`battle-cards/fiz.html` exists as the working template. Hal, Toz, and Woz still need their own single-page combat reference cards. See `battle-cards/README.md` for the layout model, dice notation, chip taxonomy, and the step-by-step recipe. Copy `fiz.html` and swap content; each card is self-contained (inline CSS, inline SVG dice, no external assets) so they can be printed or opened offline at the table.

### Continued session cadence

The core loop — new session → notes / transcript → summary → images → audio → site regen → deploy — is documented in `CLAUDE.md § Adding a new session`. Not a discrete task; just don't let the backlog build. Sessions live under `sessions/YYYY-MM-DD/` (summary, transcript, player notes, audio, images).

## Audio & podcast pipeline

### In-run TTS dedup

When the same spoken line appears twice in one script (e.g. `"You should have taken our offer."` in 2026-06-16, once in the cold open and once in Act Four), both hit the TTS API on first run because we only check the pre-run manifest for cache hits, not the in-progress one. Cheap fix in `scripts/generate-session-audio.py`: also consult `manifest_out["chunks"]` on cache miss before calling ElevenLabs. Small dollar impact per episode; still cleaner behavior.

### Richer episode descriptions in the feed

`podcast_feed()` in `website/generate.py` currently uses the `*In brief:*` one-liner as `<description>` and `<itunes:summary>`. Podcast apps happily render a longer HTML block in `<content:encoded>` — good candidate content: the summary's `## ` section headings as a bulleted show-notes list, plus a link back to the session detail page.

### Resumable audio generation

`scripts/generate-session-audio.py` aborts on ElevenLabs errors mid-batch (quota hit, network blip) and doesn't preserve the successfully-rendered chunks. Cheap wins: cache each chunk on disk keyed by `(voice, model, text)`, and on next run reuse anything that's already there before re-hitting the API.

## Website features

### Nav-bar podcast link

`sessions.html` has the Subscribe CTA (its link copies the feed URL to the clipboard with a paste-into-your-app popover). The home page deliberately carries no podcast language, and the **nav bar** (`NAV` in `website/generate.py`) doesn't mention the podcast either — so it's only discoverable from the sessions page. A small "Listen" entry in `NAV` would surface it on every page. (Note: an earlier `home-podcast` section on `index.html` was removed at the user's request.)

## Deferred / not planned

- **Cross-episode voice consistency**: Cormac at low stability drifts a little episode-to-episode. Not worth the effort of higher-stability regens; the current variance sounds human.
- **Multi-narrator / character voices in the audio recaps**: interesting but a large project — would need a voice per major NPC, script rewriting, and a director track.
- **Machine-authored session summaries or scripts without a human pass**: the summary and script quality both benefit meaningfully from review before generation; this is not a "run overnight" pipeline.

## Done

### Entity graph, connections backlinks & site search

The archive was already a graph (entities linked by frontmatter + prose), but `generate.py` computed those relationships in memory and threw them away — no persisted edge set, no reverse index, no search.

Done in `website/generate.py` (new "entity graph" section) plus `website/static/search.js`:
- **`build_graph()`** materializes a closed-vocabulary edge set (`appears_in`, `located_in`, `within`, `held_by`, `acquired_in`, `affiliated_with`, `can_help`, `depends_on`, `session_at`, `gave`, `governs`) with a reverse index. Factions become synthetic nodes (no page). Emits `site/graph.json` (`{nodes, edges}`) — also a loadable artifact for reasoning/tooling.
- **Connections block** (`_render_connections`) renders reverse links on NPC / location / PC detail pages ("Figures here", "Governed by", "Also in <faction>", "Gifts given", "Carrying"). Items are intentionally excluded — their relations already show as frontmatter meta rows.
- **Client-side search** — `site/search-index.json` (slim, derived from the graph nodes) + a hand-rolled vanilla-JS token/prefix matcher in the header (`search.js`, no CDN/Lunr), kind-grouped dropdown with keyboard nav.
- **Frontmatter enrichment**: added `giver:` to the five items that were genuine gifts (alchemy jug ← Garley Gond, bronze griffin + wind-chalk ← Zephyros, Xolkin's gift ← Xolkin, genie bottle ← Molak); loot keeps no giver.

### HTTPS + custom domain

The S3 static-hosting endpoint was HTTP-only; Apple prefers HTTPS and a real domain looks nicer in podcast apps and on the sessions page.

Done: the site is live at **https://crewofthetruehand.com** (and www). Provisioned via `website/migrations/002-cloudfront-dns-ssl.sh` (CloudFront distribution `E1M1M5VHH7QDEI` + ACM SSL cert + Route 53 hosted zone `Z0982008NXT3V47V6DCI`, fronting the S3 bucket) and `003-redirect-s3-to-domain.sh` (repoints the CloudFront origin to the S3 REST endpoint and flips the bucket website config to redirect, so the raw S3 website URL now 301s to the canonical domain with the path preserved). `SITE_BASE_URL` in `website/generate.py` now defaults to `https://crewofthetruehand.com`; the feed was regenerated and redeployed. Refresh cached content after a deploy with `aws cloudfront create-invalidation --distribution-id E1M1M5VHH7QDEI --paths '/*'`.

### Sustained under-bed mixing (music/ambience under speech)

Pipeline v2 handled discrete `[STING: …]` cues and one-off `[MUSIC: …]` cues (signature theme, minor swell, outro theme) — splicing those in as inline elements between speech chunks — but did NOT layer sustained beds under the narration itself: the `[MUSIC: settles under, becomes bed]` cue and the `[MUSIC: low ember bed; <flavor>]` cold-open cues were silently skipped, so the show lacked its hearth-crackle-under-Vandal atmosphere.

Done in `scripts/generate-session-audio.py`:
- **Bed spans**: bed cues open a span that runs until the next transition cue (`settles under` / `low ember bed` open; `signature theme` swaps to a Britons bed; `minor swell` / `outro theme` close). `render_bed()` loops `Fireplace.mp3` to the span length (cold opens also layer a per-flavor overlay via `resolve_bed_overlay` — tavern / drip / bell / wind / wheat / mist / rain / hell-fire) with fade in/out.
- **Sidechain ducking**: `mix_top_with_beds()` splits the speech+stings bus with `asplit`, `adelay`s each bed to its start offset, ducks it through `sidechaincompress` keyed off a gain-boosted copy of the speech bus (`SIDECHAIN_*` constants: threshold 0.03, ratio 2, attack 15ms, release 400ms), then `amix …:normalize=0` mixes the un-ducked speech on top so the voice is never attenuated.
- **Gain staging (the bit that made it actually audible)**: the level constants (`HEARTH_BED_DB` etc.) are **absolute dBFS targets**, not relative attenuations. `render_bed` measures each asset's own mean loudness (`_asset_mean_dbfs`, memoized via ffmpeg `volumedetect`) and normalizes it to the target — necessary because assets range from ~-15 dBFS (The Britons) to ~-47 dBFS (Wind through trees). Beds sit ~18 dB under the ~-22 dBFS voice. (The first cut used relative `volume=-22dB`, which put the already-quiet -42 dBFS fireplace at -64 dBFS — inaudible. Fixed.)
- TTS chunk cache is untouched — music-only re-runs cost zero ElevenLabs credits. `--no-beds` disables the layer for A/B.

Verified across all 11 episodes: a mid-hearth-span window has zero sub-(-50 dB) silences (the bed fills every speech gap), and phase-isolating the bed against the `--no-beds` render shows real bed energy (~-43 dBFS in the cold open) where before there was only codec-floor noise.

Follow-on (not blocking): the seams between bed spans (cold-open→signature→hearth) leave ~0.3s dips at the fade boundaries — could cross-fade them. And `SIDECHAIN_*` / target levels are easy to retune if the bed wants to sit louder/quieter.

### Attributions in the podcast feed

Every episode of "Tales of the True Hand" now uses at least four Pixabay assets and one Kevin MacLeod track (The Britons, CC BY 4.0). Pixabay's license doesn't require attribution — but The Britons does, and any future CC-BY asset we add will too. Thread the attribution list from `sessions/library/audio/CREDITS.md` through `podcast_feed()` in `website/generate.py` so every episode's `<description>` / `<content:encoded>` carries the required credits automatically. Currently the attribution lives only in the repo's CREDITS.md, which listeners won't see.

Done: `_parse_audio_credits()` / `_audio_credits_text()` in `website/generate.py` read `sessions/library/audio/CREDITS.md`, split assets by whether their license requires attribution (CC-BY: yes, verbatim wording; Pixabay: courtesy roll-up), and `podcast_feed()` appends the block to every episode's `<description>`, `<itunes:summary>`, and a new `<content:encoded>` HTML variant. Any future CC-BY asset added to CREDITS.md is picked up automatically.

### Chapter markers (MP3 ID3 chapters)

Podcast apps (Overcast, Apple, Pocket Casts) render ID3 chapter tags as tappable seek points. Add one chapter per `## ACT` heading in the script so listeners can skip to specific beats. Options: `mutagen` (Python) to write CTOC / CHAP frames directly, or `ffmpeg -f ffmetadata` to pass a metadata file at concat time.

Done via the `ffmpeg -f ffmetadata` route (no new dependency) in `scripts/generate-session-audio.py`: `parse_script` emits zero-duration `("chapter", title)` events for each `## ` section heading via `_chapter_title()` — the cold open, every ACT, and the closing; it skips the H1 show title, the episode subtitle, and the short `[TITLE]` card, and unwraps bracketed headings (`## [ACT ONE — …]`) so both bracketed and unbracketed scripts work. The build loop records `cursor_ms` at each marker (which equals the final-mix timeline, since beds mix under with `duration=first`), and `embed_chapters()` remuxes `final.mp3` in place with `-map_chapters` (codec copy) to write ID3 CHAP/CTOC frames. Each chapter runs to the next chapter's start (last → file duration). All 11 episodes rebuilt (6–7 chapters each, zero TTS credits); frames survive the `shutil.copy2` into `site/audio/sessions/` and the feed enclosure.

### Redeploy ergonomics

`website/migrations/001-create-s3-bucket.sh` uses `set -euo pipefail` and aborts on the `create-bucket` call once the bucket exists — so it's provisioning-only, not a redeploy path. `CLAUDE.md § Deploy` documents the `aws s3 sync` one-liner, but a small `website/deploy.sh` that wraps that command (with the bucket name and `--delete` baked in) would be less error-prone than remembering it.

Done: `website/bin/deploy.sh` wraps the sync with the bucket and `--delete` baked in, and parameterizes `BUCKET` / `SITE_DIR` via env vars. Run `./website/bin/deploy.sh` after regenerating the site; `CLAUDE.md § Deploy` now points at it.
