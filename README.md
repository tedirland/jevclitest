# Safelight

Safelight is a terminal app for testing what Jev can see in images.

[Jev](https://docs.typesafe.ai) is a TypeSafe model that answers typed questions with calibrated probabilities. This project asks it yes or no questions about images, compares the answers with known truth, and shows how it did.

> **Status:** Safelight's interface is finished, but its answers are simulated and it does not call Jev yet. The app labels every result as `simulated`. The `ask_image.py` and `ask_balloons.py` scripts do call the real model.

## Quick start

Install [uv](https://docs.astral.sh/uv/), then run:

```bash
uv sync
uv run safelight balloons
```

| Command | What it does |
| --- | --- |
| `uv run safelight` | Browse the experiments and images in this folder |
| `uv run safelight balloons` | Run an experiment |
| `uv run safelight sample.png` | Type a question about one image |
| ``uv run safelight sample.png 'Is there a house in `photo`?'`` | Ask about one image straight away |

Use single quotes around questions, because the shell treats backticks in double quotes as commands.

| Key | Action |
| --- | --- |
| Arrows or click | Choose a frame |
| `r` | Run again |
| `space` | Skip the reveal |
| `esc` | Go back |
| `q` | Quit and print a one-line summary of the run |

## How a run works

1. **Ask.** All the questions go to Jev in one request, because it answers a batch all at once. The timer shows this wait.
2. **Reveal.** Each image fades from grey into colour as its answer appears, and the score updates. This stage is local, so it is not part of the reported time.
3. **Review.** Select any frame to compare its reading, its true count and an enlarged copy of the image.

Jev returns a probability called a Noul, from 0 to 1, which Safelight reads like this:

| Noul | Answer |
| --- | --- |
| Above 0.7 | yes |
| Below 0.3 | no |
| 0.3 to 0.7 | unclear |

An answer counts as right only when it matches the truth, so `unclear` never scores.

## Add an experiment

An experiment, called a roll in the code, is a folder of `.png` images with an `expected.json` file giving the balloon count for each image:

```json
{
  "image_1": 6,
  "image_2": 3
}
```

Safelight finds these folders automatically. Each image is asked whether it has more than 3 balloons, as that question and threshold are currently fixed in `ask_balloons.py`.

To regenerate the sample images, run `uv run make_balloons.py`.

## Call the real model

The standalone scripts need a TypeSafe API key. Create a `.env` file containing:

```
TYPESAFE_API_KEY=your-key-here
```

Then run:

```bash
uv run --env-file .env ask_image.py sample.png 'Is there a house in `photo`?'
uv run --env-file .env ask_balloons.py
```

## Project layout

| Path | Purpose |
| --- | --- |
| `safelight/cli.py` | Command line entry point |
| `safelight/app.py` | The Textual application |
| `safelight/engine.py` | Sends a run to Jev; simulated for now |
| `safelight/rolls.py` | Loads experiments and scores answers |
| `safelight/photo.py` | Draws images in the terminal |
| `safelight/screens/` | The home and results screens |
| `safelight/widgets/` | Interface pieces such as the summary pane |
| `ask_image.py`, `ask_balloons.py` | Standalone scripts that call Jev |
| `make_balloons.py`, `balloons/` | Sample image generator and its output |

To connect the real model, see [HANDOFF.md](HANDOFF.md).

## Tests

```bash
uv run pytest
```

The tests make no network calls. See [tests/README.md](tests/README.md) for what they cover.
