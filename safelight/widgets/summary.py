"""The run summary: the pane that leads the screen through space, not volume."""
from collections import Counter

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Digits, Static

from ask_image import to_answer
from safelight.engine import Exposure
from safelight.palette import MUTED, PAPER, WRONG
from safelight.rolls import Frame, outcome, score
from safelight.widgets.frame_view import FrameView
from safelight.widgets.teststrip import TestStrip
from safelight.widgets.tiles import Tiles

OUTCOME_COLOURS = {"right": PAPER, "wrong": WRONG, "unclear": MUTED}


def counts_text(tally: Counter) -> str:
    """Markup for the running count; misses only appear once they exist."""
    parts = [f"{tally['right']} right"]
    if tally["wrong"]:
        parts.append(f"[{WRONG}]{tally['wrong']} wrong[/]")
    if tally["unclear"]:
        parts.append(f"{tally['unclear']} unclear")
    return "  ".join(parts)


def facts_text(exposure: Exposure) -> str:
    """Markup for the time, tokens and model of a finished request."""
    tag = "  simulated" if exposure.simulated else ""
    tokens = f"{exposure.input_tokens or 0:,} in  {exposure.output_tokens or 0:,} out"
    return f"{exposure.seconds:.2f}s  [$muted]{tokens}[/]\n[$muted]{exposure.model}{tag}[/]"


def reading_text(frame: Frame, index: int, noul: float | None) -> str:
    """Markup for the selected frame's own result."""
    detail = frame.name if frame.truth is None else f"{frame.truth} balloons"
    title = f"Frame {index + 1}  [$muted]{detail}[/]"
    if noul is None:
        return f"{title}\n[$muted]waiting[/]"
    answer = f"{noul:.2f} {to_answer(noul)}"
    verdict = score(frame, noul)
    if verdict is None:
        return f"{title}\n{answer}"
    return f"{title}\n{answer}  ✓" if verdict else f"{title}\n{answer}  [{WRONG}]✗ wrong[/]"


class Summary(Vertical):
    """Appears with a run, then reports it live from first to last frame."""

    def __init__(self, frames: tuple[Frame, ...], id: str | None = None) -> None:
        super().__init__(id=id)
        self.frames = frames
        self.judged = sum(frame.truth is not None for frame in frames)
        self.answers: dict[str, float] = {}
        self.display = False

    def compose(self) -> ComposeResult:
        yield Static("", id="phase")
        with Horizontal(id="headline"):
            yield Digits("0", id="score")
            yield Static("", id="unit")
        yield Tiles(len(self.frames), id="tiles")
        yield Static("", id="counts")
        yield Static("", id="facts")
        yield Static("", id="reading")
        yield Static("", id="question")
        yield FrameView(self.frames[0], 0, id="enlarged")
        yield TestStrip(id="strip")

    def part(self, selector: str) -> Static:
        return self.query_one(selector, Static)

    def headline(self, number: str, unit: str) -> None:
        """Show the number that matters right now, with its word beside it."""
        self.query_one("#score", Digits).update(number)
        self.part("#unit").update(unit)

    def tally(self) -> Counter:
        """Outcomes of the frames answered so far."""
        return Counter(
            outcome(frame, self.answers[frame.name])
            for frame in self.frames
            if frame.name in self.answers
        )

    def begin(self) -> None:
        """Clear the pane for a new request and show it."""
        self.answers = {}
        self.display = True
        strip = self.query_one(TestStrip)
        strip.nouls = {}
        strip.verdicts = {}
        self.query_one(Tiles).colours = {}
        self.part("#phase").update("Asking Jev")
        self.part("#counts").update("")
        self.part("#facts").update("")
        self.tick(0.0)

    def tick(self, seconds: float) -> None:
        """Show the clock running while Jev works."""
        self.headline(f"{seconds:.1f}", "seconds")

    def exposed(self, exposure: Exposure) -> None:
        """Move from waiting on Jev to revealing the answers."""
        self.part("#facts").update(facts_text(exposure))
        if self.judged:
            self.headline("0", f"of {self.judged} right")

    def record(self, index: int, frame: Frame, noul: float) -> None:
        """Take in one frame's answer and update everything it touches."""
        self.answers[frame.name] = noul
        self.part("#phase").update(f"Revealing {len(self.answers)} of {len(self.frames)}")
        tiles = self.query_one(Tiles)
        tiles.colours = {**tiles.colours, index: OUTCOME_COLOURS.get(outcome(frame, noul), PAPER)}
        strip = self.query_one(TestStrip)
        strip.nouls = {**strip.nouls, index: noul}
        strip.verdicts = {**strip.verdicts, index: score(frame, noul)}
        if self.judged:
            self.headline(str(self.tally()["right"]), f"of {self.judged} right")
            self.part("#counts").update(counts_text(self.tally()))
        else:
            self.headline(f"{noul:.2f}", to_answer(noul))

    def finish(self) -> None:
        """Settle on the final result."""
        self.part("#phase").update("Complete")

    def show_frame(self, frame: Frame, index: int, question: str, noul: float | None) -> None:
        """Point the lower half of the pane at the selected frame."""
        self.part("#reading").update(reading_text(frame, index, noul))
        self.part("#question").update(f"[$muted]{question}[/]")
        enlarged = self.query_one("#enlarged", FrameView)
        enlarged.load(frame, index)
        enlarged.progress = 0.0 if noul is None else 1.0
        self.query_one(TestStrip).selected = index
