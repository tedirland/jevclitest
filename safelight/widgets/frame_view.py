"""One print on the contact sheet."""
from PIL import Image
from textual.message import Message
from textual.reactive import reactive
from textual.strip import Strip
from textual.widget import Widget

from ask_image import to_answer
from safelight import photo
from safelight.palette import WRONG
from safelight.rolls import Frame, score

DEVELOP_SECONDS = 0.9


def caption(frame: Frame, noul: float) -> str:
    """Markup for a frame's border; the verdict leads so narrow frames keep it."""
    answer = f"{to_answer(noul)} {noul:.2f}"
    verdict = score(frame, noul)
    if verdict is None:
        return answer
    return f"✓ {answer}" if verdict else f"[{WRONG}]✗[/] {answer}"


class FrameView(Widget):
    """A frame that waits in grey and fades into full colour."""

    progress = reactive(0.0)

    class Picked(Message):
        """The frame was clicked."""

        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    def __init__(self, frame: Frame, index: int, id: str | None = None) -> None:
        super().__init__(id=id)
        self.rows: list[Strip] = []
        self.load(frame, index)

    def load(self, frame: Frame, index: int) -> None:
        """Put a different frame in this view."""
        self.frame = frame
        self.index = index
        self.source = Image.open(frame.path)
        self.border_title = str(index + 1)
        self.on_resize()

    def on_resize(self) -> None:
        """Rebuild the print at the new size."""
        cols, rows = self.content_size
        if not cols or not rows:
            return
        self.full = photo.fit(self.source, cols, rows)
        self.undeveloped = photo.ghost(self.full)
        self.marks = photo.tray_marks(self.full.size, seed=self.index)
        self.rebuild()

    def rebuild(self) -> None:
        """Render the print at its current stage of developing."""
        image = photo.develop(self.full, self.undeveloped, self.marks, self.progress)
        self.rows = photo.strips(image)
        self.refresh()

    def watch_progress(self) -> None:
        if self.rows:
            self.rebuild()

    def reveal(self, noul: float, instant: bool = False) -> None:
        """Develop this print and caption it with Jev's answer."""
        self.border_subtitle = caption(self.frame, noul)
        if instant:
            self.progress = 1.0
        else:
            self.animate("progress", 1.0, duration=DEVELOP_SECONDS, easing="in_out_sine")

    def reset(self) -> None:
        """Return this print to an undeveloped ghost."""
        self.border_subtitle = ""
        self.progress = 0.0

    def on_click(self) -> None:
        self.post_message(self.Picked(self.index))

    def render_line(self, y: int) -> Strip:
        if y < len(self.rows):
            return self.rows[y]
        return Strip.blank(self.content_size.width, self.rich_style)
