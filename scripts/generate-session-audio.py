#!/usr/bin/env python3
"""
Generate an audio recap for a session from a Wazoo Report script.

Reads   summaries/audio-scripts/YYYY-MM-DD.md
Writes  summaries/audio/YYYY-MM-DD.mp3

Requires:
    pip install elevenlabs
    ffmpeg on PATH
    ELEVENLABS_API_KEY (env or .env at project root)

Pilot v1 notes:
    - Voice-only. Stings and SFX collapse to short silences; music beds
      are skipped entirely so we can judge the voice on its own.
    - Delivery cues in the script — `*(hushed, urgent)*` — are mapped
      to ElevenLabs voice-setting presets. Extend DELIVERY_PRESETS to
      taste.
    - Once the voice sounds right, v2 layers music/sfx.
"""

import argparse
import os
import re
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

# Default voice: "Adam" — warm, mid-40s male narrator. A serviceable Vandal.
# Swap via --voice <voice_id> once you audition alternatives.
DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"

# Delivery cue keyword → ElevenLabs voice_settings. First recognized keyword
# in the cue wins. Everything not recognized falls to "default".
#
# Wider stability/style spreads than the v1 pilot: pushing stability lower
# and style higher on the emotional extremes to actually make the delivery
# audible in the mix. Storyteller register lives around 0.55 stability with
# moderate style (0.40); intimate/hushed pushes down; theatrical/urgent
# pushes style up; quoted lines push both hard for a distinct voice-inside-
# the-voice moment.
_D = lambda stab, sim, style, boost=True: {
    "stability": stab, "similarity_boost": sim, "style": style, "use_speaker_boost": boost,
}
DELIVERY_PRESETS = {
    "default":         _D(0.55, 0.75, 0.40),
    # Intimate / hushed
    "hushed":          _D(0.25, 0.75, 0.60),
    "murmured":        _D(0.20, 0.75, 0.65),
    "conspiratorial":  _D(0.25, 0.75, 0.65),
    "confidential":    _D(0.30, 0.75, 0.60),
    "quiet":           _D(0.45, 0.75, 0.45),
    "quieter":         _D(0.45, 0.75, 0.45),
    "softer":          _D(0.55, 0.75, 0.35),
    "low":             _D(0.40, 0.75, 0.50),
    # Cold / grave / dropping
    "grave":           _D(0.35, 0.75, 0.55),
    "cold":            _D(0.25, 0.75, 0.65),
    "chilling":        _D(0.25, 0.70, 0.70),
    "dropping":        _D(0.35, 0.75, 0.55),
    "ominous":         _D(0.35, 0.75, 0.60),
    "darker":          _D(0.35, 0.75, 0.60),
    # Bright / theatrical / storyteller
    "bright":          _D(0.65, 0.75, 0.55),
    "theatrical":      _D(0.45, 0.75, 0.65),
    "storyteller":     _D(0.55, 0.75, 0.50),
    "signature":       _D(0.65, 0.75, 0.50),
    "rising":          _D(0.40, 0.75, 0.65),
    "quickening":      _D(0.35, 0.75, 0.65),
    "urgent":          _D(0.25, 0.75, 0.70),
    # Quoted — Vandal doing a character voice inside his own
    "quoted":          _D(0.20, 0.70, 0.75),
    # Reflective / warm / winding
    "reflective":      _D(0.65, 0.75, 0.35),
    "warm":            _D(0.60, 0.75, 0.40),
    "gently":          _D(0.65, 0.75, 0.35),
    "closing":         _D(0.65, 0.75, 0.40),
    "reverent":        _D(0.60, 0.75, 0.40),
    # Sly / amused / measured
    "amused":          _D(0.45, 0.75, 0.55),
    "sly":             _D(0.40, 0.75, 0.60),
    "dry":             _D(0.55, 0.75, 0.45),
    "measured":        _D(0.60, 0.75, 0.35),
    "steadier":        _D(0.60, 0.75, 0.35),
    "plain":           _D(0.60, 0.75, 0.30),
    "workmanlike":     _D(0.60, 0.75, 0.30),
    # Curiosity / shift / draw-in
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


def resolve_delivery(cue: str) -> dict:
    if not cue:
        return DELIVERY_PRESETS["default"]
    for word in re.findall(r"[a-zA-Z']+", cue.lower()):
        if word in DELIVERY_PRESETS:
            return DELIVERY_PRESETS[word]
    return DELIVERY_PRESETS["default"]


def parse_script(text: str):
    """Turn a Wazoo Report markdown script into a list of events:
        ("speak", text, delivery_cue)
        ("silence", duration_ms)
    """
    events = []
    prev_was_silence = False

    def add_silence(ms: int):
        nonlocal prev_was_silence
        # Merge adjacent silences so we don't stack pauses over stings.
        if events and events[-1][0] == "silence":
            events[-1] = ("silence", events[-1][1] + ms)
        else:
            events.append(("silence", ms))
        prev_was_silence = True

    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if set(line) == {"-"}:  # "---" divider
            continue

        # Stage directions: whole line wrapped in [ ]
        if line.startswith("[") and line.endswith("]"):
            inner = line[1:-1].strip()
            key = inner.split(":", 1)[0].split()[0].upper()
            if key == "MUSIC":
                # Pilot v1: skip music beds.
                continue
            if key == "STING":
                add_silence(500)
                continue
            if key == "SFX":
                add_silence(350)
                continue
            if key == "PAUSE":
                m = re.search(r"(\d+(?:\.\d+)?)\s*s", inner)
                dur_ms = int(float(m.group(1)) * 1000) if m else 500
                add_silence(dur_ms)
                continue
            # Unknown / structural direction — ignore.
            continue

        # VANDAL: lines are the actual speech.
        if line.startswith("VANDAL:"):
            content = line[len("VANDAL:"):].strip()
            # Extract *(cue)* prefix if present.
            m = re.match(r"^\*\((.+?)\)\*\s*(.*)$", content)
            if m:
                delivery = m.group(1)
                text = m.group(2).strip()
            else:
                delivery = ""
                text = content
            # Strip any remaining bold/italic markdown emphasis.
            text = re.sub(r"\*+", "", text).strip()
            if text:
                events.append(("speak", text, delivery))
                # Short breath between successive lines.
                events.append(("silence", 250))
                prev_was_silence = False

    return events


def synth_silence(duration_ms: int, cache_dir: Path) -> Path:
    """ffmpeg-generated silent MP3 of a given duration. Cached per length."""
    out = cache_dir / f"silence-{duration_ms}.mp3"
    if out.exists():
        return out
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=mono",
        "-t", f"{duration_ms / 1000.0}",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        "-loglevel", "error",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


def tts_chunk(client, text: str, voice_id: str, model_id: str,
              delivery: str, previous_text: str, next_text: str,
              out_path: Path) -> None:
    """Call ElevenLabs. Pass previous_text/next_text so the model continues
    prosody across chunks (short quoted lines especially benefit)."""
    voice_settings = resolve_delivery(delivery)
    kwargs = dict(
        text=text,
        voice_id=voice_id,
        model_id=model_id,
        output_format=DEFAULT_OUTPUT_FORMAT,
        voice_settings=voice_settings,
    )
    # Only the tail of previous_text matters for prosody — cap to keep
    # request size and cost sane.
    if previous_text:
        kwargs["previous_text"] = previous_text[-600:]
    if next_text:
        kwargs["next_text"] = next_text[:200]
    audio = client.text_to_speech.convert(**kwargs)
    with out_path.open("wb") as f:
        for chunk in audio:
            f.write(chunk)


def concat_mp3s(chunk_paths, output_path: Path) -> None:
    """Stitch a sequence of MP3s into one, forcing mono 44.1kHz 128kbps."""
    inputs = []
    for p in chunk_paths:
        inputs.extend(["-i", str(p)])
    filter_str = (
        "".join(f"[{i}:a]" for i in range(len(chunk_paths)))
        + f"concat=n={len(chunk_paths)}:v=0:a=1[out]"
    )
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[out]",
        "-ac", "1",
        "-ar", "44100",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        "-loglevel", "error",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1] if __doc__ else "")
    parser.add_argument("date", help="Session date, YYYY-MM-DD")
    parser.add_argument("--voice", default=DEFAULT_VOICE_ID,
                        help="ElevenLabs voice_id (default: Adam).")
    parser.add_argument("--model", default=DEFAULT_MODEL_ID,
                        help="ElevenLabs model_id.")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite an existing output file.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse the script but don't call ElevenLabs.")
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key and not args.dry_run:
        print("ERROR: ELEVENLABS_API_KEY not set.", file=sys.stderr)
        print("       Add it to .env or export it.", file=sys.stderr)
        sys.exit(2)

    script_path = SCRIPTS_DIR / f"{args.date}.md"
    if not script_path.exists():
        print(f"ERROR: script not found: {script_path}", file=sys.stderr)
        sys.exit(1)

    output_path = AUDIO_DIR / f"{args.date}.mp3"
    if output_path.exists() and not args.force:
        print(f"{output_path} exists — use --force to regenerate.")
        return 0
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    text = script_path.read_text(encoding="utf-8")
    events = parse_script(text)
    speak_events = [e for e in events if e[0] == "speak"]
    total_chars = sum(len(e[1]) for e in speak_events)
    print(f"[{args.date}] parsed {len(speak_events)} speech chunks "
          f"({total_chars} chars) + {len(events) - len(speak_events)} pauses")

    if args.dry_run:
        for e in events[:20]:
            print(f"  {e}")
        return 0

    client = ElevenLabs(api_key=api_key)

    with tempfile.TemporaryDirectory(prefix="wazoo-") as tmp:
        tmp_dir = Path(tmp)
        cache_dir = tmp_dir / "silences"
        cache_dir.mkdir()

        # Pre-collect the speech texts so we can pass previous/next context
        # into each call for prosodic continuity.
        speech_texts = [ev[1] for ev in events if ev[0] == "speak"]

        chunk_paths = []
        speech_idx = 0  # 0-based index into speech_texts
        for i, ev in enumerate(events):
            if ev[0] == "speak":
                _, txt, delivery = ev
                prev_txt = speech_texts[speech_idx - 1] if speech_idx > 0 else ""
                next_txt = speech_texts[speech_idx + 1] if speech_idx + 1 < len(speech_texts) else ""
                speech_idx += 1
                snippet = txt[:60].replace("\n", " ")
                print(f"  [{speech_idx}/{len(speech_texts)}] "
                      f"({delivery or 'default'}) {snippet}...")
                chunk_path = tmp_dir / f"chunk-{i:04d}.mp3"
                try:
                    tts_chunk(client, txt, args.voice, args.model, delivery,
                              prev_txt, next_txt, chunk_path)
                except Exception as e:
                    print(f"  TTS error on chunk {i}: {e}", file=sys.stderr)
                    return 1
                chunk_paths.append(chunk_path)
            elif ev[0] == "silence":
                silence_path = synth_silence(ev[1], cache_dir)
                chunk_paths.append(silence_path)

        print(f"Stitching {len(chunk_paths)} chunks → {output_path.name}")
        concat_mp3s(chunk_paths, output_path)

    size_kb = output_path.stat().st_size / 1024
    print(f"Wrote {output_path} ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
