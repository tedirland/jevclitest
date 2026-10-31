"""The proof screen: expose a roll, then develop it frame by frame."""
import asyncio
from contextlib import suppress
from enum import Enum, auto
from math import ceil, sqrt
from time import perf_counter

from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal
from textual.reactive import var
from textual.screen import Screen
from textual.widgets import Footer, Input, Static

from safelight.engine import Exposure
from safelight.rolls import Roll, score
from safelight.widgets.frame_view import FrameView
from safelight.widgets.summary import Summary

REVEAL_SECONDS = 0.7


class Phase(Enum):
    """Where a run has got to."""

    READY = auto()
    EXPOSING = auto()
    DEVELOPING = auto()
    DONE = auto()


def sheet_columns(count: int) -> int:
    """Columns for a contact sheet of `count` frames."""
    return ceil(sqrt(count))


class ProofScreen(Screen):
    """Run summary on the left, contact sheet on the right."""

    VERTICAL_BREAKPOINTS = [(0, "-short"), (26, "-tall"), (38, "-towering")]

    BINDINGS = [
        Binding("left", "move(-1)", "frame", key_display="←→"),
        Binding("right", "move(1)", "frame", show=False),
        Binding("up", "move_row(-1)", show=False),
        Binding("down", "move_row(1)", show=False),
        Binding("r", "run", "run"),
        Binding("space", "skip", "skip"),
        Binding("escape", "back", "back"),
        Binding("q", "quit_with_receipt", "quit"),
    ]

    phase = var(Phase.READY, bindings=True)

    def __init__(self, roll: Roll, run_now: bool = True) -> None:
        super().__init__()
        self.roll = roll
        self.run_now = run_now
        self.selected = 0
        self.exposure: Exposure | None = None
        self.answers: dict[str, float] = {}
        self.hurry = asyncio.Event()

    def compose(self) -> ComposeResult:
        yield Static(f"safelight  [$muted]{self.roll.name}[/]", id="masthead")
        with Horizontal(id="bench"):
            yield Summary(self.roll.frames, id="summary")
            with Grid(id="sheet"):
                for index, frame in enumerate(self.roll.frames):
                    yield FrameView(frame, index)
        if self.roll.is_open:
            yield Input(self.roll.questions["photo"], placeholder="Ask about `photo`", id="ask")
        yield Footer()

    def on_mount(self) -> None:
        self.set_class(len(self.roll.frames) == 1, "single")
        self.query_one("#sheet").styles.grid_size_columns = sheet_columns(len(self.roll.frames))
        self.select(0)
        if self.run_now:
            self.run_roll()
        elif self.roll.is_open:
            self.query_one("#ask").focus()

    @property
    def views(self) -> list[FrameView]:
        return list(self.query("#sheet FrameView").results(FrameView))

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        """Only offer keys that do something in the current phase."""
        if action == "run":
            return self.phase in (Phase.READY, Phase.DONE)
        if action == "skip":
            return self.phase is Phase.DEVELOPING
        return True

    @property
    def instant(self) -> bool:
        """True when motion is switched off or the user asked to skip."""
        return self.hurry.is_set() or self.app.animation_level == "none"

    def select(self, index: int) -> None:
        """Mark a frame and show it in the summary pane."""
        self.selected = index % len(self.views)
        for view in self.views:
            view.set_class(view.index == self.selected, "selected")
        frame = self.roll.frames[self.selected]
        question = self.roll.questions[frame.name]
        self.query_one(Summary).show_frame(frame, self.selected, question, self.answers.get(frame.name))

    def action_move(self, step: int) -> None:
        self.select(self.selected + step)

    def action_move_row(self, step: int) -> None:
        self.select(self.selected + step * sheet_columns(len(self.views)))

    @on(FrameView.Picked)
    def picked(self, message: FrameView.Picked) -> None:
        self.select(message.index)

    def action_run(self) -> None:
        self.run_roll()

    def action_skip(self) -> None:
        self.hurry.set()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_quit_with_receipt(self) -> None:
        self.app.exit()

    @on(Input.Submitted, "#ask")
    def ask(self, event: Input.Submitted) -> None:
        if event.value.strip() and self.phase in (Phase.READY, Phase.DONE):
            self.roll = self.roll.with_question(event.value.strip())
            self.run_roll()

    def clear(self) -> None:
        """Return every print to a ghost before a new exposure."""
        self.answers = {}
        self.exposure = None
        self.hurry.clear()
        for view in self.views:
            view.reset()

    @work(exclusive=True)
    async def run_roll(self) -> None:
        """Expose the roll, then develop each frame in turn."""
        self.clear()
        self.query_one(Summary).begin()
        self.select(self.selected)
        await self.expose()
        await self.develop()
        self.finish()

    async def expose(self) -> None:
        """Wait for Jev, showing the real time as it passes."""
        self.phase = Phase.EXPOSING
        summary = self.query_one(Summary)
        start = perf_counter()
        ticker = self.set_interval(0.1, lambda: summary.tick(perf_counter() - start))
        self.exposure = await self.app.engine(self.roll)
        ticker.stop()
        summary.exposed(self.exposure)

    async def develop(self) -> None:
        """Reveal the answers one frame at a time."""
        self.phase = Phase.DEVELOPING
        summary = self.query_one(Summary)
        for view in self.views:
            noul = self.exposure.nouls[view.frame.name]
            self.answers[view.frame.name] = noul
            view.reveal(noul, self.instant)
            summary.record(view.index, view.frame, noul)
            self.select(view.index)
            await self.linger()

    async def linger(self) -> None:
        """Hold on a frame long enough to read it, unless skipped."""
        if not self.instant:
            with suppress(TimeoutError):
                await asyncio.wait_for(self.hurry.wait(), REVEAL_SECONDS)

    def finish(self) -> None:
        """Settle the summary and leave a receipt for the terminal."""
        self.phase = Phase.DONE
        self.select(self.selected)
        self.query_one(Summary).finish()
        self.app.receipt = self.receipt()

    def tally(self) -> tuple[int, int]:
        """Frames judged right, and frames with a truth to judge against."""
        verdicts = [score(frame, self.answers[frame.name]) for frame in self.roll.frames]
        judged = [verdict for verdict in verdicts if verdict is not None]
        return sum(judged), len(judged)

    def receipt(self) -> str:
        """Plain summary printed to the terminal after quitting."""
        right, total = self.tally()
        score_text = f"{right}/{total} right  " if total else ""
        tag = "  (simulated)" if self.exposure.simulated else ""
        return f"{self.roll.name}  {score_text}{self.exposure.seconds:.2f}s  {self.exposure.model}{tag}"
