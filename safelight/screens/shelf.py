"""The shelf: pick a roll to run or an image to ask about."""
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Footer, OptionList, Static
from textual.widgets.option_list import Option

from safelight.rolls import Roll
from safelight.screens.proof import ProofScreen


def label(roll: Roll, active: bool) -> str:
    """One aligned row of the shelf, marked and bright when it is chosen."""
    count = len(roll.frames)
    frames = f"{count} image{'' if count == 1 else 's'}"
    row = f"{roll.name:<16} {frames:<10} {roll.summary}\n"
    return f"› {row}" if active else f"[$muted]  {row}[/]"


class ShelfScreen(Screen):
    """The home screen: a name, and what can be run."""

    BINDINGS = [Binding("q", "quit", "quit")]

    def __init__(self, rolls: list[Roll]) -> None:
        super().__init__()
        self.rolls = rolls

    def compose(self) -> ComposeResult:
        with Vertical(id="welcome"):
            with Center():
                yield Static("s a f e l i g h t", id="wordmark")
            with Center():
                yield Static("[$muted]image experiments for Jev[/]", id="tagline")
            with Center():
                yield OptionList(*self.options(), id="rolls")
        yield Footer()

    def options(self) -> list[Option]:
        return [Option(label(roll, index == 0)) for index, roll in enumerate(self.rolls)]

    def on_mount(self) -> None:
        self.query_one("#rolls").focus()

    @on(OptionList.OptionHighlighted)
    def mark(self, event: OptionList.OptionHighlighted) -> None:
        """Move the marker to the highlighted row."""
        for index, roll in enumerate(self.rolls):
            prompt = label(roll, index == event.option_index)
            event.option_list.replace_option_prompt_at_index(index, prompt)

    @on(OptionList.OptionSelected)
    def open_roll(self, event: OptionList.OptionSelected) -> None:
        roll = self.rolls[event.option_index]
        self.app.push_screen(ProofScreen(roll, run_now=not roll.is_open))
