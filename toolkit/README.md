# truehand

The campaign archive's tooling, as one installable CLI.

```bash
python3 -m venv .venv                      # Python 3.11+
.venv/bin/pip install -e './toolkit[all]'
.venv/bin/truehand --help
```

Editable install: edits under `src/truehand/` take effect with no reinstall.

## Commands

```
truehand site build [--out DIR] [--base-url URL]
truehand session image DATE [--hero] [--beats] [--force] [--model M]
                           [--hero-aspect A] [--beat-aspect A] [--refs-only] [--lean]
truehand session audio DATE [--voice V] [--model M] [--force] [--force-tts]
                           [--no-music] [--no-beds] [--dry-run]
truehand session factcheck DATE
truehand refs build  [--only SLUG] [--plate N] [--force] [--model M]
truehand cover build [--force] [--model M]
truehand entities sync [--dry-run]
```

`--root PATH` (or `TRUEHAND_ROOT`) overrides archive discovery, which otherwise
walks up from the working directory looking for `campaign-state.md`, `quests.md`
and `sessions/` together.

## Layout

| Package | Holds |
|---|---|
| `core/` | The archive model: frontmatter, markdown, entities, loaders, graph. Pure, stdlib, no HTML and no network. |
| `content/` | Prompt prose — PC identity anchors and art direction. |
| `adapters/` | Everything external: Gemini, ElevenLabs, ffmpeg, Pillow. |
| `site/` | HTML and RSS rendering. Depends on `core`; never the reverse. |
| `pipelines/` | Orchestration — `core` + `content` + `adapters`, no CLI concerns. |
| `cli/` | Typer only. Parses flags, builds `Paths`, calls a pipeline. |

## Dependencies

Typer is the only hard dependency, so `truehand site build` runs in a venv with
nothing else installed. `google-genai` and `pillow` (`[image]`), and
`elevenlabs` (`[audio]`) are imported lazily; a missing one is reported as an
install hint, not a traceback.

## Tests

```bash
.venv/bin/python -m pytest toolkit/tests -q
.venv/bin/python -m ruff check toolkit/src toolkit/tests
```

Two are load-bearing:

- **`test_golden_site.py`** rebuilds the whole site and asserts it is
  byte-identical to the committed `website/site/`. Because that tree is tracked
  in git, `truehand site build && git diff --exit-code website/site` is the same
  check by hand.
- **`test_chunk_hash.py`** freezes the TTS cache key against a value captured
  from the pre-migration script. Perturbing it invalidates every cached chunk in
  every episode and re-bills a paid ElevenLabs voice.

`test_frontmatter.py` pins the archive's frontmatter dialect, which resembles
YAML but is not — see its `TestThisIsNotYaml`.
