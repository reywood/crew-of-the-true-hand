# TODO

Running list of open work on the Crew of the True Hand archive — site, content, audio, distribution. Add new items here rather than sprinkling `TODO:` comments across code. Roughly ordered by impact within each section; move items to `## Done` at the bottom (or delete) when they land.

When picking something up, note enough context that the reader can start work without spelunking — links to relevant files, a sentence or two on why it matters, and rough effort if you know it.

## Content

### Battle cards for Hal, Toz, Woz

`battle-cards/fiz.html` exists as the working template. Hal, Toz, and Woz still need their own single-page combat reference cards. See `battle-cards/README.md` for the layout model, dice notation, chip taxonomy, and the step-by-step recipe. Copy `fiz.html` and swap content; each card is self-contained (inline CSS, inline SVG dice, no external assets) so they can be printed or opened offline at the table.

### Continued session cadence

The core loop — new session → notes / transcript → summary → images → audio → site regen → deploy — is documented in `CLAUDE.md § Adding a new session`. Not a discrete task; just don't let the backlog build. Sessions live in `session notes/`, `transcripts/`, and `summaries/`.

## Audio & podcast pipeline

### Music beds and stingers

Scripts under `summaries/audio-scripts/` are peppered with `[MUSIC: …]` and `[STING: …]` cue lines, but the TTS pipeline currently ignores them — those cues render as plain silence. Wiring them up needs:

1. A small asset library:
   - Intro / outro theme (5–8s each).
   - 2–3 sting variants — a low held chord, a chime, a bridge.
   - An ambient bed for cold-open / hearth sections.
   - Public-domain / royalty-free works fine at this scale: Free Music Archive, YouTube Audio Library, Kevin MacLeod. Epidemic Sound / Artlist for more polish.
2. Parser upgrades in `scripts/generate-session-audio.py` to map cue labels → asset paths, honoring the duration hint (e.g. `[STING: chime — 1s]`).
3. ffmpeg work to layer beds *under* narration with sidechain ducking (~ -18 dB when Vandal speaks) and drop stings between chunks.

Estimated effort: a few hours once assets are picked. Highest-impact single change to the audio product.

### Intro / outro stinger (cheap subset of the above)

Independent of the full music-bed lift, a single 3–5 second musical stinger dropped in before `"Well met, friend"` and after `"…This has been a Tale of the True Hand."` would give the show sonic branding at low effort. Uses the same ffmpeg concat mechanism the pipeline already relies on.

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
