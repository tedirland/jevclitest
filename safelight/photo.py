"""Turn image files into terminal pixels that fade from grey into colour."""
import random

from PIL import Image, ImageOps
from rich.color import Color
from rich.segment import Segment
from rich.style import Style
from textual.strip import Strip

FILM = (18, 17, 16)
GHOST_LIGHT = (72, 69, 65)
GHOST_DARK = (24, 23, 22)
SPREAD = 0.25


def fit(image: Image.Image, cols: int, rows: int) -> Image.Image:
    """Letterbox an image into `cols` by `rows` cells, two pixels to a cell.

    Never crops: a frame is evidence, so all of it stays visible.
    """
    return ImageOps.pad(image.convert("RGB"), (cols, rows * 2), Image.Resampling.LANCZOS, FILM)


def ghost(image: Image.Image) -> Image.Image:
    """Render the waiting print: its tones in soft, dim grey."""
    return ImageOps.colorize(ImageOps.grayscale(image), GHOST_DARK, GHOST_LIGHT)


def tray_marks(size: tuple[int, int], seed: int) -> Image.Image:
    """Make the soft blotches that decide where developer takes first."""
    rng = random.Random(seed)
    coarse = Image.new("L", (5, 4))
    coarse.putdata([rng.randrange(256) for _ in range(5 * 4)])
    return coarse.resize(size, Image.Resampling.BICUBIC)


def _lut(progress: float) -> list[int]:
    """Map tray marks to mask strength at this moment of developing."""
    reach = progress * (1 + SPREAD)
    return [max(0, min(255, round(255 * (reach - SPREAD * mark / 255)))) for mark in range(256)]


def develop(full: Image.Image, undeveloped: Image.Image, marks: Image.Image, progress: float) -> Image.Image:
    """Blend a print between its ghost (0.0) and full colour (1.0)."""
    return Image.composite(full, undeveloped, marks.point(_lut(progress)))


def strips(image: Image.Image) -> list[Strip]:
    """Convert an image to half-block rows, one Strip per two pixel rows."""
    width, height = image.size
    data = image.tobytes()

    def colour(x: int, y: int) -> Color:
        start = (y * width + x) * 3
        return Color.from_rgb(data[start], data[start + 1], data[start + 2])

    return [
        Strip(
            [
                Segment("▀", Style.from_color(colour(x, y), colour(x, y + 1)))
                for x in range(width)
            ],
            width,
        )
        for y in range(0, height - 1, 2)
    ]
