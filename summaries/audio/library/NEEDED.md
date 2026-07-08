# Audio library — sounds still needed

Shopping list for the "Tales of the True Hand" audio pipeline. Compiled by scanning `[MUSIC: ...]` and `[STING: ...]` cue lines across every script in `summaries/audio-scripts/`. Grouped by asset type and priority. See `CREDITS.md` for what's already registered.

Preferred sources: Pixabay (no attribution required — see Pixabay Content License), Freesound (attribution required per sound), Kevin MacLeod / incompetech.com (CC BY 4.0). Whenever a candidate is added to this directory, add its `CREDITS.md` entry **in the same commit**.

---

## Tier 1 — reusable, high-frequency (biggest wins per asset)

These fixed assets play in every episode and cover the bulk of cue lines. Land these first and 90% of the audio production quality is unlocked.

### Signature theme — intro (11 uses per session, cued as `[MUSIC: signature theme, brief]`)
- **Have candidate**: `The Britons.mp3` (Kevin MacLeod, CC BY 4.0). Needs a 4–6 second segment picked and faded.
- **Purpose**: plays under the TITLE section after the cold-open sting; establishes brand identity.

### Signature theme — outro (11 uses, cued as `[MUSIC: outro theme, full swell, fade out — 6s]`)
- **Plan**: reuse a different 6-second segment of `The Britons.mp3` — a full-swell resolution phrase, then fade. Consider running it through a light reverb / EQ so it doesn't sound identical to the intro cue.

### Hearth ambience bed (11 uses, cued as `[MUSIC: settles under, becomes bed]`)
- **Have**: `Fireplace.mp3` (Pixabay, 32.3 s). Long enough to seamless-loop under a full act with ffmpeg. Also forms the base layer for every `[MUSIC: low ember bed; <flavor>]` cold-open cue.

### Sting — chime (22 uses, cued as `[STING: chime — 1s]`)
- **Have candidate**: `Ship bell — two chimes.mp3` (Pixabay, 2.9 s). Needs trimming to ~1 second — either one bell strike or both, faded.
- **Purpose**: act break / beat transition. Most-used sting in the show.

### Sting — bridge (18 uses, cued as `[STING: bridge — 2s]`)
- **Need**: a warmer 2-second transitional flourish — a small arpeggio, harp roll, or held choir chord that closes one thought and opens the next. Lighter than the low-chord sting; not as final as the chime.
- **Search terms**: "medieval harp flourish", "cinematic bridge sting", "story transition musical".

### Sting — sharp low chord, held (11 uses, cued as `[STING: sharp low chord, held — 3s]`)
- **Have candidate**: `Tension stinger — ambience.mp3` (Pixabay, 7.9 s — SOLEMAN ALI). Needs a 3-second trim; the full clip is longer than the cue calls for. Audition alongside a couple of alternatives before locking it in.

### Music — minor swell (10 uses, cued as `[MUSIC: minor swell — 4s]`)
- **Need**: a 4-second minor-key musical swell — orchestral or choral crescendo — that lands under the pre-CLOSING beat where the tension resolves before Vandal signs off.
- **Search terms**: "orchestral minor swell", "emotional cinematic build", "melancholy strings crescendo".

---

## Tier 2 — atmospheric ambience overlays (one-off per session)

The 11 cold-opens each use a distinct `[MUSIC: low ember bed; <flavor>]` cue. Every one is the same **core** ember-bed layer (Tier 1) with a location-specific ambience overlay on top. So we don't need 11 unique assets — we need one ember bed and a small collection of ambience beds that we can layer.

Overlay assets to source (each ~15–30 s loopable):

| Overlay | Cued in | Status |
|---|---|---|
| Wind — thin, high (pine forest) | 2025-11-12, 2026-01-27 | needed |
| Wind — soft, over wheat | 2026-02-10 | needed |
| Wind — mist-wet, with a distant small voice | one session | needed |
| Rain — light, with distant heavy wing-beats | one session | needed |
| Slow water drip on stone (cave) | 2025-12-07 | needed |
| Distant tavern hum (crowd murmur, mugs) | 2026-06-16 | needed |
| Crackling hell-fire under the earth | 2026-01-13 | needed |
| Distant iron bell tolling — urgent | 2026-05-12 | ✅ `Church bell — single (musical).mp3` (needs distant/reverb treatment) |
| Distant iron bell tolling — faint, unbroken | one session | ✅ `Church bell — single (film SFX).mp3` (needs distant/reverb treatment) |

Roughly 6–7 unique overlay recordings would cover all 11 cold-opens with some sharing (both "wind" cues can share one asset, both "bell" cues can share one). None of these have candidates yet.

Alternatively, defer Tier 2 entirely and treat every cold-open as the core hearth bed alone. Loses some session-specific colour but ships a lot faster.

---

## Tier 3 — polish (not blocking any episode)

- **Alternate chime variant** — a *softer* chime for intimate beats where the ship's bell feels too percussive. Optional. Not currently cued but worth having.
- **Signature theme, alt cut for cold-open** — a *quieter* pre-title version of The Britons could go under the "Listen…" cold-open in place of, or under, the low-chord sting. Optional design choice, not currently scripted.
- **Beat images have no matching audio bumper** — inline audio for individual `##` acts is out of scope for the podcast product but could work on the site's session pages as ambient background. Deferred.
