"""The test strip: every frame's Noul laid out on one line."""
from rich.style import Style
from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

from safelight.palette import LINE, MUTED, PAPER, WRONG

LEFT, RIGHT = "no ", " yes"


def place(nouls: dict[int, float], width: int) -> dict[int, int]:
    """Give each frame a free column near its Noul, returning column to frame."""
    columns: dict[int, int] = {}
    for index, noul in sorted(nouls.items(), key=lambda item: item[1]):
        column = round(noul * (width - 1))
        while column in columns and column < width - 1:
            column += 1
        while column in columns:
            column -= 1
        columns[column] = index
    return columns


class TestStrip(Widget):
    """Shows where each answer sits between no and yes."""

    __test__ = False

    nouls: reactive[dict[int, float]] = reactive(dict, always_update=True)
    verdicts: reactive[dict[int, bool | None]] = reactive(dict, always_update=True)
    selected = reactive(0)

    def style_for(self, index: int) -> Style:
        """Quiet by default: wrong answers tint, the selected frame brightens."""
        if self.verdicts.get(index) is False:
            return Style(color=WRONG, bold=index == self.selected)
        return Style(color=PAPER if index == self.selected else MUTED)

    def render(self) -> Text:
        width = self.content_size.width - len(LEFT) - len(RIGHT)
        columns = place(self.nouls, width)
        text = Text(LEFT, MUTED, no_wrap=True)
        for column in range(width):
            index = columns.get(column)
            if index is None:
                text.append("─", LINE)
            else:
                text.append(str(index + 1)[-1], self.style_for(index))
        text.append(RIGHT, MUTED)
        return text
