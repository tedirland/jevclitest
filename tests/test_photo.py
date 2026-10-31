"""Tests for the print pipeline."""
from PIL import Image

from safelight.photo import develop, fit, ghost, strips, tray_marks

BLUE = (10, 80, 240)


def blue_print():
    full = fit(Image.new("RGB", (800, 600), BLUE), 8, 3)
    return full, ghost(full), tray_marks(full.size, seed=1)


def test_fit_makes_two_pixels_per_cell():
    assert fit(Image.new("RGB", (800, 600)), 30, 10).size == (30, 20)


def test_waiting_print_has_almost_no_colour():
    _, undeveloped, _ = blue_print()
    assert max(undeveloped.getpixel((0, 0))) - min(undeveloped.getpixel((0, 0))) < 12


def test_develop_starts_as_ghost_and_ends_in_colour():
    full, undeveloped, marks = blue_print()
    assert develop(full, undeveloped, marks, 0.0).tobytes() == undeveloped.tobytes()
    assert develop(full, undeveloped, marks, 1.0).tobytes() == full.tobytes()


def test_develop_midway_is_partly_developed():
    full, undeveloped, marks = blue_print()
    middle = develop(full, undeveloped, marks, 0.5).tobytes()
    assert middle != undeveloped.tobytes()
    assert middle != full.tobytes()


def test_strips_use_one_row_per_two_pixels():
    full, _, _ = blue_print()
    rows = strips(full)
    assert len(rows) == 3
    assert rows[0].cell_length == 8
    assert rows[0].text == "▀" * 8
