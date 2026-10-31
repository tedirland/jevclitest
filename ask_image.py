"""Ask pinned Jev 1.14 one yes or no question about an image.

Run with: uv run --env-file .env ask_image.py [image] [question]
"""
import sys
from pathlib import Path
from time import perf_counter

from typesafe_sdk import Image, Noul, TypeSafeClient

MODEL = "jev-1.14.0"
IMAGES_ON = {"TypeSafe-Danger-Zone-Images": "true"}
DEFAULT_IMAGE = "sample.png"
DEFAULT_QUESTION = "Is there a house in `photo`?"


def to_answer(noul: float) -> str:
    """Read a Noul probability as yes, no, or unclear."""
    if noul > 0.7:
        return "yes"
    if noul < 0.3:
        return "no"
    return "unclear"


def main() -> None:
    image = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMAGE
    question = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_QUESTION

    start = perf_counter()
    with TypeSafeClient(model=MODEL) as client:
        result = client.system_one(
            state={"photo": Image(Path(image))},
            questions={"answer": Noul(instructions=question)},
            extra_headers=IMAGES_ON,
        )
    seconds = perf_counter() - start

    noul = result.answers["answer"].noul
    print(f"Model:       {result.model}")
    print(f"Image:       {image}")
    print(f"Question:    {question}")
    print(f"Answer:      {to_answer(noul)}")
    print(f"Probability: {noul}")
    print(f"Usage:       {result.usage}")
    print(f"Seconds:     {seconds:.2f}")


if __name__ == "__main__":
    main()
