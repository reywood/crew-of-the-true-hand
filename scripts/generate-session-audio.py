#!/usr/bin/env python3
"""
Generate an audio recap for a session from a "Tales of the True Hand" script.

Reads   summaries/audio-scripts/YYYY-MM-DD.md
Writes  summaries/audio/YYYY-MM-DD/                         (artifact folder)
          ├── script.md            frozen copy of the script
          ├── manifest.json        voice, model, per-chunk hashes for cache
          ├── chunks/NNNN.mp3      persistent per-speech-line TTS output
          └── final.mp3            stitched output with music/stings layered

Cache behavior:
    Each speech chunk's hash = sha256(voice_id + model_id + delivery_preset + text).
    On re-run, chunks whose hash still matches the manifest are reused — no
    ElevenLabs call. Editing a single line in the script re-TTSes only that
    chunk. Change --voice or --model to invalidate everything.

Music / sting layering (v2):
    STING cues → replaced by the matching asset in summaries/audio/library/.
    Discrete MUSIC cues (signature theme, minor swell, outro theme) → played
    inline at low mixed volume. Sustained under-beds (hearth ambience mixed
    under speech) are NOT handled here — that's v3 sidechain-mix work.

Requires:
    pip install elevenlabs
    ffmpeg on PATH
    ELEVENLABS_API_KEY (env or .env at project root)
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv(ROOT / ".env")

try:
    from elevenlabs.client import ElevenLabs
except ImportError:
    print("ERROR: elevenlabs not installed. pip install elevenlabs", file=sys.stderr)
    sys.exit(2)


SCRIPTS_DIR = ROOT / "summaries" / "audio-scripts"
AUDIO_DIR = ROOT / "summaries" / "audio"
LIBRARY_DIR = AUDIO_DIR / "library"

DEFAULT_VOICE_ID = "tEo3d4j7gzVojBL5Z4Pt"  # Cormac (Irish Fantasy Storyteller)
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"

# Volume levels (in dB) for library assets relative to the speech track.
# Speech chunks are left at 0 dB. Music / sting elements are duckedto sit under
# the narration without competing.
MUSIC_INTRO_DB = -6.0    # signature theme — brighter, near speech level
MUSIC_MID_DB = -8.0      # minor swell — pushed under the closing line
MUSIC_OUTRO_DB = -4.0    # outro theme — full swell, closer to speech level
STING_CHIME_DB = -5.0
STING_BRIDGE_DB = -6.0
STING_LOW_CHORD_DB = -3.0  # cold-open tag — wants to hit

# --------------------------------------------------------------------------
# delivery presets (unchanged from v1)
# --------------------------------------------------------------------------

_D = lambda stab, sim, style, boost=True: {
    "stability": stab, "similarity_boost": sim, "style": style, "use_speaker_boost": boost,
}
DELIVERY_PRESETS = {
    "default":         _D(0.55, 0.75, 0.40),
    "hushed":          _D(0.25, 0.75, 0.60),
    "murmured":        _D(0.20, 0.75, 0.65),
    "conspiratorial":  _D(0.25, 0.75, 0.65),
    "confidential":    _D(0.30, 0.75, 0.60),
    "quiet":           _D(0.45, 0.75, 0.45),
    "quieter":         _D(0.45, 0.75, 0.45),
    "softer":          _D(0.55, 0.75, 0.35),
    "low":             _D(0.40, 0.75, 0.50),
    "grave":           _D(0.35, 0.75, 0.55),
    "cold":            _D(0.25, 0.75, 0.65),
    "chilling":        _D(0.25, 0.70, 0.70),
    "dropping":        _D(0.35, 0.75, 0.55),
    "ominous":         _D(0.35, 0.75, 0.60),
    "darker":          _D(0.35, 0.75, 0.60),
    "bright":          _D(0.65, 0.75, 0.55),
    "theatrical":      _D(0.45, 0.75, 0.65),
    "storyteller":     _D(0.55, 0.75, 0.50),
    "signature":       _D(0.65, 0.75, 0.50),
    "rising":          _D(0.40, 0.75, 0.65),
    "quickening":      _D(0.35, 0.75, 0.65),
    "urgent":          _D(0.25, 0.75, 0.70),
    "quoted":          _D(0.20, 0.70, 0.75),
    "reflective":      _D(0.65, 0.75, 0.35),
    "warm":            _D(0.60, 0.75, 0.40),
    "gently":          _D(0.65, 0.75, 0.35),
    "closing":         _D(0.65, 0.75, 0.40),
    "reverent":        _D(0.60, 0.75, 0.40),
    "amused":          _D(0.45, 0.75, 0.55),
    "sly":             _D(0.40, 0.75, 0.60),
    "dry":             _D(0.55, 0.75, 0.45),
    "measured":        _D(0.60, 0.75, 0.35),
    "steadier":        _D(0.60, 0.75, 0.35),
    "plain":           _D(0.60, 0.75, 0.30),
    "workmanlike":     _D(0.60, 0.75, 0.30),
    "wondering":       _D(0.45, 0.75, 0.50),
    "wonder":          _D(0.45, 0.75, 0.50),
    "curious":         _D(0.50, 0.75, 0.45),
    "leaning":         _D(0.45, 0.75, 0.55),
    "shifting":        _D(0.50, 0.75, 0.45),
    "drawing":         _D(0.50, 0.75, 0.45),
    "drawn":           _D(0.50, 0.75, 0.45),
    "personal":        _D(0.55, 0.75, 0.40),
    "unfolding":       _D(0.55, 0.75, 0.45),
    "telling":         _D(0.55, 0.75, 0.45),
    "admiring":        _D(0.50, 0.75, 0.50),
    "revenant":        _D(0.40, 0.75, 0.55),
    "savoring":        _D(0.50, 0.75, 0.55),
    "taut":            _D(0.35, 0.75, 0.60),
    "hoarse":          _D(0.30, 0.75, 0.60),
    "gathering":       _D(0.55, 0.75, 0.45),
    "beat":            _D(0.55, 0.75, 0.35),
    "aside":           _D(0.55, 0.75, 0.40),
}


def resolve_delivery(cue: str):
    """Return (delivery_key, voice_settings). Falls to 'default'."""
    if not cue:
        return "default", DELIVERY_PRESETS["default"]
    for word in re.findall(r"[a-zA-Z']+", cue.lower()):
        if word in DELIVERY_PRESETS:
            return word, DELIVERY_PRESETS[word]
    return "default", DELIVERY_PRESETS["default"]


# --------------------------------------------------------------------------
# library asset resolution
# --------------------------------------------------------------------------

STING_ASSETS = {
    # match keyword → (asset filename, mix volume in dB, use full clip?
    #                  or (start_sec, dur_sec) segment)
    "chime":            ("Ship bell — two chimes.mp3",  STING_CHIME_DB,     None),
    "bridge":           ("Ascending harp bridge.mp3",   STING_BRIDGE_DB,    None),
    "sharp low chord":  ("Tension stinger — ambience.mp3", STING_LOW_CHORD_DB, None),
}

# Music cues that we handle inline (v2). Sustained beds are NOT here — they
# need v3 sidechain mixing under the speech track.
MUSIC_ASSETS = {
    "signature theme": ("The Britons.mp3", MUSIC_INTRO_DB, (0.0, 8.0)),   # first 8 s
    "outro theme":     ("The Britons.mp3", MUSIC_OUTRO_DB, (300.0, 6.7)),  # last swell
    "minor swell":     ("Minor swell.mp3", MUSIC_MID_DB,   None),
}


def resolve_sting_cue(label: str):
    """Return (asset_path, volume_db, segment_or_None) or None if no match."""
    lo = label.lower()
    # Order matters: longer/more specific keys first.
    for key in sorted(STING_ASSETS.keys(), key=lambda k: -len(k)):
        if key in lo:
            filename, db, segment = STING_ASSETS[key]
            return (LIBRARY_DIR / filename, db, segment)
    return None


def resolve_music_cue(label: str):
    """Return (asset_path, volume_db, segment_or_None) or None if no match /
    if this cue is a sustained bed we don't handle in v2."""
    lo = label.lower()
    for key in sorted(MUSIC_ASSETS.keys(), key=lambda k: -len(k)):
        if key in lo:
            filename, db, segment = MUSIC_ASSETS[key]
            return (LIBRARY_DIR / filename, db, segment)
    return None


# --------------------------------------------------------------------------
# script parsing
# --------------------------------------------------------------------------

def parse_script(text: str):
    """Turn the storyteller script into a linear list of events:
        ("speak",  text, delivery_cue)
        ("sting",  cue_label)          — replaced with asset if resolvable
        ("music",  cue_label)          — same, for MUSIC cues
        ("silence", duration_ms)
    """
    events = []

    def add_silence(ms: int):
        if events and events[-1][0] == "silence":
            events[-1] = ("silence", events[-1][1] + ms)
        else:
            events.append(("silence", ms))

    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if set(line) == {"-"}:
            continue

        if line.startswith("[") and line.endswith("]"):
            inner = line[1:-1].strip()
            key = inner.split(":", 1)[0].split()[0].upper()
            label = inner.split(":", 1)[1].strip() if ":" in inner else ""
            if key == "MUSIC":
                events.append(("music", label))
                continue
            if key == "STING":
                events.append(("sting", label))
                continue
            if key == "SFX":
                add_silence(350)
                continue
            if key == "PAUSE":
                m = re.search(r"(\d+(?:\.\d+)?)\s*s", inner)
                dur_ms = int(float(m.group(1)) * 1000) if m else 500
                add_silence(dur_ms)
                continue
            continue

        if line.startswith("VANDAL:"):
            content = line[len("VANDAL:"):].strip()
            m = re.match(r"^\*\((.+?)\)\*\s*(.*)$", content)
            if m:
                delivery = m.group(1)
                spoken = m.group(2).strip()
            else:
                delivery = ""
                spoken = content
            spoken = re.sub(r"\*+", "", spoken).strip()
            if spoken:
                events.append(("speak", spoken, delivery))
                events.append(("silence", 250))

    return events


# --------------------------------------------------------------------------
# hashing / manifest
# --------------------------------------------------------------------------

def chunk_hash(text: str, voice_id: str, model_id: str, delivery_key: str) -> str:
    h = hashlib.sha256()
    h.update(voice_id.encode("utf-8"))
    h.update(b"\x00")
    h.update(model_id.encode("utf-8"))
    h.update(b"\x00")
    h.update(delivery_key.encode("utf-8"))
    # Include the preset numbers so preset tweaks invalidate cached chunks.
    preset = DELIVERY_PRESETS[delivery_key]
    h.update(json.dumps(preset, sort_keys=True).encode("utf-8"))
    h.update(b"\x00")
    h.update(text.encode("utf-8"))
    return h.hexdigest()


def load_manifest(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"WARN: {path} unreadable, treating as empty", file=sys.stderr)
    return {}


def save_manifest(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


# --------------------------------------------------------------------------
# ffmpeg helpers
# --------------------------------------------------------------------------

def synth_silence(duration_ms: int, out_path: Path) -> Path:
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=mono",
        "-t", f"{duration_ms / 1000.0}",
        "-c:a", "libmp3lame", "-b:a", "128k",
        "-loglevel", "error",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)
    return out_path


def render_asset(source: Path, out_path: Path, volume_db: float,
                  segment) -> Path:
    """Extract a clip (or the full asset), mix down to mono 128kbps, apply
    a volume adjustment, and add a short fade in/out so it sits nicely
    next to speech. Cached — skips if out_path already exists."""
    if out_path.exists():
        return out_path
    afilters = []
    if segment is not None:
        pass  # handled via -ss / -t below
    afilters.append(f"volume={volume_db}dB")
    afilters.append("afade=t=in:st=0:d=0.15")
    # afade out at end requires knowing duration; use dynaudnorm or just skip.
    # For now, a symmetric fade-in only.
    cmd = ["ffmpeg", "-y"]
    if segment is not None:
        start, dur = segment
        cmd += ["-ss", str(start), "-t", str(dur)]
    cmd += ["-i", str(source),
            "-af", ",".join(afilters),
            "-ac", "1", "-ar", "44100",
            "-c:a", "libmp3lame", "-b:a", "128k",
            "-loglevel", "error",
            str(out_path)]
    subprocess.run(cmd, check=True)
    return out_path


def concat_mp3s(chunk_paths, output_path: Path) -> None:
    inputs = []
    for p in chunk_paths:
        inputs.extend(["-i", str(p)])
    filter_str = (
        "".join(f"[{i}:a]" for i in range(len(chunk_paths)))
        + f"concat=n={len(chunk_paths)}:v=0:a=1[out]"
    )
    cmd = ["ffmpeg", "-y", *inputs,
           "-filter_complex", filter_str, "-map", "[out]",
           "-ac", "1", "-ar", "44100",
           "-c:a", "libmp3lame", "-b:a", "128k",
           "-loglevel", "error",
           str(output_path)]
    subprocess.run(cmd, check=True)


# --------------------------------------------------------------------------
# TTS with cache
# --------------------------------------------------------------------------

def tts_chunk(client, text: str, voice_id: str, model_id: str,
              voice_settings: dict, previous_text: str, next_text: str,
              out_path: Path) -> None:
    kwargs = dict(text=text, voice_id=voice_id, model_id=model_id,
                  output_format=DEFAULT_OUTPUT_FORMAT,
                  voice_settings=voice_settings)
    if previous_text:
        kwargs["previous_text"] = previous_text[-600:]
    if next_text:
        kwargs["next_text"] = next_text[:200]
    audio = client.text_to_speech.convert(**kwargs)
    with out_path.open("wb") as f:
        for chunk in audio:
            f.write(chunk)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[1] if __doc__ else "",
    )
    parser.add_argument("date", help="Session date, YYYY-MM-DD")
    parser.add_argument("--voice", default=DEFAULT_VOICE_ID,
                        help="ElevenLabs voice_id (default: Cormac).")
    parser.add_argument("--model", default=DEFAULT_MODEL_ID,
                        help="ElevenLabs model_id.")
    parser.add_argument("--force", action="store_true",
                        help="Rebuild final.mp3 even if it exists. Speech "
                        "chunks are still cache-checked; use --force-tts to "
                        "invalidate them too.")
    parser.add_argument("--force-tts", action="store_true",
                        help="Invalidate the TTS cache and re-call ElevenLabs "
                        "for every speech chunk.")
    parser.add_argument("--no-music", action="store_true",
                        help="Skip music/sting layering — voice only.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse the script but don't call ElevenLabs "
                        "or stitch anything.")
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")

    script_path = SCRIPTS_DIR / f"{args.date}.md"
    if not script_path.exists():
        print(f"ERROR: script not found: {script_path}", file=sys.stderr)
        sys.exit(1)

    session_dir = AUDIO_DIR / args.date
    chunks_dir = session_dir / "chunks"
    manifest_path = session_dir / "manifest.json"
    final_path = session_dir / "final.mp3"
    frozen_script_path = session_dir / "script.md"

    if final_path.exists() and not args.force and not args.force_tts and not args.dry_run:
        print(f"{final_path} exists — use --force to rebuild.")
        return 0

    session_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(script_path, frozen_script_path)

    text = script_path.read_text(encoding="utf-8")
    events = parse_script(text)
    speak_events = [e for e in events if e[0] == "speak"]
    total_chars = sum(len(e[1]) for e in speak_events)
    print(f"[{args.date}] parsed {len(speak_events)} speech chunks "
          f"({total_chars} chars), "
          f"{sum(1 for e in events if e[0] == 'sting')} stings, "
          f"{sum(1 for e in events if e[0] == 'music')} music cues")

    if args.dry_run:
        for e in events[:30]:
            print(f"  {e}")
        return 0

    manifest = load_manifest(manifest_path)
    if args.force_tts:
        manifest = {}
    existing_chunks = manifest.get("chunks", {})  # hash → chunk_id (str)
    manifest_out = {
        "date": args.date,
        "voice_id": args.voice,
        "model_id": args.model,
        "chunks": {},
    }

    client = None  # lazy — don't require the API key if everything's cached

    with tempfile.TemporaryDirectory(prefix="tales-") as tmp:
        tmp_dir = Path(tmp)
        silence_cache = tmp_dir / "silences"
        silence_cache.mkdir()
        asset_cache = tmp_dir / "assets"
        asset_cache.mkdir()

        speech_texts = [ev[1] for ev in events if ev[0] == "speak"]

        stitched_paths = []
        speech_idx = 0

        for i, ev in enumerate(events):
            kind = ev[0]
            if kind == "speak":
                _, txt, delivery = ev
                delivery_key, voice_settings = resolve_delivery(delivery)
                h = chunk_hash(txt, args.voice, args.model, delivery_key)
                chunk_id = f"{speech_idx + 1:04d}"
                chunk_path = chunks_dir / f"{chunk_id}.mp3"

                if h in existing_chunks and (chunks_dir / f"{existing_chunks[h]}.mp3").exists():
                    # Reuse the cached chunk under its original filename.
                    cached_id = existing_chunks[h]
                    cached_path = chunks_dir / f"{cached_id}.mp3"
                    if cached_id != chunk_id:
                        # Speech ordering changed but content matches an old
                        # chunk — copy under the new name so lookups stay
                        # position-stable for reruns.
                        shutil.copy2(cached_path, chunk_path)
                    print(f"  [{speech_idx + 1}/{len(speech_texts)}] "
                          f"({delivery_key}) [cache hit] "
                          f"{txt[:50].replace(chr(10), ' ')}...")
                else:
                    if client is None:
                        if not api_key:
                            print("ERROR: ELEVENLABS_API_KEY not set and cache "
                                  "miss occurred. Add to .env or pass --dry-run.",
                                  file=sys.stderr)
                            return 1
                        client = ElevenLabs(api_key=api_key)
                    prev_txt = speech_texts[speech_idx - 1] if speech_idx > 0 else ""
                    next_txt = (speech_texts[speech_idx + 1]
                                if speech_idx + 1 < len(speech_texts) else "")
                    print(f"  [{speech_idx + 1}/{len(speech_texts)}] "
                          f"({delivery_key}) [TTS] "
                          f"{txt[:50].replace(chr(10), ' ')}...")
                    try:
                        tts_chunk(client, txt, args.voice, args.model,
                                  voice_settings, prev_txt, next_txt, chunk_path)
                    except Exception as e:
                        print(f"  TTS error on chunk {chunk_id}: {e}",
                              file=sys.stderr)
                        return 1

                manifest_out["chunks"][h] = chunk_id
                stitched_paths.append(chunk_path)
                speech_idx += 1

            elif kind == "silence":
                dur = ev[1]
                sil_path = silence_cache / f"silence-{dur}.mp3"
                if not sil_path.exists():
                    synth_silence(dur, sil_path)
                stitched_paths.append(sil_path)

            elif kind == "sting":
                label = ev[1]
                if args.no_music:
                    stitched_paths.append(synth_silence(400, silence_cache / "sting-fallback.mp3")
                                          if not (silence_cache / "sting-fallback.mp3").exists()
                                          else silence_cache / "sting-fallback.mp3")
                    continue
                resolved = resolve_sting_cue(label)
                if resolved is None:
                    # Unrecognized sting — fall back to a short silence.
                    fallback = silence_cache / "sting-unknown.mp3"
                    if not fallback.exists():
                        synth_silence(500, fallback)
                    stitched_paths.append(fallback)
                    continue
                src, db, segment = resolved
                slug = re.sub(r"[^a-z0-9]+", "-", label.lower())[:40].strip("-")
                asset_path = asset_cache / f"sting-{slug}.mp3"
                render_asset(src, asset_path, db, segment)
                stitched_paths.append(asset_path)

            elif kind == "music":
                label = ev[1]
                if args.no_music:
                    continue
                resolved = resolve_music_cue(label)
                if resolved is None:
                    # Sustained beds and unhandled music — no inline element.
                    # (Deliberate: v2 doesn't sidechain-mix beds under speech.)
                    continue
                src, db, segment = resolved
                slug = re.sub(r"[^a-z0-9]+", "-", label.lower())[:40].strip("-")
                asset_path = asset_cache / f"music-{slug}.mp3"
                render_asset(src, asset_path, db, segment)
                stitched_paths.append(asset_path)

        save_manifest(manifest_path, manifest_out)
        print(f"Stitching {len(stitched_paths)} elements → {final_path.name}")
        concat_mp3s(stitched_paths, final_path)

    size_kb = final_path.stat().st_size / 1024
    print(f"Wrote {final_path} ({size_kb:.0f} KB)")
    n_speech = len(manifest_out["chunks"])
    print(f"  Cached {n_speech} speech chunks under {chunks_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
