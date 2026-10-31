# Handoff: Safelight

**State:** UI built and awaiting UAT. Answers are simulated; no Jev calls happen yet.

**Next step:** add a real engine in `safelight/engine.py` with the `Engine` signature, using `AsyncTypeSafeClient.system_one`, `IMAGES_ON` and `perf_counter` timing. Set `simulated=False` and pass it to `Safelight(engine=...)`. Run with `uv run --env-file .env safelight`.

**Design constraints:**
- `system_one` answers a batch all at once. So a run has two stages: exposing is the real wait, and developing is a local reveal. Do not fake per-image streaming.
- Report only the engine's measured seconds. The reveal is not part of the time.
- Every Jev run must show its seconds.
- Half-blocks are deliberate: they work everywhere and can animate. Kitty and sixel output is unreliable inside Textual.
- Frames are letterboxed, never cropped, because they are evidence.
- Keep it quiet: images are the only colour, plus one muted tone for wrong answers. Hierarchy comes from space and type.

**Known gaps:**
- There is no plain or JSON output for pipes.
- Rolls assume the balloon question and threshold from `ask_balloons.py`.
- The layout test checks summary pane overlap and spill at seven sizes. It does not check frame content.
