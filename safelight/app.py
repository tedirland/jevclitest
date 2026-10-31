"""The Safelight application."""
from pathlib import Path

from textual.app import App

from safelight.engine import Engine, simulate
from safelight.palette import SAFELIGHT
from safelight.rolls import Roll, discover
from safelight.screens.proof import ProofScreen
from safelight.screens.shelf import ShelfScreen


class Safelight(App):
    """Image experiments for Jev."""

    CSS_PATH = "safelight.tcss"
    TITLE = "Safelight"
    ENABLE_COMMAND_PALETTE = False

    def __init__(
        self,
        root: Path = Path("."),
        target: Roll | None = None,
        run_now: bool = True,
        engine: Engine = simulate,
    ) -> None:
        super().__init__()
        self.root = root
        self.target = target
        self.run_now = run_now
        self.engine = engine
        self.receipt: str | None = None
        self.register_theme(SAFELIGHT)
        self.theme = SAFELIGHT.name

    def on_mount(self) -> None:
        self.push_screen(ShelfScreen(discover(self.root)))
        if self.target:
            self.push_screen(ProofScreen(self.target, self.run_now))
