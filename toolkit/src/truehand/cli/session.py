"""``truehand session`` — per-session artifacts: images, audio, fact-check."""

from __future__ import annotations

from typing import Annotated

import typer

from ..adapters.images import DEFAULT_IMAGE_MODEL, GeminiImageBackend
from ..adapters.tts import DEFAULT_MODEL_ID, DEFAULT_VOICE_ID, ElevenLabsBackend
from ..core.env import load_dotenv
from ..errors import UserError
from ..pipelines import session_audio, session_image
from .app import resolve_paths

session_app = typer.Typer(help="Per-session artifacts.", no_args_is_help=True)

DATE_ARG = typer.Argument(..., metavar="DATE", help="Session date, YYYY-MM-DD.")


@session_app.command("image")
def image(
    ctx: typer.Context,
    date: Annotated[str, DATE_ARG],
    force: Annotated[bool, typer.Option("--force", help="Regenerate even if the file exists.")] = False,
    model: Annotated[str, typer.Option("--model", help="Gemini image model.")] = DEFAULT_IMAGE_MODEL,
    hero: Annotated[bool, typer.Option("--hero", help="Hero banner only.")] = False,
    beats: Annotated[bool, typer.Option("--beats", help="Beat illustrations only.")] = False,
    hero_aspect: Annotated[str, typer.Option("--hero-aspect", help="Hero aspect ratio.")] = "16:9",
    beat_aspect: Annotated[str, typer.Option("--beat-aspect", help="Beat aspect ratio.")] = "3:2",
    refs_only: Annotated[bool, typer.Option("--refs-only", help="Reference plates only, no cast prose.")] = False,
    lean: Annotated[bool, typer.Option("--lean", help="Lean cast lines instead of full identity anchors.")] = False,
) -> None:
    """Generate the hero banner and beat illustrations for a session."""
    if refs_only and lean:
        raise UserError("--refs-only and --lean are mutually exclusive")
    paths = resolve_paths(ctx)
    load_dotenv(paths.env_file)
    # Neither flag given means both, matching the original script.
    want_hero, want_beats = (hero, beats) if (hero or beats) else (True, True)
    backend = GeminiImageBackend()
    results, warnings = session_image.generate(
        paths, backend, date, hero=want_hero, beats=want_beats, force=force,
        model=model, hero_aspect=hero_aspect, beat_aspect=beat_aspect,
        refs_only=refs_only, lean=lean,
    )
    for w in warnings:
        typer.secho(f"  WARN: {w}", fg="yellow", err=True)
    for r in results:
        typer.echo(f"  {r.status:8s} {r.label}: {r.path.name} {r.detail}")
    typer.echo("Next: truehand site build")


@session_app.command("audio")
def audio(
    ctx: typer.Context,
    date: Annotated[str, DATE_ARG],
    voice: Annotated[str, typer.Option("--voice", help="ElevenLabs voice_id (default: Cormac).")] = DEFAULT_VOICE_ID,
    model: Annotated[str, typer.Option("--model", help="ElevenLabs model_id.")] = DEFAULT_MODEL_ID,
    force: Annotated[bool, typer.Option("--force", help="Rebuild final.mp3 even if it exists. Chunks stay cached.")] = False,
    force_tts: Annotated[bool, typer.Option("--force-tts", help="Invalidate the TTS cache and re-call for every chunk.")] = False,
    no_music: Annotated[bool, typer.Option("--no-music", help="Voice only — skip all layering. Implies --no-beds.")] = False,
    no_beds: Annotated[bool, typer.Option("--no-beds", help="Skip sustained under-beds; inline cues still play.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Parse the script without calling TTS or stitching.")] = False,
) -> None:
    """Render the Tales of the True Hand episode for a session."""
    paths = resolve_paths(ctx)
    load_dotenv(paths.env_file)
    result = session_audio.build_episode(
        paths, ElevenLabsBackend(), date, voice_id=voice, model_id=model,
        force=force, force_tts=force_tts, no_music=no_music,
        no_beds=no_beds, dry_run=dry_run,
    )
    if result["status"] == "skipped":
        typer.echo(f"{result['path']} {result['detail']}")
    elif result["status"] == "written":
        typer.echo(f"Wrote {result['path']} ({result['size_kb']:.0f} KB)")
        typer.echo(f"  Cached {result['chunks']} speech chunks under {result['chunks_dir']}")


@session_app.command("factcheck")
def factcheck(
    ctx: typer.Context,
    date: Annotated[str, DATE_ARG],
) -> None:
    """Render the fact-check worksheet as a reviewable HTML page."""
    from ..pipelines import factcheck as pipeline
    paths = resolve_paths(ctx)
    dest = pipeline.render_review(paths, date)
    note = "" if pipeline.recording_present(paths, date) else \
        "  (warning: recording.m4a not found beside it)"
    typer.echo(f"wrote {dest.relative_to(paths.root)}{note}")
