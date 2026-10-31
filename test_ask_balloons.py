"""Tests for the balloon test's scoring and its generated images."""
import pytest

from ask_balloons import is_correct, question
from ask_image import to_answer
from make_balloons import make_image


@pytest.mark.parametrize(
    ("noul", "answer"),
    [(0.71, "yes"), (0.7, "unclear"), (0.5, "unclear"), (0.3, "unclear"), (0.29, "no")],
)
def test_to_answer_uses_thresholds(noul, answer):
    assert to_answer(noul) == answer


@pytest.mark.parametrize(
    ("count", "noul", "correct"),
    [(4, 0.9, True), (3, 0.1, True), (3, 0.9, False), (6, 0.1, False), (6, 0.5, False)],
)
def test_is_correct_compares_with_more_than_three(count, noul, correct):
    assert is_correct(count, noul) is correct


def test_question_points_at_one_image():
    assert question("image_2") == "Are there more than 3 balloons in `images.image_2`?"


def test_make_image_fits_api_size_limits():
    width, height = make_image(6, seed=1).size
    assert 280 <= width <= 1568
    assert 280 <= height <= 1568
