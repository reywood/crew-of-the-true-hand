# TODO

Known open work on the "Tales of the True Hand" audio recap pipeline and site. Items are roughly ordered by how much they'd move the needle on listener experience.

## Audio pipeline

### Music beds and stingers

The scripts are peppered with `[MUSIC: …]` and `[STING: …]` cue lines (see any file in `summaries/audio-scripts/`) but the TTS pipeline currently ignores them — those cues render as plain silence. Wiring them up needs:

1. A small asset library:
   - Intro / outro theme (5–8s each).
   - 2–3 sting variants — a low held chord, a chime, a bridge.
   - An ambient bed for cold-open / hearth sections.
   - Public-domain / royalty-free is fine: Free Music Archive, YouTube Audio Library, Kevin MacLeod. Epidemic Sound / Artlist for more polish.
2. Parser upgrades in `scripts/generate-session-audio.py` to map cue labels → asset paths, honoring the duration hint (e.g. `[STING: chime — 1s]`).
3. ffmpeg work to layer beds *under* narration with sidechain ducking (~ -18 dB when Vandal speaks) and drop stings between chunks.

Estimated effort: a few hours once assets are picked. Highest-impact single change — it's the difference between a monologue and a produced show.

### Chapter markers (MP3 ID3 chapters)

Podcast apps (Overcast, Apple, Pocket Casts) render ID3 chapter tags as tappable seek points. Add one chapter per `## ACT` heading in the script so listeners can skip to specific beats. Options:

- `mutagen` (Python) — write CTOC / CHAP frames directly.
- `ffmpeg -f ffmetadata` — pass a metadata file at concat time.

Straightforward, high reward per hour.

### Richer episode descriptions in the feed

`podcast_feed()` in `website/generate.py` currently uses the `*In brief:*` one-liner as `<description>` and `<itunes:summary>`. Podcast apps happily render a longer HTML block in `<content:encoded>` — good candidate content: the summary's `## ` section headings as a bulleted show-notes list, plus a link back to the session detail page.

## Distribution

### Submit the feed to podcast directories

The feed at `http://crew-of-the-true-hand.s3-website-us-east-1.amazonaws.com/feed.xml` works but isn't listed anywhere. If we want organic discovery / cross-device subscribing:

- Apple Podcasts Connect: submit the feed. Will flag HTTP-only as a soft warning.
- Spotify for Podcasters: submit the feed.
- Overcast, Pocket Casts, Castro, Podcast Addict: automatic once Apple / Spotify accept it, or add manually.

### HTTPS + custom domain

The S3 static-hosting endpoint is HTTP-only. Nothing about the pipeline hard-requires HTTPS — Overcast, Pocket Casts, and Castro will happily fetch HTTP feeds and enclosures — but Apple prefers HTTPS, and a real domain looks nicer in podcast apps.

To fix: front the bucket with CloudFront + an ACM certificate on a domain you own, set the feed's `SITE_BASE_URL` env var at build time, regenerate, redeploy. Meaningful AWS setup (bucket policy, Route 53, ACM validation), not strictly required.

## Nice-to-have

### Intro / outro theme even without full music beds

Independent of the full music-bed lift above, a single 3–5 second musical stinger dropped in before `"Well met, friend"` and after `"…This has been a Tale of the True Hand."` would give the show sonic branding at low effort. Uses the same ffmpeg concat mechanism the pipeline already relies on.

### Homepage / nav podcast link

`sessions.html` has the Subscribe CTA. `index.html` and the nav bar don't mention the podcast at all. Adding a small "Listen: Tales of the True Hand" link somewhere prominent would surface it to first-time visitors.

### Retry stuck / partial audio jobs cleanly

`scripts/generate-session-audio.py` currently aborts on ElevenLabs errors (quota, network) mid-batch. If we regen often it'd be nice to have it skip already-generated MP3s by default (which it kind of does — `--force` is opt-in), and to *resume* a partial stitch when only some chunks succeeded, so a quota hit doesn't cost the successfully-rendered chunks.

## Deferred / not planned

- **Cross-episode voice consistency**: Cormac at low stability drifts a little episode-to-episode. Not worth the effort of higher-stability regens; the current variance sounds human.
- **Multi-narrator / character voices**: interesting but a large project — would need a voice per major NPC, script rewriting, and a director track. Save for later.
