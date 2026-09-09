"""The "Tales of the True Hand" audio recap pipeline.

Was scripts/generate-session-audio.py. Parses sessions/<date>/audio/script.md
into an event stream (speech lines, stings, music cues, bed spans, chapter
marks), renders each speech line through a TTSBackend, layers the music library
underneath, stitches with ffmpeg and writes final.mp3 + manifest.json.

The manifest is a TTS cache keyed by sha256(voice, model, delivery preset,
text): re-running after a music-only change costs zero ElevenLabs credits.
That hash is load-bearing — perturbing it silently invalidates every cached
chunk in every session and re-bills a paid voice. See tests/test_chunk_hash.py.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import warnings
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .. import data as _data
from ..adapters.ffmpeg import (
    concat_mp3s,
    embed_chapters,
    mix_top_with_beds,
    probe_duration_ms,
    render_asset,
    render_bed,
    render_segment,
    synth_silence,
)
from ..adapters.tts import (
    DEFAULT_MODEL_ID,
    DEFAULT_VOICE_ID,
    TTSBackend,
)
from ..core.episode_script import (
    ChapterMark,
    EpisodeScript,
    MusicCue,
    Silence,
    Speak,
    StingCue,
)
from ..errors import OperationFailed, UserError

#: Show direction — levels, cue-to-asset maps and delivery presets. Edited in
#: truehand/data/audio_direction.toml, not here. The delivery table is inside
#: the TTS cache key (see chunk_hash), so tweaking it costs real credits.
_DIRECTION = _data.load("audio_direction")
_LEVELS = _DIRECTION["levels"]
_SIGNATURE = _DIRECTION["signature"]

MUSIC_MID_DB = _LEVELS["music_mid"]
MUSIC_OUTRO_DB = _LEVELS["music_outro"]
STING_CHIME_DB = _LEVELS["sting_chime"]
STING_BRIDGE_DB = _LEVELS["sting_bridge"]
STING_LOW_CHORD_DB = _LEVELS["sting_low_chord"]

#: Absolute dBFS targets for the sustained beds, not attenuations.
HEARTH_BED_DB = _LEVELS["hearth_bed"]
COLD_OPEN_HEARTH_DB = _LEVELS["cold_open_hearth"]
COLD_OPEN_OVERLAY_DB = _LEVELS["cold_open_overlay"]

DELIVERY_PRESETS = _DIRECTION["delivery"]


def resolve_delivery(cue: str):
    """Return (delivery_key, voice_settings). Falls to 'default'."""
    if not cue:
        return "default", DELIVERY_PRESETS["default"]
    for word in re.findall(r"[a-zA-Z']+", cue.lower()):
        if word in DELIVERY_PRESETS:
            return word, DELIVERY_PRESETS[word]
    return "default", DELIVERY_PRESETS["default"]


def _cue_asset(entry, default_db=None):
    """One cue's TOML entry as the (filename, volume_db, segment_or_None)
    triple the resolvers hand back. `db_offset` is relative to default_db, so
    retuning one level moves a whole family of cues with it."""
    db = entry["db"] if "db" in entry else default_db + entry.get("db_offset", 0.0)
    segment = (entry["start_sec"], entry["duration_sec"]) if "start_sec" in entry else None
    return entry["asset"], db, segment


#: Cue keyword -> (asset filename, mix volume in dB, full clip or (start, dur)).
STING_ASSETS = {k: _cue_asset(v) for k, v in _DIRECTION["stings"].items()}

#: Discrete music cues played inline. The signature theme is NOT here: it is
#: rendered as a bed span so it fades under the title line instead of cutting
#: off. The outro plays after all narration; the minor swell before the closing.
MUSIC_ASSETS = {k: _cue_asset(v) for k, v in _DIRECTION["music"].items()}

SIGNATURE_ASSET = _SIGNATURE["asset"]
SIGNATURE_SEGMENT = (_SIGNATURE["start_sec"], _SIGNATURE["duration_sec"])
SIGNATURE_DB = _SIGNATURE["db"]
SIGNATURE_FADE_OUT = _SIGNATURE["fade_out_sec"]
SIGNATURE_HEADROOM_MS = _SIGNATURE["headroom_ms"]


def resolve_sting_cue(library: Path, label: str):
    """Return (asset_path, volume_db, segment_or_None) or None if no match."""
    lo = label.lower()
    # Order matters: longer/more specific keys first.
    for key in sorted(STING_ASSETS.keys(), key=lambda k: -len(k)):
        if key in lo:
            filename, db, segment = STING_ASSETS[key]
            return (library / filename, db, segment)
    return None


def resolve_music_cue(library: Path, label: str):
    """Return (asset_path, volume_db, segment_or_None) or None if no match /
    if this cue is a sustained bed we handle separately (see resolve_bed_start)."""
    lo = label.lower()
    for key in sorted(MUSIC_ASSETS.keys(), key=lambda k: -len(k)):
        if key in lo:
            filename, db, segment = MUSIC_ASSETS[key]
            return (library / filename, db, segment)
    return None


HEARTH_ASSET = _SIGNATURE["hearth_asset"]

#: Cold-open ambience overlays. A `[MUSIC: low ember bed; <flavor>]` cue starts
#: a hearth bed AND layers one of these per the flavor keyword; an unmatched
#: flavor falls back to hearth-only.
BED_OVERLAY_ASSETS = {
    k: _cue_asset(v, COLD_OPEN_OVERLAY_DB)[:2] for k, v in _DIRECTION["bed_overlays"].items()
}


def resolve_bed_overlay(library: Path, label: str):
    """Given a `[MUSIC: low ember bed; <flavor>]` label, return
    (overlay_path, volume_db) for the matching overlay, or None if no
    overlay is available. Hearth is always added by the caller."""
    lo = label.lower()
    for key in sorted(BED_OVERLAY_ASSETS.keys(), key=lambda k: -len(k)):
        if key in lo:
            filename, db = BED_OVERLAY_ASSETS[key]
            return (library / filename, db)
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
            warnings.warn(f"{path} unreadable, treating as empty", stacklevel=2)
    return {}


def save_manifest(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@contextmanager
def _keep_paid_chunks(manifest_path: Path, manifest_out: dict, existing: dict):
    """Persist the TTS cache even when a run dies partway through.

    Chunks are written to disk and recorded in `manifest_out` as they are
    synthesized, but the manifest is only saved once the whole pass completes.
    A quota error or a dropped connection on chunk 40 of 60 propagated straight
    out, leaving 39 freshly-billed mp3s on disk that no manifest mentioned — so
    the next run missed the cache on every one of them and paid again.

    On the way out of a failure, write the union of what the previous run knew
    and what this one recorded. The union is the point: `manifest_out` starts
    empty and fills in script order, so saving it alone would *drop* the
    entries for chunks this run had not reached yet and re-bill those too.

    Catches BaseException deliberately — Ctrl-C partway through a long episode
    is exactly the case worth protecting.
    """
    try:
        yield
    except BaseException:
        save_manifest(
            manifest_path, {**manifest_out, "chunks": {**existing, **manifest_out["chunks"]}}
        )
        raise


@dataclass(frozen=True)
class EpisodeResult:
    """What a build did. The CLI decides how to say it — every other pipeline
    in the package already returns its outcome instead of printing it."""

    status: str  # "written" | "skipped" | "dry-run"
    path: Path
    detail: str = ""
    size_kb: float = 0.0
    chunks: int = 0
    chunks_dir: Path | None = None
    events: int = 0
    spoken_lines: int = 0
    characters: int = 0

    @property
    def estimated_minutes(self) -> float:
        """Calibration across every episode to date is ~888 characters per
        finished minute, music and stings included."""
        return self.characters / 888.0


@dataclass(frozen=True)
class BedSpan:
    """A sustained under-bed running beneath a stretch of narration."""

    kind: str  # "cold_open" | "hearth" | "signature"
    label: str
    start_ms: int
    end_ms: int

    @property
    def duration_sec(self) -> float:
        return (self.end_ms - self.start_ms) / 1000.0


#: Marker kind -> the bed it opens. Anything else closes whatever is open.
_BED_OPENERS = {
    "start_cold_open": "cold_open",
    "start_hearth": "hearth",
    "start_signature": "signature",
}


def resolve_bed_spans(markers, total_ms: int) -> list[BedSpan]:
    """Turn the ordered bed markers into concrete spans.

    An opener closes whatever was playing and starts its own; an end marker
    just closes. A span still open when the show runs out is closed at the end
    (well-formed scripts do not do this). Zero-length spans are dropped.

    Pure, so it can be tested without ElevenLabs or ffmpeg — it used to sit at
    the bottom of build_episode and could only run after money had been spent.
    """
    spans, open_at, kind, label = [], None, None, None

    def close(at_ms):
        if open_at is not None and at_ms > open_at:
            spans.append(BedSpan(kind, label, open_at, at_ms))

    for marker in markers:
        close(marker["at_ms"])
        if marker["kind"] in _BED_OPENERS:
            open_at, kind, label = (marker["at_ms"], _BED_OPENERS[marker["kind"]], marker["label"])
        else:
            open_at = None
    close(total_ms)
    return spans


def _render_bed_span(library: Path, span: BedSpan, asset_cache: Path):
    """Render a single bed span (dict with start_ms, end_ms, type, label)
    into an MP3 in asset_cache. Returns (bed_path, delay_ms) for the mix."""
    duration_sec = span.duration_sec
    slug = span.kind
    out_path = asset_cache / f"bed-{slug}-{int(duration_sec)}s.mp3"

    if span.kind == "signature":
        # Signature theme intro: play from the start of Britons, extend across
        # the title line, and fade out over the tail so it recedes gradually
        # under narration instead of ending abruptly.
        _render_signature_bed(library, duration_sec, out_path)
    else:
        hearth_path = library / HEARTH_ASSET
        overlay_path = None
        overlay_db = COLD_OPEN_OVERLAY_DB
        hearth_db = HEARTH_BED_DB
        if span.kind == "cold_open":
            hearth_db = COLD_OPEN_HEARTH_DB
            overlay = resolve_bed_overlay(library, span.label)
            if overlay is not None:
                overlay_path, overlay_db = overlay
        render_bed(
            hearth_path,
            overlay_path,
            duration_sec,
            out_path,
            hearth_db=hearth_db,
            overlay_db=overlay_db,
        )
    return (out_path, span.start_ms)


def _render_signature_bed(library: Path, duration_sec: float, out_path: Path) -> Path:
    """Render the signature-theme bed (Britons intro). Plays louder at the
    top so it punches, then fades gradually under the title line."""
    source = library / SIGNATURE_ASSET
    start_offset, max_segment = SIGNATURE_SEGMENT
    segment = min(duration_sec, max_segment)
    fade_in = 0.4
    fade_out = min(SIGNATURE_FADE_OUT, max(1.5, segment * 0.6))
    fade_out_start = max(0.0, segment - fade_out)
    render_segment(
        source,
        out_path,
        start_offset=start_offset,
        segment=segment,
        afilters=(
            f"volume={SIGNATURE_DB}dB",
            f"afade=t=in:st=0:d={fade_in}",
            f"afade=t=out:st={fade_out_start}:d={fade_out}",
        ),
    )
    return out_path


def build_episode(
    paths,
    backend: TTSBackend,
    date: str,
    *,
    voice_id: str = DEFAULT_VOICE_ID,
    model_id: str = DEFAULT_MODEL_ID,
    force: bool = False,
    force_tts: bool = False,
    no_music: bool = False,
    no_beds: bool = False,
    dry_run: bool = False,
    on_progress=None,
) -> EpisodeResult:
    """Render sessions/<date>/audio/final.mp3 from its script.md.

    Progress goes to *on_progress* rather than stdout, so a caller can stay
    quiet, capture it, or render it however it likes.
    """
    report = on_progress or (lambda _msg: None)
    library = paths.audio_library
    session_dir = paths.session_audio(date)
    script_path = session_dir / "script.md"
    if not script_path.exists():
        raise UserError(f"script not found: {script_path}")

    chunks_dir = session_dir / "chunks"
    manifest_path = session_dir / "manifest.json"
    final_path = session_dir / "final.mp3"

    if final_path.exists() and not force and not force_tts and not dry_run:
        return EpisodeResult(
            "skipped", final_path, detail="already exists — use --force to rebuild"
        )

    session_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    script = EpisodeScript.parse(script_path.read_text(encoding="utf-8"))
    events = script.events
    spoken = script.spoken_lines
    total_chars = script.character_count
    report(
        f"[{date}] parsed {len(spoken)} speech chunks "
        f"({total_chars} chars), "
        f"{script.count(StingCue)} stings, "
        f"{script.count(MusicCue)} music cues"
    )

    if dry_run:
        for e in events[:30]:
            report(f"  {e}")
        return EpisodeResult(
            "dry-run",
            final_path,
            events=len(events),
            spoken_lines=len(spoken),
            characters=total_chars,
        )

    manifest = load_manifest(manifest_path)
    if force_tts:
        manifest = {}
    existing_chunks = manifest.get("chunks", {})  # hash -> chunk_id
    manifest_out = {"date": date, "voice_id": voice_id, "model_id": model_id, "chunks": {}}

    with (
        tempfile.TemporaryDirectory(prefix="tales-") as tmp,
        _keep_paid_chunks(manifest_path, manifest_out, existing_chunks),
    ):
        tmp_dir = Path(tmp)
        silence_cache = tmp_dir / "silences"
        silence_cache.mkdir()
        asset_cache = tmp_dir / "assets"
        asset_cache.mkdir()

        speech_texts = [line.text for line in spoken]

        # --- Pass 1: resolve every event to a concrete audio element on
        # disk (speech chunk from cache or new TTS, silence, sting, inline
        # music) and capture its duration in ms. Bed cues are left as
        # markers with no audio element attached — they're consumed in
        # pass 2 to find the sustained under-bed spans.
        top_layer = []  # list of dicts: {"path": Path, "dur_ms": int, "kind": str, "label": str}
        # dicts: {"at_ms": int, "label": str,
        #         "kind": "start_hearth" | "start_cold_open" | "end"}
        bed_markers = []
        chapters = []  # list of dicts: {"title": str, "at_ms": int} — ID3 chapter marks
        cursor_ms = 0
        speech_idx = 0

        for ev in events:
            if isinstance(ev, Speak):
                txt = ev.text
                delivery_key, voice_settings = resolve_delivery(ev.delivery)
                h = chunk_hash(txt, voice_id, model_id, delivery_key)
                chunk_id = f"{speech_idx + 1:04d}"
                chunk_path = chunks_dir / f"{chunk_id}.mp3"

                if h in existing_chunks and (chunks_dir / f"{existing_chunks[h]}.mp3").exists():
                    cached_id = existing_chunks[h]
                    cached_path = chunks_dir / f"{cached_id}.mp3"
                    if cached_id != chunk_id:
                        shutil.copy2(cached_path, chunk_path)
                    report(
                        f"  [{speech_idx + 1}/{len(speech_texts)}] "
                        f"({delivery_key}) [cache hit] "
                        f"{txt[:50].replace(chr(10), ' ')}..."
                    )
                else:
                    prev_txt = speech_texts[speech_idx - 1] if speech_idx > 0 else ""
                    next_txt = (
                        speech_texts[speech_idx + 1] if speech_idx + 1 < len(speech_texts) else ""
                    )
                    report(
                        f"  [{speech_idx + 1}/{len(speech_texts)}] "
                        f"({delivery_key}) [TTS] "
                        f"{txt[:50].replace(chr(10), ' ')}..."
                    )
                    try:
                        chunk_path.write_bytes(
                            backend.synthesize(
                                txt,
                                voice_id=voice_id,
                                model_id=model_id,
                                settings=voice_settings,
                                previous_text=prev_txt,
                                next_text=next_txt,
                            )
                        )
                    except Exception as exc:
                        raise OperationFailed(f"TTS failed on chunk {chunk_id}: {exc}") from exc

                manifest_out["chunks"][h] = chunk_id
                dur_ms = probe_duration_ms(chunk_path)
                top_layer.append({"path": chunk_path, "dur_ms": dur_ms, "kind": "speak"})
                cursor_ms += dur_ms
                speech_idx += 1

            elif isinstance(ev, ChapterMark):
                # Zero-duration marker: record the current timeline position;
                # embedded as an ID3 chapter after the final mix.
                chapters.append({"title": ev.title, "at_ms": cursor_ms})

            elif isinstance(ev, Silence):
                dur = ev.duration_ms
                sil_path = silence_cache / f"silence-{dur}.mp3"
                if not sil_path.exists():
                    synth_silence(dur, sil_path)
                top_layer.append({"path": sil_path, "dur_ms": dur, "kind": "silence"})
                cursor_ms += dur

            elif isinstance(ev, StingCue):
                label = ev.label
                if no_music:
                    fb = silence_cache / "sting-fallback.mp3"
                    if not fb.exists():
                        synth_silence(400, fb)
                    top_layer.append({"path": fb, "dur_ms": 400, "kind": "sting"})
                    cursor_ms += 400
                    continue
                resolved = resolve_sting_cue(library, label)
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

            elif isinstance(ev, MusicCue):
                label = ev.label

                # Register bed markers at THIS cursor position, before
                # advancing for any inline element the cue may also carry.
                if not no_music and not no_beds:
                    if is_cold_open_bed_cue(label):
                        bed_markers.append(
                            {"at_ms": cursor_ms, "kind": "start_cold_open", "label": label}
                        )
                    elif is_hearth_bed_start_cue(label):
                        bed_markers.append(
                            {"at_ms": cursor_ms, "kind": "start_hearth", "label": label}
                        )
                    elif is_signature_bed_cue(label):
                        # Transition: closes the cold-open bed and opens the
                        # signature bed at the same position. Then inject a
                        # short silence into the top layer so the intro theme
                        # plays alone for a beat before the title-line speech
                        # comes in.
                        bed_markers.append(
                            {"at_ms": cursor_ms, "kind": "start_signature", "label": label}
                        )
                        headroom_path = (
                            silence_cache / f"signature-headroom-{SIGNATURE_HEADROOM_MS}.mp3"
                        )
                        if not headroom_path.exists():
                            synth_silence(SIGNATURE_HEADROOM_MS, headroom_path)
                        top_layer.append(
                            {
                                "path": headroom_path,
                                "dur_ms": SIGNATURE_HEADROOM_MS,
                                "kind": "silence",
                            }
                        )
                        cursor_ms += SIGNATURE_HEADROOM_MS
                    elif is_bed_end_cue(label):
                        bed_markers.append({"at_ms": cursor_ms, "kind": "end", "label": label})

                if no_music:
                    continue
                resolved = resolve_music_cue(library, label)
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
        if not no_music and not no_beds:
            for span in resolve_bed_spans(bed_markers, cursor_ms):
                report(
                    f"  bed span: {span.kind} — {span.duration_sec:.1f}s "
                    f"@ {span.start_ms / 1000:.1f}s"
                )
                bed_specs.append(_render_bed_span(library, span, asset_cache))

        # --- Pass 3: concat the top layer to top.mp3, then mix in the
        # rendered beds at their offsets.
        top_path = tmp_dir / "top.mp3"
        top_paths = [e["path"] for e in top_layer]
        report(f"Concatenating {len(top_paths)} top-layer elements")
        concat_mp3s(top_paths, top_path)

        if bed_specs:
            report(f"Mixing {len(bed_specs)} under-bed span(s) → {final_path.name}")
            mix_top_with_beds(top_path, bed_specs, final_path)
        else:
            report(f"No under-beds → {final_path.name}")
            shutil.copy2(top_path, final_path)

        if chapters:
            total_ms = probe_duration_ms(final_path)
            embed_chapters(final_path, chapters, total_ms, tmp_dir)
            report(
                f"  Embedded {len(chapters)} chapter marker(s): "
                f"{', '.join(c['title'] for c in chapters)}"
            )

    return EpisodeResult(
        "written",
        final_path,
        size_kb=final_path.stat().st_size / 1024,
        chunks=len(manifest_out["chunks"]),
        chunks_dir=chunks_dir,
        events=len(events),
        spoken_lines=len(spoken),
        characters=total_chars,
    )
