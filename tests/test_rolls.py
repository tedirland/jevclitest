"""Tests for rolls and the simulated engine."""
import json
from pathlib import Path

from safelight.engine import fake_noul, simulate
from safelight.rolls import Frame, discover, load_roll, outcome, score, single_frame


def make_roll(tmp_path: Path) -> Path:
    folder = tmp_path / "party"
    folder.mkdir()
    (folder / "expected.json").write_text(json.dumps({"image_1": 6, "image_2": 3}))
    return folder


def test_load_roll_reads_truth_and_questions(tmp_path):
    roll = load_roll(make_roll(tmp_path))
    assert [frame.truth for frame in roll.frames] == [6, 3]
    assert roll.questions["image_2"] == "Are there more than 3 balloons in `images.image_2`?"
    assert not roll.is_open


def test_single_frame_is_open_and_takes_a_new_question():
    roll = single_frame(Path("sample.png")).with_question("Is it red?")
    assert roll.is_open
    assert roll.questions == {"photo": "Is it red?"}


def test_score_needs_a_truth():
    assert score(Frame("a", Path("a.png"), 6), 0.9) is True
    assert score(Frame("a", Path("a.png"), 6), 0.1) is False
    assert score(Frame("a", Path("a.png")), 0.9) is None


def test_outcome_splits_misses_into_wrong_and_unclear():
    frame = Frame("a", Path("a.png"), 6)
    assert outcome(frame, 0.9) == "right"
    assert outcome(frame, 0.1) == "wrong"
    assert outcome(frame, 0.5) == "unclear"
    assert outcome(Frame("a", Path("a.png")), 0.9) is None


def test_discover_finds_rolls_then_loose_images(tmp_path):
    make_roll(tmp_path)
    (tmp_path / "loose.png").touch()
    (tmp_path / "notes.txt").touch()
    assert [roll.name for roll in discover(tmp_path)] == ["party", "loose.png"]


def test_fake_noul_is_repeatable_and_a_probability():
    frame = Frame("image_1", Path("a.png"), 6)
    assert fake_noul(frame, "q") == fake_noul(frame, "q")
    assert 0 <= fake_noul(frame, "q") <= 1


async def test_simulate_answers_every_frame_and_is_labelled(tmp_path):
    roll = load_roll(make_roll(tmp_path))
    exposure = await simulate(roll)
    assert set(exposure.nouls) == {"image_1", "image_2"}
    assert exposure.simulated
    assert exposure.seconds > 0
