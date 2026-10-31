# Tests

Run with `uv run pytest`.

| File | Covers |
| --- | --- |
| `test_photo.py` | Letterboxing, grey waiting print, fade stages, half-block rows |
| `test_rolls.py` | Roll loading, scoring, discovery, simulated engine |
| `test_cli.py` | Argument handling and usage errors |
| `test_app.py` | Interface flows through Textual's Pilot, including keys, requests in flight, the live summary pane and layout at several sizes |
| `../test_ask_balloons.py` | The original script logic |

`test_app.py` sets `animation_level = "none"` and swaps in a fake engine, so these tests make no network calls. The exception is `test_space_skips_the_reveal`, which keeps animations on.

Not covered automatically: how it looks. Check visuals in a real terminal.
