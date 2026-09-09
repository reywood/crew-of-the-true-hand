"""The TTS cache key.

The only test here that protects money. chunk_hash() decides whether a speech
line is reused from sessions/<date>/audio/chunks/ or re-synthesized. Perturb it
and every cached chunk in every episode invalidates at once, re-billing a paid
ElevenLabs voice for ~366 lines.
"""

import json
import shutil

import pytest

from truehand.errors import OperationFailed
from truehand.pipelines.session_audio import (
    DELIVERY_PRESETS,
    chunk_hash,
    parse_script,
    resolve_delivery,
)

VOICE = "tEo3d4j7gzVojBL5Z4Pt"
MODEL = "eleven_multilingual_v2"


def test_frozen_hash_for_a_known_line():
    """Captured from the pre-migration script, so this pins equivalence
    with the code that produced every committed manifest — not merely with
    whatever the current implementation happens to do."""
    assert chunk_hash(
        "Well met, friend. Draw close to the fire.", VOICE, MODEL, "storyteller"
    ) == "88c000309ecec24d4df054b87ecfb8f8c05783f6cf34d84bde398b3c869b82d6"


def test_hash_is_stable_across_calls():
    a = chunk_hash("x", VOICE, MODEL, "storyteller")
    b = chunk_hash("x", VOICE, MODEL, "storyteller")
    assert a == b


@pytest.mark.parametrize("field", ["text", "voice", "model", "delivery"])
def test_every_input_participates(field):
    base = {"text": "x", "voice_id": VOICE, "model_id": MODEL,
            "delivery_key": "storyteller"}
    other = dict(base)
    other[{"text": "text", "voice": "voice_id", "model": "model_id",
           "delivery": "delivery_key"}[field]] = {
        "text": "y", "voice": "OTHERVOICE", "model": "other_model",
        "delivery": "hushed"}[field]
    assert chunk_hash(**base) != chunk_hash(**other)


def test_preset_values_are_baked_in(monkeypatch):
    """Tweaking a preset must invalidate its cached chunks."""
    before = chunk_hash("x", VOICE, MODEL, "storyteller")
    tweaked = dict(DELIVERY_PRESETS)
    tweaked["storyteller"] = dict(tweaked["storyteller"])
    tweaked["storyteller"]["stability"] = 0.999
    monkeypatch.setattr("truehand.pipelines.session_audio.DELIVERY_PRESETS", tweaked)
    assert chunk_hash("x", VOICE, MODEL, "storyteller") != before


def test_every_committed_manifest_still_resolves(paths):
    """The real guarantee: no episode re-bills on its next rebuild."""
    checked = 0
    for manifest_path in sorted(paths.sessions.glob("*/audio/manifest.json")):
        script = manifest_path.parent / "script.md"
        if not script.exists():
            continue
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        live = {
            chunk_hash(text, data["voice_id"], data["model_id"],
                       resolve_delivery(delivery)[0])
            for kind, text, delivery in
            (e for e in parse_script(script.read_text(encoding="utf-8")) if e[0] == "speak")
        }
        orphaned = set(data["chunks"]) - live
        assert not orphaned, (
            f"{manifest_path.parent.parent.name}: {len(orphaned)} cached chunks "
            f"would be re-synthesized"
        )
        checked += 1
    assert checked >= 10, f"only checked {checked} episodes"


# --------------------------------------------------------------------------
# Crash safety: a run that dies partway must not re-bill what it already paid
# for. Chunks are written to disk as they are synthesized, but the manifest —
# the only record of which hash is in which file — used to be saved after the
# whole pass. A failure in between stranded every paid chunk.
# --------------------------------------------------------------------------

SCRIPT = """# Tales of the True Hand — 2099-01-01
## A Test Episode

[COLD OPEN — 25s]

VANDAL: *(storyteller)* Line one.

VANDAL: *(hushed)* Line two.

VANDAL: *(grave)* Line three.

VANDAL: *(warm)* Line four.
"""


class FlakyBackend:
    """Counts synthesize() calls and fails on the nth, like a quota error."""

    def __init__(self, audio, fail_on=None):
        self.audio = audio
        self.calls = []
        self.fail_on = fail_on

    def synthesize(self, text, *, voice_id, model_id, settings,
                   previous_text="", next_text=""):
        self.calls.append(text)
        if self.fail_on is not None and len(self.calls) == self.fail_on:
            raise RuntimeError("quota exceeded")
        return self.audio


@pytest.fixture(scope="module")
def mp3_bytes(tmp_path_factory):
    """A real, decodable mp3 — the stitch shells out to ffmpeg for the runs
    that are meant to succeed, so placeholder bytes will not do."""
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.skip("ffmpeg/ffprobe not installed")
    from truehand.adapters.ffmpeg import synth_silence
    return synth_silence(120, tmp_path_factory.mktemp("tone") / "s.mp3").read_bytes()


@pytest.fixture
def episode(tmp_path):
    """A minimal archive holding one session with a script, aimed at tmp."""
    from truehand.paths import Paths
    for marker in ("campaign-state.md", "quests.md"):
        (tmp_path / marker).write_text("")
    audio = tmp_path / "sessions" / "2099-01-01" / "audio"
    audio.mkdir(parents=True)
    (audio / "script.md").write_text(SCRIPT, encoding="utf-8")
    return Paths.at(tmp_path), audio


def _run(paths, backend, force=False):
    from truehand.pipelines.session_audio import build_episode
    return build_episode(paths, backend, "2099-01-01",
                         voice_id=VOICE, model_id=MODEL,
                         no_music=True, no_beds=True, force=force)


def test_a_crash_records_every_chunk_already_paid_for(episode, mp3_bytes):
    paths, audio = episode
    backend = FlakyBackend(mp3_bytes, fail_on=3)

    with pytest.raises(OperationFailed, match="TTS failed on chunk"):
        _run(paths, backend)

    assert len(backend.calls) == 3, "should have died on the third line"
    manifest = json.loads((audio / "manifest.json").read_text())
    # The two that succeeded are recorded and their files are on disk.
    assert len(manifest["chunks"]) == 2
    for chunk_id in manifest["chunks"].values():
        assert (audio / "chunks" / f"{chunk_id}.mp3").exists()


def test_a_retry_after_a_crash_does_not_re_bill(episode, mp3_bytes):
    """The whole point: the retry pays only for what was never voiced."""
    paths, _audio = episode
    with pytest.raises(OperationFailed):
        _run(paths, FlakyBackend(mp3_bytes, fail_on=3))

    retry = FlakyBackend(mp3_bytes)
    _run(paths, retry)
    assert retry.calls == ["Line three.", "Line four."], \
        "lines one and two were already paid for and must come from the cache"


def test_a_crash_does_not_drop_chunks_the_run_had_not_reached(episode, mp3_bytes):
    """The subtle half. `manifest_out` starts empty and fills in script order,
    so persisting it alone would strand every chunk from a previous run that
    this run died before revisiting — re-billing those too."""
    from truehand.pipelines.session_audio import chunk_hash
    paths, audio = episode

    _run(paths, FlakyBackend(mp3_bytes))          # a complete previous run
    assert len(json.loads((audio / "manifest.json").read_text())["chunks"]) == 4

    # Edit the opening line, so this run must voice it and can die on it
    # before ever reaching the three lines it would have taken from cache.
    (audio / "script.md").write_text(
        SCRIPT.replace("Line one.", "A rewritten line."), encoding="utf-8")
    with pytest.raises(OperationFailed):
        _run(paths, FlakyBackend(mp3_bytes, fail_on=1), force=True)

    chunks = json.loads((audio / "manifest.json").read_text())["chunks"]
    for text, cue in [("Line two.", "hushed"), ("Line three.", "grave"),
                      ("Line four.", "warm")]:
        assert chunk_hash(text, VOICE, MODEL, cue) in chunks, \
            f"{text!r} was paid for by the earlier run and must survive"


def test_a_clean_run_writes_only_the_current_scripts_chunks(episode, mp3_bytes):
    """The guard must not turn the manifest into an append-only pile."""
    paths, audio = episode
    _run(paths, FlakyBackend(mp3_bytes))
    assert len(json.loads((audio / "manifest.json").read_text())["chunks"]) == 4
