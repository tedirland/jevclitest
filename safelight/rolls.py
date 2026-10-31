"""Rolls: the image experiments Safelight can run."""
import json
from dataclasses import dataclass, replace
from pathlib import Path

from ask_balloons import THRESHOLD, is_correct, question
from ask_image import DEFAULT_QUESTION, to_answer

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass(frozen=True)
class Frame:
    """One image in a roll, with its known balloon count if it has one."""

    name: str
    path: Path
    truth: int | None = None


@dataclass(frozen=True)
class Roll:
    """A set of frames and the question asked about each."""

    name: str
    frames: tuple[Frame, ...]
    questions: dict[str, str]

    @property
    def is_open(self) -> bool:
        """An open roll takes a typed question rather than a fixed one."""
        return all(frame.truth is None for frame in self.frames)

    @property
    def summary(self) -> str:
        """One line describing what this roll asks."""
        if self.is_open:
            return "ask anything"
        return f"more than {THRESHOLD} balloons?"

    def with_question(self, text: str) -> "Roll":
        """Return this roll asking `text` about every frame."""
        return replace(self, questions={frame.name: text for frame in self.frames})


def score(frame: Frame, noul: float) -> bool | None:
    """Judge an answer against the truth; None when the truth is unknown."""
    return None if frame.truth is None else is_correct(frame.truth, noul)


def outcome(frame: Frame, noul: float) -> str | None:
    """Name the result: right, wrong, unclear, or None without a truth."""
    verdict = score(frame, noul)
    if verdict is None:
        return None
    if verdict:
        return "right"
    return "unclear" if to_answer(noul) == "unclear" else "wrong"


def load_roll(folder: Path) -> Roll:
    """Load a folder of images described by its expected.json."""
    expected = json.loads((folder / "expected.json").read_text())
    frames = tuple(Frame(name, folder / f"{name}.png", count) for name, count in expected.items())
    return Roll(folder.name, frames, {frame.name: question(frame.name) for frame in frames})


def single_frame(path: Path, text: str = DEFAULT_QUESTION) -> Roll:
    """Wrap one image as an open roll."""
    frame = Frame("photo", path)
    return Roll(path.name, (frame,), {frame.name: text})


def discover(root: Path) -> list[Roll]:
    """Find every roll and loose image directly under `root`."""
    folders = sorted(path.parent for path in root.glob("*/expected.json"))
    images = sorted(path for path in root.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)
    return [load_roll(folder) for folder in folders] + [single_frame(path) for path in images]
