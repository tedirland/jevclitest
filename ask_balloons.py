"""Ask pinned Jev 1.14 whether each balloon image has more than 3 balloons.

Run with: uv run --env-file .env ask_balloons.py
"""
import json
from pathlib import Path
from time import perf_counter

from typesafe_sdk import Image, Noul, TypeSafeClient

from ask_image import IMAGES_ON, MODEL, to_answer

IMAGE_DIR = Path("balloons")
THRESHOLD = 3


def question(name: str) -> str:
    """Word the question for one image in the state."""
    return f"Are there more than {THRESHOLD} balloons in `images.{name}`?"


def is_correct(count: int, noul: float) -> bool:
    """Compare Jev's answer with the true balloon count."""
    return to_answer(noul) == ("yes" if count > THRESHOLD else "no")


def main() -> None:
    expected = json.loads((IMAGE_DIR / "expected.json").read_text())

    start = perf_counter()
    with TypeSafeClient(model=MODEL) as client:
        result = client.system_one(
            state={"images": {name: Image(IMAGE_DIR / f"{name}.png") for name in expected}},
            questions={name: Noul(instructions=question(name)) for name in expected},
            extra_headers=IMAGES_ON,
        )
    seconds = perf_counter() - start

    print(f"Model: {result.model}")
    correct = 0
    for name, count in expected.items():
        noul = result.answers[name].noul
        correct += is_correct(count, noul)
        mark = "right" if is_correct(count, noul) else "WRONG"
        print(f"{name}  balloons={count}  answer={to_answer(noul):7}  probability={noul:<5}  {mark}")
    print(f"Correct: {correct} of {len(expected)}")
    print(f"Usage: {result.usage}")
    print(f"Seconds: {seconds:.2f}")


if __name__ == "__main__":
    main()
