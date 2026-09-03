# scripts/ — moved

These generators are now subcommands of the `truehand` CLI, which lives in
[`toolkit/`](../toolkit/). One package, one shared core, no copy-pasted helpers.

| Was | Now |
|---|---|
| `scripts/generate-session-image.py DATE` | `truehand session image DATE` |
| `scripts/generate-session-audio.py DATE` | `truehand session audio DATE` |
| `scripts/generate-factcheck-review.py DATE` | `truehand session factcheck DATE` |
| `scripts/generate-character-references.py` | `truehand refs build` |
| `scripts/generate-podcast-cover.py` | `truehand cover build` |
| `scripts/update-entity-sessions.py` | `truehand entities sync` |
| `python3 website/generate.py` | `truehand site build` |

Every flag was carried over unchanged. Setup and the full workflow are in
[`CLAUDE.md`](../CLAUDE.md); `requirements.txt` was replaced by
`toolkit/pyproject.toml`.
