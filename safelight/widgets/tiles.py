"""A hairline with one segment per frame, lit as answers land."""
from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

from safelight.palette import LINE


def spans(count: int, width: int) -> list[int]:
    """Split `width`, less one-cell gaps, into `count` near-equal segments."""
    room = max(count, width - (count - 1))
    return [room // count + (1 if index < room % count else 0) for index in range(count)]


class Tiles(Widget):
    """The roll's progress and results at a glance."""

    colours: reactive[dict[int, str]] = reactive(dict, always_update=True)

    def __init__(self, count: int, id: str | None = None) -> None:
        super().__init__(id=id)
        self.count = count

    def render(self) -> Text:
        text = Text(no_wrap=True)
        for index, span in enumerate(spans(self.count, self.content_size.width)):
            if index:
                text.append(" ")
            text.append("━" * span, self.colours.get(index, LINE))
        return text
