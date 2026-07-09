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
# Speech chunks are left at 0 dB. Music / sting elements are ducked to sit
# under the narration without competing.
MUSIC_INTRO_DB = -6.0    # signature theme — brighter, near speech level
MUSIC_MID_DB = -8.0      # minor swell — pushed under the closing line
MUSIC_OUTRO_DB = -4.0    # outro theme — full swell, closer to speech level
STING_CHIME_DB = -5.0
STING_BRIDGE_DB = -6.0
STING_LOW_CHORD_DB = -3.0  # cold-open tag — wants to hit
# Sustained under-beds — much quieter, sit well below the narration.
HEARTH_BED_DB = -22.0        # crackling fire under a full act of speech
COLD_OPEN_HEARTH_DB = -24.0  # a touch quieter under the low-chord sting
COLD_OPEN_OVERLAY_DB = -20.0 # tavern/drip/bell overlay in cold-open ambience

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

# Music cues that we handle inline (v2/v3). The signature theme is NOT here —
# it's rendered as a bed span so it can fade under the title line instead of
# cutting off abruptly. The outro theme stays inline because it plays after
# all narration is done. The minor swell plays inline right before the closing.
MUSIC_ASSETS = {
    "outro theme":     ("The Britons.mp3", MUSIC_OUTRO_DB, (300.0, 6.7)),  # last swell
    "minor swell":     ("Minor swell.mp3", MUSIC_MID_DB,   None),
}

# Signature theme is rendered as its own bed span so it can play through and
# fade under the title line rather than ending abruptly. Uses the same Britons
# track, first 20 s.
SIGNATURE_ASSET = "The Britons.mp3"
SIGNATURE_SEGMENT = (0.0, 20.0)
SIGNATURE_DB = -12.0        # quiet enough to sit under Vandal's title line
SIGNATURE_FADE_OUT = 6.0    # long tail so it recedes gradually under narration
SIGNATURE_HEADROOM_MS = 2500  # play intro alone this long before speech comes in


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
    if this cue is a sustained bed we handle separately (see resolve_bed_start)."""
    lo = label.lower()
    for key in sorted(MUSIC_ASSETS.keys(), key=lambda k: -len(k)):
        if key in lo:
            filename, db, segment = MUSIC_ASSETS[key]
            return (LIBRARY_DIR / filename, db, segment)
    return None


# --------------------------------------------------------------------------
# sustained under-bed handling
# --------------------------------------------------------------------------

HEARTH_ASSET = "Fireplace.mp3"

# Cold-open ambience overlays. When a [MUSIC: low ember bed; <flavor>] cue
# appears, we start a hearth bed AND layer one of these on top per the flavor
# keyword. Unmatched flavors fall back to hearth-only.
BED_OVERLAY_ASSETS = {
    "tavern":               ("Tavern ambience.mp3",                COLD_OPEN_OVERLAY_DB),
    "drip":                 ("Cave drip.mp3",                      COLD_OPEN_OVERLAY_DB),
    "bell tolling, urgent": ("Church bell — single (musical).mp3", COLD_OPEN_OVERLAY_DB),
    "bell tolling, faint":  ("Church bell — single (film SFX).mp3", COLD_OPEN_OVERLAY_DB - 4.0),
    "bell tolling":         ("Church bell — single (film SFX).mp3", COLD_OPEN_OVERLAY_DB - 2.0),
    "wheat":                ("Wind over wheat.mp3",                COLD_OPEN_OVERLAY_DB),
    "mist":                 ("Mist-damp wind.mp3",                 COLD_OPEN_OVERLAY_DB),
    "damp":                 ("Mist-damp wind.mp3",                 COLD_OPEN_OVERLAY_DB),
    "rain":                 ("Rain.mp3",                           COLD_OPEN_OVERLAY_DB),
    "pine":                 ("Wind through trees.mp3",             COLD_OPEN_OVERLAY_DB),
    "wind":                 ("Wind through trees.mp3",             COLD_OPEN_OVERLAY_DB),
    # hell-fire crackle (2026-01-13): not yet in library. Cold-open bed
    # falls back to hearth-only for that one.
}


def resolve_bed_overlay(label: str):
    """Given a `[MUSIC: low ember bed; <flavor>]` label, return
    (overlay_path, volume_db) for the matching overlay, or None if no
    overlay is available. Hearth is always added by the caller."""
    lo = label.lower()
    for key in sorted(BED_OVERLAY_ASSETS.keys(), key=lambda k: -len(k)):
        if key in lo:
            filename, db = BED_OVERLAY_ASSETS[key]
            return (LIBRARY_DIR / filename, db)
    return None


def is_cold_open_bed_cue(label: str) -> bool:
    return "low ember bed" in label.lower()


def is_hearth_bed_start_cue(label: str) -> bool:
    lo = label.lower()
    return "settles under" in lo or "becomes bed" in lo


def is_signature_bed_cue(label: str) -> bool:
    """The signature-theme cue closes the cold-open bed AND opens a signature
    bed (Britons intro) that plays through the title line and fades out under
    the next bed transition."""
    return "signature theme" in label.lower()


def is_bed_end_cue(label: str) -> bool:
    """Cues that terminate any currently-playing bed. minor swell replaces
    the bed at the show's emotional close; outro theme wraps the show."""
    lo = label.lower()
    return "minor swell" in lo or "outro theme" in lo


def probe_duration_ms(path: Path) -> int:
    """ffprobe → duration in milliseconds. Returns 0 on failure."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return int(float(out) * 1000)
    except (subprocess.CalledProcessError, ValueError):
        return 0


def render_bed(hearth_path: Path, overlay_path, duration_sec: float,
                out_path: Path, hearth_db: float = HEARTH_BED_DB,
                overlay_db: float = COLD_OPEN_OVERLAY_DB) -> Path:
    """Build a bed of the given duration by looping the hearth asset (and,
    if provided, an overlay), setting per-track volumes, applying fade in
    and fade out. Written to out_path; returns out_path."""
    fade_in = 1.0
    fade_out = 1.5
    fade_out_start = max(0.0, duration_sec - fade_out)
    if overlay_path is not None:
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(hearth_path),
            "-stream_loop", "-1", "-i", str(overlay_path),
            "-filter_complex",
            f"[0:a]volume={hearth_db}dB,atrim=0:{duration_sec}[a0];"
            f"[1:a]volume={overlay_db}dB,atrim=0:{duration_sec}[a1];"
            f"[a0][a1]amix=inputs=2:duration=first:normalize=0,"
            f"afade=t=in:st=0:d={fade_in},"
            f"afade=t=out:st={fade_out_start}:d={fade_out}[out]",
            "-map", "[out]",
            "-ac", "1", "-ar", "44100",
            "-c:a", "libmp3lame", "-b:a", "128k",
            "-loglevel", "error",
            str(out_path),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(hearth_path),
            "-af",
            f"volume={hearth_db}dB,"
            f"atrim=0:{duration_sec},"
            f"afade=t=in:st=0:d={fade_in},"
            f"afade=t=out:st={fade_out_start}:d={fade_out}",
            "-ac", "1", "-ar", "44100",
            "-c:a", "libmp3lame", "-b:a", "128k",
            "-loglevel", "error",
            str(out_path),
        ]
    subprocess.run(cmd, check=True)
    return out_path


def mix_top_with_beds(top_path: Path, bed_specs, out_path: Path) -> None:
    """bed_specs: list of (bed_path, delay_ms). Mixes top_path (the speech +
    inline-music bus) with each bed at its start offset. Uses amix with
    normalize=0 so the top layer's level isn't attenuated by the mix."""
    if not bed_specs:
        shutil.copy2(top_path, out_path)
        return
    inputs = ["-i", str(top_path)]
    for bed_path, _ in bed_specs:
        inputs.extend(["-i", str(bed_path)])
    filters = []
    labels = ["[0:a]"]
    for i, (_, delay_ms) in enumerate(bed_specs, start=1):
        filters.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[b{i}]")
        labels.append(f"[b{i}]")
    n = len(bed_specs) + 1
    filters.append(
        f"{''.join(labels)}amix=inputs={n}:duration=first:"
        f"dropout_transition=0:normalize=0[out]"
    )
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[out]",
        "-ac", "1", "-ar", "44100",
        "-c:a", "libmp3lame", "-b:a", "128k",
        "-loglevel", "error",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)


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
                        help="Skip all music/sting layering — voice only. "
                        "Implies --no-beds.")
    parser.add_argument("--no-beds", action="store_true",
                        help="Skip sustained under-bed mixing (hearth ambience "
                        "and cold-open overlays). Inline stings and one-off "
                        "music cues still play. Useful to A/B a mix.")
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

        # --- Pass 1: resolve every event to a concrete audio element on
        # disk (speech chunk from cache or new TTS, silence, sting, inline
        # music) and capture its duration in ms. Bed cues are left as
        # markers with no audio element attached — they're consumed in
        # pass 2 to find the sustained under-bed spans.
        top_layer = []  # list of dicts: {"path": Path, "dur_ms": int, "kind": str, "label": str}
        bed_markers = []  # list of dicts: {"at_ms": int, "kind": "start_hearth"|"start_cold_open"|"end", "label": str}
        cursor_ms = 0
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
                    cached_id = existing_chunks[h]
                    cached_path = chunks_dir / f"{cached_id}.mp3"
                    if cached_id != chunk_id:
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
                dur_ms = probe_duration_ms(chunk_path)
                top_layer.append({"path": chunk_path, "dur_ms": dur_ms, "kind": "speak"})
                cursor_ms += dur_ms
                speech_idx += 1

            elif kind == "silence":
                dur = ev[1]
                sil_path = silence_cache / f"silence-{dur}.mp3"
                if not sil_path.exists():
                    synth_silence(dur, sil_path)
                top_layer.append({"path": sil_path, "dur_ms": dur, "kind": "silence"})
                cursor_ms += dur

            elif kind == "sting":
                label = ev[1]
                if args.no_music:
                    fb = silence_cache / "sting-fallback.mp3"
                    if not fb.exists():
                        synth_silence(400, fb)
                    top_layer.append({"path": fb, "dur_ms": 400, "kind": "sting"})
                    cursor_ms += 400
                    continue
                resolved = resolve_sting_cue(label)
                if resolved is None:
                    fallback = silence_cache / "sting-unknown.mp3"
                    if not fallback.exists():
                        synth_silence(500, fallback)
                    top_layer.append({"path": fallback, "dur_ms": 500, "kind": "sting"})
                    cursor_ms += 500
                    continue
                src, db, segment = resolved
                slug = re.sub(r"[^a-z0-9]+", "-", label.lower())[:40].strip("-")
                asset_path = asset_cache / f"sting-{slug}.mp3"
                render_asset(src, asset_path, db, segment)
                dur_ms = probe_duration_ms(asset_path)
                top_layer.append({"path": asset_path, "dur_ms": dur_ms, "kind": "sting"})
                cursor_ms += dur_ms

            elif kind == "music":
                label = ev[1]

                # Register bed markers at THIS cursor position, before
                # advancing for any inline element the cue may also carry.
                if not args.no_music and not args.no_beds:
                    if is_cold_open_bed_cue(label):
                        bed_markers.append({"at_ms": cursor_ms,
                                             "kind": "start_cold_open",
                                             "label": label})
                    elif is_hearth_bed_start_cue(label):
                        bed_markers.append({"at_ms": cursor_ms,
                                             "kind": "start_hearth",
                                             "label": label})
                    elif is_signature_bed_cue(label):
                        # Transition: closes the cold-open bed and opens the
                        # signature bed at the same position. Then inject a
                        # short silence into the top layer so the intro theme
                        # plays alone for a beat before the title-line speech
                        # comes in.
                        bed_markers.append({"at_ms": cursor_ms,
                                             "kind": "start_signature",
                                             "label": label})
                        headroom_path = silence_cache / f"signature-headroom-{SIGNATURE_HEADROOM_MS}.mp3"
                        if not headroom_path.exists():
                            synth_silence(SIGNATURE_HEADROOM_MS, headroom_path)
                        top_layer.append({"path": headroom_path,
                                           "dur_ms": SIGNATURE_HEADROOM_MS,
                                           "kind": "silence"})
                        cursor_ms += SIGNATURE_HEADROOM_MS
                    elif is_bed_end_cue(label):
                        bed_markers.append({"at_ms": cursor_ms,
                                             "kind": "end",
                                             "label": label})

                if args.no_music:
                    continue
                resolved = resolve_music_cue(label)
                if resolved is None:
                    continue
                src, db, segment = resolved
                slug = re.sub(r"[^a-z0-9]+", "-", label.lower())[:40].strip("-")
                asset_path = asset_cache / f"music-{slug}.mp3"
                render_asset(src, asset_path, db, segment)
                dur_ms = probe_duration_ms(asset_path)
                top_layer.append({"path": asset_path, "dur_ms": dur_ms, "kind": "music"})
                cursor_ms += dur_ms

        save_manifest(manifest_path, manifest_out)

        # --- Pass 2: resolve bed markers into concrete spans and render
        # each span's bed track. A cold-open marker overrides / restarts;
        # a hearth marker starts a new span; an end marker closes any open
        # span. Adjacent overlapping markers close the previous span at
        # this position before opening the new one.
        bed_specs = []  # list of (bed_path, delay_ms) for the final mix
        if not args.no_music and not args.no_beds:
            active = None
            marker_kind_to_type = {
                "start_cold_open": "cold_open",
                "start_hearth":    "hearth",
                "start_signature": "signature",
            }
            for m in bed_markers:
                if m["kind"] in marker_kind_to_type:
                    if active is not None:
                        active["end_ms"] = m["at_ms"]
                        if active["end_ms"] > active["start_ms"]:
                            bed_specs.append(_render_bed_span(active, asset_cache))
                    active = {
                        "start_ms": m["at_ms"],
                        "type": marker_kind_to_type[m["kind"]],
                        "label": m["label"],
                    }
                elif m["kind"] == "end":
                    if active is not None:
                        active["end_ms"] = m["at_ms"]
                        if active["end_ms"] > active["start_ms"]:
                            bed_specs.append(_render_bed_span(active, asset_cache))
                        active = None
            # If a span is still open at end of show, close it at total
            # cursor position (this shouldn't happen in well-formed scripts).
            if active is not None:
                active["end_ms"] = cursor_ms
                if active["end_ms"] > active["start_ms"]:
                    bed_specs.append(_render_bed_span(active, asset_cache))

        # --- Pass 3: concat the top layer to top.mp3, then mix in the
        # rendered beds at their offsets.
        top_path = tmp_dir / "top.mp3"
        top_paths = [e["path"] for e in top_layer]
        print(f"Concatenating {len(top_paths)} top-layer elements")
        concat_mp3s(top_paths, top_path)

        if bed_specs:
            print(f"Mixing {len(bed_specs)} under-bed span(s) → {final_path.name}")
            mix_top_with_beds(top_path, bed_specs, final_path)
        else:
            print(f"No under-beds → {final_path.name}")
            shutil.copy2(top_path, final_path)

    size_kb = final_path.stat().st_size / 1024
    print(f"Wrote {final_path} ({size_kb:.0f} KB)")
    n_speech = len(manifest_out["chunks"])
    print(f"  Cached {n_speech} speech chunks under {chunks_dir}")
    return 0


def _render_bed_span(span: dict, asset_cache: Path):
    """Render a single bed span (dict with start_ms, end_ms, type, label)
    into an MP3 in asset_cache. Returns (bed_path, delay_ms) for the mix."""
    duration_sec = (span["end_ms"] - span["start_ms"]) / 1000.0
    slug = span["type"]
    out_path = asset_cache / f"bed-{slug}-{int(duration_sec)}s.mp3"
    print(f"  bed span: {slug} — {duration_sec:.1f}s @ {span['start_ms'] / 1000:.1f}s")

    if span["type"] == "signature":
        # Signature theme intro: play from the start of Britons, extend across
        # the title line, and fade out over the tail so it recedes gradually
        # under narration instead of ending abruptly.
        _render_signature_bed(duration_sec, out_path)
    else:
        hearth_path = LIBRARY_DIR / HEARTH_ASSET
        overlay_path = None
        overlay_db = COLD_OPEN_OVERLAY_DB
        hearth_db = HEARTH_BED_DB
        if span["type"] == "cold_open":
            hearth_db = COLD_OPEN_HEARTH_DB
            overlay = resolve_bed_overlay(span["label"])
            if overlay is not None:
                overlay_path, overlay_db = overlay
        render_bed(hearth_path, overlay_path, duration_sec, out_path,
                   hearth_db=hearth_db, overlay_db=overlay_db)
    return (out_path, span["start_ms"])


def _render_signature_bed(duration_sec: float, out_path: Path) -> Path:
    """Render the signature-theme bed (Britons intro). Plays louder at the
    top so it punches, then fades gradually under the title line."""
    source = LIBRARY_DIR / SIGNATURE_ASSET
    start_offset, max_segment = SIGNATURE_SEGMENT
    segment = min(duration_sec, max_segment)
    fade_in = 0.4
    fade_out = min(SIGNATURE_FADE_OUT, max(1.5, segment * 0.6))
    fade_out_start = max(0.0, segment - fade_out)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_offset),
        "-t", str(segment),
        "-i", str(source),
        "-af",
        f"volume={SIGNATURE_DB}dB,"
        f"afade=t=in:st=0:d={fade_in},"
        f"afade=t=out:st={fade_out_start}:d={fade_out}",
        "-ac", "1", "-ar", "44100",
        "-c:a", "libmp3lame", "-b:a", "128k",
        "-loglevel", "error",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)
    return out_path


if __name__ == "__main__":
    sys.exit(main())
