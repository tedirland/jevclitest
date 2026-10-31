"""Tests for command line parsing."""
from pathlib import Path

import pytest

from safelight.cli import parser, resolve


def run_resolve(*arguments: str):
    build = parser()
    options = build.parse_args(list(arguments))
    return resolve(options.target, options.question, build)


def test_no_arguments_opens_the_shelf():
    assert run_resolve() == (None, False)


def test_folder_runs_straight_away():
    roll, run_now = run_resolve("balloons")
    assert roll.name == "balloons"
    assert run_now


def test_image_alone_waits_for_a_question():
    roll, run_now = run_resolve("sample.png")
    assert roll.is_open
    assert not run_now


def test_image_with_question_runs_it():
    roll, run_now = run_resolve("sample.png", "Is it red?")
    assert roll.questions["photo"] == "Is it red?"
    assert run_now


@pytest.mark.parametrize("arguments", [("missing.png",), ("balloons", "extra question")])
def test_bad_arguments_exit_with_usage_error(arguments, capsys):
    with pytest.raises(SystemExit) as caught:
        run_resolve(*arguments)
    assert caught.value.code == 2
    assert "safelight" in capsys.readouterr().err
