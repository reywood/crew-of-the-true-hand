"""ffmpeg / ffprobe: every external audio operation.

Plain functions, not a class — there is one ffmpeg and no plausible second
implementation, so an interface here would be ceremony. Was spread through
scripts/generate-session-audio.py.

probe_duration_seconds() also replaces the site generator's private
_mp3_duration_seconds(), which shelled out to the same ffprobe command.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

# Sustained under-beds sit well below the narration. These are ABSOLUTE target
# mean levels (dBFS), not relative attenuations: each bed asset is normalized
# to hit its target regardless of its own inherent loudness (Fireplace.mp3 is
# ~-42 dBFS raw, Rain ~-20). Speech sits at ~-22 dBFS, so a hearth bed at -40
# reads ~18 dB under the voice — present in the gaps, unobtrusive under
# narration. See render_bed().
HEARTH_BED_DB = -40.0        # crackling fire under a full act of speech
COLD_OPEN_HEARTH_DB = -42.0  # a touch quieter under the low-chord sting
COLD_OPEN_OVERLAY_DB = -36.0 # tavern/drip/bell overlay in cold-open ambience


def probe_duration_seconds(path) -> float:
    """Best-effort media duration in seconds via ffprobe. Returns 0.0 on failure."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=15, check=True,
        ).stdout.strip()
        return float(out)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
            FileNotFoundError, ValueError):
        return 0.0


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


def _ffmeta_escape(value: str) -> str:
    """Escape a value for an ffmetadata file: =, ;, #, \\ and newlines."""
    for ch in ("\\", "=", ";", "#"):
        value = value.replace(ch, "\\" + ch)
    return value.replace("\n", " ").replace("\r", " ")


def embed_chapters(final_path: Path, chapters, total_ms: int, tmp_dir: Path) -> None:
    """Remux final_path in place, adding one ID3 chapter per entry in `chapters`
    (list of {"title", "at_ms"}, in order). Each chapter runs from its own start
    to the next chapter's start (last one to total_ms). ffmpeg writes these as
    ID3v2 CHAP/CTOC frames, which podcast apps render as tappable seek points."""
    lines = [";FFMETADATA1"]
    for i, ch in enumerate(chapters):
        start = max(0, ch["at_ms"])
        end = chapters[i + 1]["at_ms"] if i + 1 < len(chapters) else total_ms
        if end <= start:                   # guard against zero/negative spans
            end = start + 1000
        lines += ["[CHAPTER]", "TIMEBASE=1/1000",
                  f"START={start}", f"END={end}",
                  f"title={_ffmeta_escape(ch['title'])}"]
    meta_path = tmp_dir / "chapters.ffmeta"
    meta_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    out_path = tmp_dir / "final-chaptered.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(final_path), "-i", str(meta_path),
         "-map_metadata", "0", "-map_chapters", "1",
         "-codec", "copy", "-loglevel", "error", str(out_path)],
        check=True,
    )
    shutil.move(str(out_path), str(final_path))


_ASSET_MEAN_CACHE = {}


def _asset_mean_dbfs(path: Path) -> float:
    """Measure an asset's mean volume (dBFS) via ffmpeg volumedetect, memoized
    per path. Bed assets vary wildly in inherent loudness (Fireplace ~-42 dBFS,
    Rain ~-20), so we normalize each to an absolute target rather than applying a
    fixed relative attenuation that lands them at unpredictable levels."""
    key = str(path)
    if key not in _ASSET_MEAN_CACHE:
        proc = subprocess.run(
            ["ffmpeg", "-t", "30", "-i", str(path),
             "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True,
        )
        m = re.search(r"mean_volume:\s*(-?[0-9.]+) dB", proc.stderr)
        # Fall back to a neutral guess if volumedetect is silent (never observed).
        _ASSET_MEAN_CACHE[key] = float(m.group(1)) if m else -23.0
    return _ASSET_MEAN_CACHE[key]


def render_bed(hearth_path: Path, overlay_path, duration_sec: float,
                out_path: Path, hearth_db: float = HEARTH_BED_DB,
                overlay_db: float = COLD_OPEN_OVERLAY_DB) -> Path:
    """Build a bed of the given duration by looping the hearth asset (and,
    if provided, an overlay), normalizing each track to its ABSOLUTE target
    level (hearth_db / overlay_db are dBFS targets, not attenuations), applying
    fade in and fade out. Written to out_path; returns out_path."""
    fade_in = 1.0
    fade_out = 1.5
    fade_out_start = max(0.0, duration_sec - fade_out)
    # Gain to move each asset from its measured mean up/down to the target level.
    hearth_gain = hearth_db - _asset_mean_dbfs(hearth_path)
    if overlay_path is not None:
        overlay_gain = overlay_db - _asset_mean_dbfs(overlay_path)
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(hearth_path),
            "-stream_loop", "-1", "-i", str(overlay_path),
            "-filter_complex",
            f"[0:a]volume={hearth_gain}dB,atrim=0:{duration_sec}[a0];"
            f"[1:a]volume={overlay_gain}dB,atrim=0:{duration_sec}[a1];"
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
            f"volume={hearth_gain}dB,"
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


# Sidechain-ducking parameters. The bed is the compressor's *main* input; the
# speech+stings bus is the *sidechain key*. When Vandal speaks, the bed ducks by
# roughly SIDECHAIN_DUCK_DB; in the silences it rises back to its resting level.
# threshold/ratio are tuned for a *light* ~2 dB duck (the bed already sits ~22 dB
# under speech, so this is a gentle secondary breath, not aggressive pumping).
SIDECHAIN_THRESHOLD = 0.03   # speech level (linear) above which ducking engages


SIDECHAIN_RATIO = 2.0        # gentle


SIDECHAIN_ATTACK_MS = 15.0   # duck quickly when speech starts


SIDECHAIN_RELEASE_MS = 400.0 # rise back smoothly in the gaps between phrases


SIDECHAIN_KEY_GAIN = 4.0     # boost the key so quiet narration still triggers it


def mix_top_with_beds(top_path: Path, bed_specs, out_path: Path) -> None:
    """bed_specs: list of (bed_path, delay_ms). Mixes top_path (the speech +
    inline-music bus) with each bed at its start offset.

    Each bed is run through `sidechaincompress` keyed off a copy of the
    speech+stings bus, so the bed ducks ~2 dB whenever Vandal is speaking and
    rises back up in the silences. The un-ducked speech bus is then mixed on top
    with amix normalize=0 so its own level is never attenuated by the mix."""
    if not bed_specs:
        shutil.copy2(top_path, out_path)
        return
    n = len(bed_specs)
    inputs = ["-i", str(top_path)]
    for bed_path, _ in bed_specs:
        inputs.extend(["-i", str(bed_path)])

    filters = []
    # Split the speech bus into 1 (final mix) + n (one sidechain key per bed).
    split_outs = "[spmix]" + "".join(f"[key{i}]" for i in range(1, n + 1))
    filters.append(f"[0:a]asplit={n + 1}{split_outs}")

    mix_labels = ["[spmix]"]
    for i, (_, delay_ms) in enumerate(bed_specs, start=1):
        # Position the bed at its start offset, then duck it against the speech.
        filters.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[bd{i}]")
        filters.append(
            f"[key{i}]volume={SIDECHAIN_KEY_GAIN}[k{i}]"
        )
        filters.append(
            f"[bd{i}][k{i}]sidechaincompress="
            f"threshold={SIDECHAIN_THRESHOLD}:ratio={SIDECHAIN_RATIO}:"
            f"attack={SIDECHAIN_ATTACK_MS}:release={SIDECHAIN_RELEASE_MS}:"
            f"makeup=1:level_sc=1[ducked{i}]"
        )
        mix_labels.append(f"[ducked{i}]")

    filters.append(
        f"{''.join(mix_labels)}amix=inputs={n + 1}:duration=first:"
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


def render_segment(source: Path, out_path: Path, *, start_offset: float,
                   segment: float, afilters: tuple[str, ...]) -> Path:
    """Cut `segment` seconds from `source` at `start_offset` through `afilters`."""
    subprocess.run([
        "ffmpeg", "-y",
        "-ss", str(start_offset),
        "-t", str(segment),
        "-i", str(source),
        "-af", ",".join(afilters),
        "-ac", "1", "-ar", "44100",
        "-c:a", "libmp3lame", "-b:a", "128k",
        "-loglevel", "error",
        str(out_path),
    ], check=True)
    return out_path
