"""Draw the balloon test images and record how many balloons each one has.

Run with: uv run make_balloons.py
"""
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path("balloons")
BALLOON_COUNTS = [6, 3, 3, 5, 6, 5]
SIZE = (800, 600)
COLUMNS, ROWS = 4, 3
SKIES = [(205, 232, 245), (250, 236, 214), (226, 240, 222), (232, 226, 244)]
COLOURS = [(214, 48, 49), (9, 132, 227), (0, 148, 110), (253, 170, 40), (155, 89, 182), (232, 67, 147)]


def draw_balloon(draw: ImageDraw.ImageDraw, x: int, y: int, colour: tuple[int, int, int]) -> None:
    """Draw one balloon whose top-left corner is at (x, y)."""
    width, height = 90, 112
    centre = x + width // 2
    bottom = y + height
    draw.ellipse([x, y, x + width, bottom], fill=colour)
    draw.polygon([(centre, bottom - 3), (centre - 8, bottom + 10), (centre + 8, bottom + 10)], fill=colour)
    draw.line([(centre, bottom + 10), (centre + 10, bottom + 30), (centre - 6, bottom + 52)], fill=(90, 90, 90), width=2)


def make_image(count: int, seed: int) -> Image.Image:
    """Draw `count` balloons, each in its own grid cell so none overlap."""
    rng = random.Random(seed)
    img = Image.new("RGB", SIZE, rng.choice(SKIES))
    draw = ImageDraw.Draw(img)
    cell_w, cell_h = SIZE[0] // COLUMNS, SIZE[1] // ROWS
    cells = [(col, row) for col in range(COLUMNS) for row in range(ROWS)]
    for col, row in rng.sample(cells, count):
        x = col * cell_w + rng.randint(5, cell_w - 95)
        y = row * cell_h + rng.randint(4, 10)
        draw_balloon(draw, x, y, rng.choice(COLOURS))
    return img


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    expected = {}
    for number, count in enumerate(BALLOON_COUNTS, start=1):
        name = f"image_{number}"
        make_image(count, seed=number).save(OUT_DIR / f"{name}.png")
        expected[name] = count
    (OUT_DIR / "expected.json").write_text(json.dumps(expected, indent=2) + "\n")


if __name__ == "__main__":
    main()
