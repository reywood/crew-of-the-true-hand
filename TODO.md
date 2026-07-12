# TODO

Running list of open work on the Crew of the True Hand archive — site, content, audio, distribution. Add new items here rather than sprinkling `TODO:` comments across code. Roughly ordered by impact within each section; move items to `## Done` at the bottom (or delete) when they land.

When picking something up, note enough context that the reader can start work without spelunking — links to relevant files, a sentence or two on why it matters, and rough effort if you know it.

## Content

### Battle cards for Hal, Toz, Woz

`battle-cards/fiz.html` exists as the working template. Hal, Toz, and Woz still need their own single-page combat reference cards. See `battle-cards/README.md` for the layout model, dice notation, chip taxonomy, and the step-by-step recipe. Copy `fiz.html` and swap content; each card is self-contained (inline CSS, inline SVG dice, no external assets) so they can be printed or opened offline at the table.

### Continued session cadence

The core loop — new session → notes / transcript → summary → images → audio → site regen → deploy — is documented in `CLAUDE.md § Adding a new session`. Not a discrete task; just don't let the backlog build. Sessions live under `sessions/YYYY-MM-DD/` (summary, transcript, player notes, audio, images).

## Audio & podcast pipeline

### Sustained under-bed mixing (music/ambience under speech) — DONE

Pipeline v2 handled discrete `[STING: …]` cues and one-off `[MUSIC: …]` cues (signature theme, minor swell, outro theme) — splicing those in as inline elements between speech chunks — but did NOT layer sustained beds under the narration itself: the `[MUSIC: settles under, becomes bed]` cue and the `[MUSIC: low ember bed; <flavor>]` cold-open cues were silently skipped, so the show lacked its hearth-crackle-under-Vandal atmosphere.

Done in `scripts/generate-session-audio.py`:
- **Bed spans**: bed cues open a span that runs until the next transition cue (`settles under` / `low ember bed` open; `signature theme` swaps to a Britons bed; `minor swell` / `outro theme` close). `render_bed()` loops `Fireplace.mp3` to the span length (cold opens also layer a per-flavor overlay via `resolve_bed_overlay` — tavern / drip / bell / wind / wheat / mist / rain / hell-fire) with fade in/out.
- **Sidechain ducking**: `mix_top_with_beds()` splits the speech+stings bus with `asplit`, `adelay`s each bed to its start offset, ducks it through `sidechaincompress` keyed off a gain-boosted copy of the speech bus (`SIDECHAIN_*` constants: threshold 0.03, ratio 2, attack 15ms, release 400ms), then `amix …:normalize=0` mixes the un-ducked speech on top so the voice is never attenuated.
- **Gain staging (the bit that made it actually audible)**: the level constants (`HEARTH_BED_DB` etc.) are **absolute dBFS targets**, not relative attenuations. `render_bed` measures each asset's own mean loudness (`_asset_mean_dbfs`, memoized via ffmpeg `volumedetect`) and normalizes it to the target — necessary because assets range from ~-15 dBFS (The Britons) to ~-47 dBFS (Wind through trees). Beds sit ~18 dB under the ~-22 dBFS voice. (The first cut used relative `volume=-22dB`, which put the already-quiet -42 dBFS fireplace at -64 dBFS — inaudible. Fixed.)
- TTS chunk cache is untouched — music-only re-runs cost zero ElevenLabs credits. `--no-beds` disables the layer for A/B.

Verified across all 11 episodes: a mid-hearth-span window has zero sub-(-50 dB) silences (the bed fills every speech gap), and phase-isolating the bed against the `--no-beds` render shows real bed energy (~-43 dBFS in the cold open) where before there was only codec-floor noise.

Follow-on (not blocking): the seams between bed spans (cold-open→signature→hearth) leave ~0.3s dips at the fade boundaries — could cross-fade them. And `SIDECHAIN_*` / target levels are easy to retune if the bed wants to sit louder/quieter.

### Attributions in the podcast feed — DONE

Every episode of "Tales of the True Hand" now uses at least four Pixabay assets and one Kevin MacLeod track (The Britons, CC BY 4.0). Pixabay's license doesn't require attribution — but The Britons does, and any future CC-BY asset we add will too. Thread the attribution list from `sessions/library/audio/CREDITS.md` through `podcast_feed()` in `website/generate.py` so every episode's `<description>` / `<content:encoded>` carries the required credits automatically. Currently the attribution lives only in the repo's CREDITS.md, which listeners won't see.

Done: `_parse_audio_credits()` / `_audio_credits_text()` in `website/generate.py` read `sessions/library/audio/CREDITS.md`, split assets by whether their license requires attribution (CC-BY: yes, verbatim wording; Pixabay: courtesy roll-up), and `podcast_feed()` appends the block to every episode's `<description>`, `<itunes:summary>`, and a new `<content:encoded>` HTML variant. Any future CC-BY asset added to CREDITS.md is picked up automatically.

### In-run TTS dedup

When the same spoken line appears twice in one script (e.g. `"You should have taken our offer."` in 2026-06-16, once in the cold open and once in Act Four), both hit the TTS API on first run because we only check the pre-run manifest for cache hits, not the in-progress one. Cheap fix in `scripts/generate-session-audio.py`: also consult `manifest_out["chunks"]` on cache miss before calling ElevenLabs. Small dollar impact per episode; still cleaner behavior.

### Chapter markers (MP3 ID3 chapters) — DONE

Podcast apps (Overcast, Apple, Pocket Casts) render ID3 chapter tags as tappable seek points. Add one chapter per `## ACT` heading in the script so listeners can skip to specific beats. Options: `mutagen` (Python) to write CTOC / CHAP frames directly, or `ffmpeg -f ffmetadata` to pass a metadata file at concat time.

Done via the `ffmpeg -f ffmetadata` route (no new dependency) in `scripts/generate-session-audio.py`: `parse_script` emits zero-duration `("chapter", title)` events for each `## ` section heading via `_chapter_title()` — the cold open, every ACT, and the closing; it skips the H1 show title, the episode subtitle, and the short `[TITLE]` card, and unwraps bracketed headings (`## [ACT ONE — …]`) so both bracketed and unbracketed scripts work. The build loop records `cursor_ms` at each marker (which equals the final-mix timeline, since beds mix under with `duration=first`), and `embed_chapters()` remuxes `final.mp3` in place with `-map_chapters` (codec copy) to write ID3 CHAP/CTOC frames. Each chapter runs to the next chapter's start (last → file duration). All 11 episodes rebuilt (6–7 chapters each, zero TTS credits); frames survive the `shutil.copy2` into `site/audio/sessions/` and the feed enclosure.

### Richer episode descriptions in the feed

`podcast_feed()` in `website/generate.py` currently uses the `*In brief:*` one-liner as `<description>` and `<itunes:summary>`. Podcast apps happily render a longer HTML block in `<content:encoded>` — good candidate content: the summary's `## ` section headings as a bulleted show-notes list, plus a link back to the session detail page.

### Resumable audio generation

`scripts/generate-session-audio.py` aborts on ElevenLabs errors mid-batch (quota hit, network blip) and doesn't preserve the successfully-rendered chunks. Cheap wins: cache each chunk on disk keyed by `(voice, model, text)`, and on next run reuse anything that's already there before re-hitting the API.

## Website features

### Nav-bar podcast link

`sessions.html` has the Subscribe CTA (its link copies the feed URL to the clipboard with a paste-into-your-app popover). The home page deliberately carries no podcast language, and the **nav bar** (`NAV` in `website/generate.py`) doesn't mention the podcast either — so it's only discoverable from the sessions page. A small "Listen" entry in `NAV` would surface it on every page. (Note: an earlier `home-podcast` section on `index.html` was removed at the user's request.)

### Site search

There's no way to search across NPCs / locations / sessions / items today — visitors have to browse category pages or use their browser's find-in-page. A tiny client-side search (Lunr.js, or an even lighter hand-rolled index over the entity JSON that `generate.py` already builds internally) would fit the site's static nature.

## Distribution / infrastructure

### Submit the podcast to directories

The feed at `http://crew-of-the-true-hand.s3-website-us-east-1.amazonaws.com/feed.xml` works but isn't listed anywhere. If we want organic discovery / cross-device subscribing:

- Apple Podcasts Connect: submit the feed. Will flag HTTP-only as a soft warning.
- Spotify for Podcasters: submit the feed.
- Overcast, Pocket Casts, Castro, Podcast Addict: automatic once Apple / Spotify accept it, or add manually.

### HTTPS + custom domain

The S3 static-hosting endpoint is HTTP-only. Nothing about the pipeline hard-requires HTTPS — Overcast, Pocket Casts, and Castro will happily fetch HTTP feeds and enclosures — but Apple prefers HTTPS, and a real domain looks nicer in podcast apps and on the sessions page.

To fix: front the bucket with CloudFront + an ACM certificate on a domain you own, set the feed's `SITE_BASE_URL` env var at build time, regenerate, redeploy. Meaningful AWS setup (bucket policy, Route 53, ACM validation), not strictly required.

### Redeploy ergonomics — DONE

`website/migrations/001-create-s3-bucket.sh` uses `set -euo pipefail` and aborts on the `create-bucket` call once the bucket exists — so it's provisioning-only, not a redeploy path. `CLAUDE.md § Deploy` documents the `aws s3 sync` one-liner, but a small `website/deploy.sh` that wraps that command (with the bucket name and `--delete` baked in) would be less error-prone than remembering it.

Done: `website/bin/deploy.sh` wraps the sync with the bucket and `--delete` baked in, and parameterizes `BUCKET` / `SITE_DIR` via env vars. Run `./website/bin/deploy.sh` after regenerating the site; `CLAUDE.md § Deploy` now points at it.

## Deferred / not planned

- **Cross-episode voice consistency**: Cormac at low stability drifts a little episode-to-episode. Not worth the effort of higher-stability regens; the current variance sounds human.
- **Multi-narrator / character voices in the audio recaps**: interesting but a large project — would need a voice per major NPC, script rewriting, and a director track.
- **Machine-authored session summaries or scripts without a human pass**: the summary and script quality both benefit meaningfully from review before generation; this is not a "run overnight" pipeline.
