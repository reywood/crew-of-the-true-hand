# Audio library — third-party assets and attribution

Files under `summaries/audio/library/` are third-party music / sound assets used (or being evaluated for use) in the "Tales of the True Hand" podcast recap pipeline. Every asset here MUST be recorded below with its source, license, and the exact attribution wording the license requires. This file — plus the show's episode descriptions / footer — is where those attributions live.

Do NOT add an asset to the library without also adding its entry here. Do NOT modify or delete these attribution blocks; they are a license condition.

---

## The Britons.mp3

- **Source**: incompetech.com (Kevin MacLeod)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0) — <https://creativecommons.org/licenses/by/4.0/>
- **Duration**: 5:07
- **Status**: Under evaluation as intro music. Not yet wired into the audio pipeline.

**Required attribution wording** (must appear in show notes / episode description or somewhere reasonably discoverable to listeners whenever the track is used):

> "The Britons" Kevin MacLeod (incompetech.com)
> Licensed under Creative Commons: By Attribution 4.0 License
> http://creativecommons.org/licenses/by/4.0/

---

## Ship bell — two chimes.mp3

- **Source**: Pixabay — uploader [`freesound_community`](https://pixabay.com/users/freesound_community-46691455/), Pixabay sound ID 102730
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 2.9 s
- **Status**: Candidate STING asset — a two-chime ship's bell suitable for `[STING: chime — 1s]` cue lines. Not yet wired into the audio pipeline.

**Attribution**: Not required by the Pixabay Content License. We voluntarily credit uploaders in the podcast show notes as a courtesy. Pixabay's generated attribution snippet (use verbatim when the license permits HTML; use the plain-text fallback below for text-only channels):

```html
Sound Effect by <a href="https://pixabay.com/users/freesound_community-46691455/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=102730">freesound_community</a> from <a href="https://pixabay.com//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=102730">Pixabay</a>
```

Plain-text fallback: *Ship bell sound effect by freesound_community from Pixabay (https://pixabay.com).*

**Redistribution note**: Pixabay's license forbids redistributing raw assets "as-is on any stock or wallpaper platform." Keeping the file inside this project's git repo is standard project use and is allowed; do NOT publish this MP3 to any stock or free-download site.

---

## Church bell — single (musical).mp3

- **Source**: Pixabay — uploader [`Universfield`](https://pixabay.com/users/universfield-28281460/), Pixabay sound ID 156463
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 4.8 s
- **Status**: Candidate for the Tier-2 "distant iron bell tolling — urgent" cold-open overlay (2026-05-12). Not yet wired into the audio pipeline.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/universfield-28281460/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=156463">Universfield</a> from <a href="https://pixabay.com/sound-effects//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=156463">Pixabay</a>
```

Plain-text fallback: *Musical single church bell by Universfield from Pixabay (https://pixabay.com).*

---

## Church bell — single (film SFX).mp3

- **Source**: Pixabay — uploader [`Universfield`](https://pixabay.com/users/universfield-28281460/), Pixabay sound ID 352062
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 3.6 s
- **Status**: Candidate for the Tier-2 "distant iron bell tolling — faint, unbroken" cold-open overlay. Not yet wired into the audio pipeline.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/universfield-28281460/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=352062">Universfield</a> from <a href="https://pixabay.com//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=352062">Pixabay</a>
```

Plain-text fallback: *Film SFX single church bell by Universfield from Pixabay (https://pixabay.com).*

---

## Fireplace.mp3

- **Source**: Pixabay — uploader [`freesound_community`](https://pixabay.com/users/freesound_community-46691455/), Pixabay sound ID 6160
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 32.3 s
- **Status**: Registered as the Tier-1 hearth ambience bed. Covers `[MUSIC: settles under, becomes bed]` (11 uses, one per session) and forms the base layer for every `[MUSIC: low ember bed; <flavor>]` cold-open cue. Long enough to loop seamlessly under a full act; ffmpeg will handle the loop + fade.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/freesound_community-46691455/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=6160">freesound_community</a> from <a href="https://pixabay.com//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=6160">Pixabay</a>
```

Plain-text fallback: *Fireplace ambience by freesound_community from Pixabay (https://pixabay.com).*

---

## Tension stinger — ambience.mp3

- **Source**: Pixabay — uploader [`SOLEMAN ALI` (`gd_salman`)](https://pixabay.com/users/gd_salman-13705087/), Pixabay sound ID 355381
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 3.87 s (locally re-encoded — 1 s of silence trimmed off the head and 3 s of silence trimmed off the tail of the original 7.9 s Pixabay download)
- **Status**: Candidate for the Tier-1 `[STING: sharp low chord, held — 3s]` cue (11 uses — the cold-open tag under Vandal's opening "Listen…"). Duration now sits right on the cue's 3-second target once the head/tail are ffmpeg-faded.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/gd_salman-13705087/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=355381">SOLEMAN ALI</a> from <a href="https://pixabay.com/sound-effects//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=355381">Pixabay</a>
```

Plain-text fallback: *Tension stinger ambience by SOLEMAN ALI from Pixabay (https://pixabay.com).*

---

## Tavern ambience.mp3

- **Source**: Pixabay — uploader [`freesound_community`](https://pixabay.com/users/freesound_community-46691455/), Pixabay sound ID 73008
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 37.5 s
- **Status**: Registered for the Tier-2 "distant tavern hum (crowd murmur, mugs)" overlay in the 2026-06-16 cold open. Long enough to seamless-loop under a full cold-open beat.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/freesound_community-46691455/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=73008">freesound_community</a> from <a href="https://pixabay.com/sound-effects//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=73008">Pixabay</a>
```

Plain-text fallback: *Tavern ambience by freesound_community from Pixabay (https://pixabay.com).*

---

## Ascending harp bridge.mp3

- **Source**: Pixabay — uploader [`freesound_community`](https://pixabay.com/users/freesound_community-46691455/), Pixabay sound ID 40490
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 4.27 s (locally re-encoded — 1.77 s of head silence and 2.94 s of tail silence trimmed off the original 8.98 s Pixabay download; silence boundaries detected via `ffmpeg -af silencedetect=noise=-40dB`)
- **Status**: Candidate for the Tier-1 `[STING: bridge — 2s]` cue (18 uses — between acts within a session). Ascending harp phrase; slightly longer than the cue's 2 s target, but the natural phrase length reads better than a hard truncation. May shorten further at concat time if it drags.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/freesound_community-46691455/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=40490">freesound_community</a> from <a href="https://pixabay.com//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=40490">Pixabay</a>
```

Plain-text fallback: *Ascending harp bridge by freesound_community from Pixabay (https://pixabay.com).*

---

## Minor swell.mp3

- **Source**: Pixabay — uploader [`Rson201`](https://pixabay.com/users/rson201-55690538/), Pixabay sound ID 553814
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 9.58 s (locally re-encoded — head and tail silence trimmed via `ffmpeg silencedetect` from the original 10.68 s Pixabay download)
- **Status**: Candidate for the Tier-1 `[MUSIC: minor swell — 4s]` cue (10 uses — the reflective breath after the last narrative beat, before Vandal's closing "Rest well tonight, heroes." signature). Runs longer than the 4 s cue calls for; the audio pipeline will either fade in on the peak portion (~5 s in) or overlap the tail into the closing signature.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/rson201-55690538/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=553814">Rson201</a> from <a href="https://pixabay.com/sound-effects//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=553814">Pixabay</a>
```

Plain-text fallback: *Deep rising cinematic swell by Rson201 from Pixabay (https://pixabay.com).*

---

## Cave drip.mp3

- **Source**: Pixabay — uploader [`solarmusic`](https://pixabay.com/users/solarmusic-27851065/), Pixabay sound ID 114694
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 20.08 s (locally re-encoded — 3.5 s of tail silence trimmed off the original 23.6 s Pixabay download)
- **Status**: Registered for the Tier-2 "slow water drip on stone (cave)" overlay in the 2025-12-07 cold open. Long enough to loop under the cold-open beat under a layer of `Fireplace.mp3`.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/solarmusic-27851065/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=114694">solarmusic</a> from <a href="https://pixabay.com/sound-effects//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=114694">Pixabay</a>
```

Plain-text fallback: *Cave drip ambience by solarmusic from Pixabay (https://pixabay.com).*

---

## Wind through trees.mp3

- **Source**: Pixabay — uploader [`Traian Mitroi` (`traian1984`)](https://pixabay.com/users/traian1984-41907904/), Pixabay sound ID 186986
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 86.08 s (locally re-encoded — head/tail silence trimmed from the original 90.24 s Pixabay download)
- **Status**: Registered as the Tier-2 "wind — thin, high (pine forest)" overlay. Covers cold-open cues in 2025-11-12 (pine forest ambience under Vandal's opening) and 2026-01-27 (aboard Zephyros's floating tower). Long enough to loop under a full cold-open beat.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/traian1984-41907904/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=186986">Traian Mitroi</a> from <a href="https://pixabay.com//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=186986">Pixabay</a>
```

Plain-text fallback: *Wind through trees ambience by Traian Mitroi from Pixabay (https://pixabay.com).*

---

## Wind over wheat.mp3

- **Source**: Pixabay — uploader [`freesound_community`](https://pixabay.com/users/freesound_community-46691455/), Pixabay sound ID 7159
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 132.18 s (locally re-encoded — head/tail silence trimmed from the original 137.66 s Pixabay download)
- **Status**: Registered as the Tier-2 "wind — soft, over wheat" overlay for the 2026-03-08 cold open (`[MUSIC: low ember bed; a soft wind moving over ripe wheat]`). Long enough to loop under a full cold-open beat.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/freesound_community-46691455/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=7159">freesound_community</a> from <a href="https://pixabay.com//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=7159">Pixabay</a>
```

Plain-text fallback: *Wheat in the wind ambience by freesound_community from Pixabay (https://pixabay.com).*

---

## Mist-damp wind.mp3

- **Source**: Pixabay — uploader [`Aman Kumar` (`tanweraman`)](https://pixabay.com/users/tanweraman-29554143/), Pixabay sound ID 350417
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 32.39 s (no trimming needed — no silence detected)
- **Status**: Registered as the Tier-2 "wind — mist-wet" overlay for the 2026-05-12 cold open (`[MUSIC: low ember bed; a mist-damp hush, one far-off drunken voice]`). Filename is "desert wind" on Pixabay but the recording reads as a damp atmospheric wind — the auditioning was the important step. Long enough to loop under a cold-open beat.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/tanweraman-29554143/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=350417">Aman Kumar</a> from <a href="https://pixabay.com/sound-effects//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=350417">Pixabay</a>
```

Plain-text fallback: *Ambient wind by Aman Kumar from Pixabay (https://pixabay.com).*

---

## Rain.mp3

- **Source**: Pixabay — uploader [`DRAGON-STUDIO`](https://pixabay.com/users/dragon-studio-38165424/), Pixabay sound ID 398653
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 180.02 s (no trimming needed — no silence detected; the file is an explicit seamless-loop upload)
- **Status**: Registered as the Tier-2 "rain" overlay for the 2026-02-10 cold open (`[MUSIC: low ember bed; rain thickening, and the far-off roll of wrong-coloured thunder]`). Thunder layer is not yet added and will need a separate asset if we want it.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/dragon-studio-38165424/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=398653">DRAGON-STUDIO</a> from <a href="https://pixabay.com/sound-effects//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=398653">Pixabay</a>
```

Plain-text fallback: *Calming rain loop by DRAGON-STUDIO from Pixabay (https://pixabay.com).*

---

## Hell-fire crackle.mp3

- **Source**: Pixabay — uploader [`floraphonic`](https://pixabay.com/users/floraphonic-38928062/), Pixabay sound ID 188211
- **License**: Pixabay Content License — <https://pixabay.com/service/license-summary/>
- **Duration**: 114.96 s (no trimming needed — clean loop-ready recording, no silence detected)
- **Status**: Registered as the Tier-2 "hell-fire crackle" overlay for the 2026-01-13 cold open (`[MUSIC: low ember bed; a slow crackle of embers, and something hissing beneath the earth]`). Wired on the "hissing" keyword.

**Attribution** (voluntary per the Pixabay Content License):

```html
Sound Effect by <a href="https://pixabay.com/users/floraphonic-38928062/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=188211">floraphonic</a> from <a href="https://pixabay.com/sound-effects//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=188211">Pixabay</a>
```

Plain-text fallback: *Burning fire loop by floraphonic from Pixabay (https://pixabay.com).*
