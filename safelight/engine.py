"""Exposures: one batched request to Jev, answered all at once.

`simulate` stands in for Jev while the interface is built. A real engine keeps
the same signature and calls `TypeSafeClient.system_one`.
"""
import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import perf_counter

from ask_image import MODEL
from safelight.rolls import Frame, Roll


@dataclass(frozen=True)
class Exposure:
    """The result of one request: every frame's Noul and the time it took."""

    model: str
    nouls: dict[str, float]
    input_tokens: int | None
    output_tokens: int | None
    seconds: float
    simulated: bool = False


Engine = Callable[[Roll], Awaitable[Exposure]]


def fake_noul(frame: Frame, question: str) -> float:
    """Make a repeatable, plausible Noul, including the odd miss."""
    rng = random.Random(f"safelight:{frame.name}:{question}")
    leaning_yes = rng.random() > 0.4 if frame.truth is None else frame.truth > 3
    roll = rng.random()
    if roll < 0.75:
        confident = rng.uniform(0.82, 0.98)
    elif roll < 0.9:
        confident = rng.uniform(0.35, 0.65)
    else:
        confident = rng.uniform(0.05, 0.25)
    return round(confident if leaning_yes else 1 - confident, 3)


async def simulate(roll: Roll) -> Exposure:
    """Pretend to ask Jev, with a realistic pause."""
    start = perf_counter()
    await asyncio.sleep(1.0 + 0.2 * len(roll.frames))
    nouls = {frame.name: fake_noul(frame, roll.questions[frame.name]) for frame in roll.frames}
    seconds = perf_counter() - start
    return Exposure(MODEL, nouls, 1240 * len(roll.frames), 16 * len(roll.frames), seconds, simulated=True)
