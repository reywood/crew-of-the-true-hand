# TODO

Running list of open work on the Crew of the True Hand archive — site, content, audio, distribution. Add new items here rather than sprinkling `TODO:` comments across code. Roughly ordered by impact within each section; move items to `## Done` at the bottom (or delete) when they land.

When picking something up, note enough context that the reader can start work without spelunking — links to relevant files, a sentence or two on why it matters, and rough effort if you know it.

## Content

### Battle cards for Hal, Toz, Woz

`battle-cards/fiz.html` exists as the working template. Hal, Toz, and Woz still need their own single-page combat reference cards. See `battle-cards/README.md` for the layout model, dice notation, chip taxonomy, and the step-by-step recipe. Copy `fiz.html` and swap content; each card is self-contained (inline CSS, inline SVG dice, no external assets) so they can be printed or opened offline at the table.

### Continued session cadence

The core loop — new session → notes / transcript → summary → images → audio → site regen → deploy — is documented in `CLAUDE.md § Adding a new session`. Not a discrete task; just don't let the backlog build. Sessions live in `session notes/`, `transcripts/`, and `summaries/`.

## Audio & podcast pipeline

### Sustained under-bed mixing (music/ambience under speech)

Pipeline v2 handles discrete `[STING: …]` cues and one-off `[MUSIC: …]` cues (signature theme, minor swell, outro theme) — it splices those in as inline elements between speech chunks. What it does NOT do yet is **layer sustained beds under the narration itself**: the `[MUSIC: settles under, becomes bed]` cue that starts every episode, and the `[MUSIC: low ember bed; <flavor>]` cold-open cues, are silently skipped. The show currently doesn't have the hearth-crackle-under-Vandal atmosphere its whole storyteller conceit was built around.

Wiring this needs sidechain-style ffmpeg mixing:
1. Track the current bed state through the events list (idle → hearth on → hearth off).
2. Render the speech-plus-stings track as one bus, then mix in `Fireplace.mp3` (looped to length) at ~ -22 dB during any "bed on" span.
3. For cold-open ambience overlays (tavern hum, cave drip, distant bells, wind, rain, hell-fire), also layer the specific asset per the flavor label.
4. Apply a light sidechain compressor keyed to speech so the bed ducks another ~2 dB when Vandal is speaking, then rises back up in the silences.

Estimated effort: a solid afternoon of ffmpeg filtergraph work. Highest-remaining-impact change to the audio product now that Tier-1 discrete assets are in.

### Attributions in the podcast feed — DONE

Every episode of "Tales of the True Hand" now uses at least four Pixabay assets and one Kevin MacLeod track (The Britons, CC BY 4.0). Pixabay's license doesn't require attribution — but The Britons does, and any future CC-BY asset we add will too. Thread the attribution list from `summaries/audio/library/CREDITS.md` through `podcast_feed()` in `website/generate.py` so every episode's `<description>` / `<content:encoded>` carries the required credits automatically. Currently the attribution lives only in the repo's CREDITS.md, which listeners won't see.

Done: `_parse_audio_credits()` / `_audio_credits_text()` in `website/generate.py` read `summaries/audio/library/CREDITS.md`, split assets by whether their license requires attribution (CC-BY: yes, verbatim wording; Pixabay: courtesy roll-up), and `podcast_feed()` appends the block to every episode's `<description>`, `<itunes:summary>`, and a new `<content:encoded>` HTML variant. Any future CC-BY asset added to CREDITS.md is picked up automatically.

### In-run TTS dedup

When the same spoken line appears twice in one script (e.g. `"You should have taken our offer."` in 2026-06-16, once in the cold open and once in Act Four), both hit the TTS API on first run because we only check the pre-run manifest for cache hits, not the in-progress one. Cheap fix in `scripts/generate-session-audio.py`: also consult `manifest_out["chunks"]` on cache miss before calling ElevenLabs. Small dollar impact per episode; still cleaner behavior.

### Chapter markers (MP3 ID3 chapters)

Podcast apps (Overcast, Apple, Pocket Casts) render ID3 chapter tags as tappable seek points. Add one chapter per `## ACT` heading in the script so listeners can skip to specific beats. Options: `mutagen` (Python) to write CTOC / CHAP frames directly, or `ffmpeg -f ffmetadata` to pass a metadata file at concat time.

### Richer episode descriptions in the feed

`podcast_feed()` in `website/generate.py` currently uses the `*In brief:*` one-liner as `<description>` and `<itunes:summary>`. Podcast apps happily render a longer HTML block in `<content:encoded>` — good candidate content: the summary's `## ` section headings as a bulleted show-notes list, plus a link back to the session detail page.

### Resumable audio generation

`scripts/generate-session-audio.py` aborts on ElevenLabs errors mid-batch (quota hit, network blip) and doesn't preserve the successfully-rendered chunks. Cheap wins: cache each chunk on disk keyed by `(voice, model, text)`, and on next run reuse anything that's already there before re-hitting the API.

## Website features

### Homepage / nav podcast link

`sessions.html` has the Subscribe CTA. `index.html` and the nav bar don't mention the podcast at all. Adding a small "Listen: Tales of the True Hand" link somewhere prominent would surface it to first-time visitors.

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

### Redeploy ergonomics

`website/migrations/001-create-s3-bucket.sh` uses `set -euo pipefail` and aborts on the `create-bucket` call once the bucket exists — so it's provisioning-only, not a redeploy path. `CLAUDE.md § Deploy` documents the `aws s3 sync` one-liner, but a small `website/deploy.sh` that wraps that command (with the bucket name and `--delete` baked in) would be less error-prone than remembering it.

## Deferred / not planned

- **Cross-episode voice consistency**: Cormac at low stability drifts a little episode-to-episode. Not worth the effort of higher-stability regens; the current variance sounds human.
- **Multi-narrator / character voices in the audio recaps**: interesting but a large project — would need a voice per major NPC, script rewriting, and a director track.
- **Machine-authored session summaries or scripts without a human pass**: the summary and script quality both benefit meaningfully from review before generation; this is not a "run overnight" pipeline.
