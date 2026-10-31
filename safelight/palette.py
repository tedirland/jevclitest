"""Quiet, semantic colours. Images carry the colour; only a wrong answer adds any."""
from textual.theme import Theme

BASE = "#121110"
OVERLAY = "#1C1A18"
LINE = "#2E2B28"
PAPER = "#E6E1DA"
MUTED = "#A39C93"
WRONG = "#D07A6E"

SAFELIGHT = Theme(
    name="safelight",
    primary=PAPER,
    secondary=MUTED,
    accent=PAPER,
    foreground=PAPER,
    background=BASE,
    surface=BASE,
    panel=OVERLAY,
    success=PAPER,
    warning=MUTED,
    error=WRONG,
    dark=True,
    variables={"muted": MUTED, "line": LINE},
)
