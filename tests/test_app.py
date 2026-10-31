"""End-to-end tests of the interface, driven through Textual's Pilot."""
from pathlib import Path

import asyncio
from collections import Counter

import pytest

from safelight.app import Safelight
from safelight.engine import Exposure
from safelight.rolls import load_roll, single_frame
from safelight.screens.proof import Phase, ProofScreen, sheet_columns
from safelight.screens.shelf import ShelfScreen
from safelight.widgets.frame_view import FrameView, caption
from safelight.widgets.summary import Summary, counts_text
from safelight.widgets.teststrip import place
from safelight.widgets.tiles import Tiles, spans

BALLOONS = load_roll(Path("balloons"))


async def instant_engine(roll) -> Exposure:
    """Answer yes to everything at once."""
    return Exposure("jev-test", {frame.name: 0.9 for frame in roll.frames}, 10, 2, 1.25)


async def stalled_engine(roll) -> Exposure:
    """Never answer, like a request stuck in flight."""
    await asyncio.Event().wait()


def make_app(target=BALLOONS, run_now=True, engine=instant_engine) -> Safelight:
    app = Safelight(target=target, run_now=run_now, engine=engine)
    app.animation_level = "none"
    return app


def score_of(app) -> str:
    return app.screen.query_one("#score").value


async def settle(pilot) -> None:
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


async def test_shelf_lists_rolls_and_opens_one():
    app = Safelight(root=Path("."), engine=instant_engine)
    app.animation_level = "none"
    async with app.run_test(size=(120, 40)) as pilot:
        assert isinstance(app.screen, ShelfScreen)
        await pilot.press("enter")
        await settle(pilot)
        assert isinstance(app.screen, ProofScreen)
        assert app.screen.roll.name == "balloons"


async def test_shelf_marks_the_chosen_row_and_opens_it():
    app = Safelight(root=Path("."), engine=instant_engine)
    app.animation_level = "none"
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        rolls = app.screen.query_one("#rolls")
        marked = lambda: [str(rolls.get_option_at_index(i).prompt).startswith("›") for i in range(2)]
        assert marked() == [True, False]
        await pilot.press("down")
        await pilot.pause()
        assert marked() == [False, True]
        await pilot.press("up")
        await pilot.pause()
        assert marked() == [True, False]
        await pilot.press("down", "enter")
        await settle(pilot)
        assert app.screen.roll.name == "sample.png"


async def test_run_scores_and_develops_every_frame():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        screen = app.screen
        assert screen.phase is Phase.DONE
        assert screen.tally() == (4, 6)
        assert all(view.progress == 1.0 for view in screen.views)


async def test_receipt_reports_score_and_seconds():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        assert app.receipt == "balloons  4/6 right  1.25s  jev-test"


async def test_arrows_move_selection_and_wrap():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await pilot.press("left")
        assert app.screen.selected == 4
        await pilot.press("right", "right")
        assert app.screen.selected == 0
        await pilot.press("down")
        assert app.screen.selected == 3


async def test_clicking_a_frame_selects_it():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await pilot.click(app.screen.views[2])
        assert app.screen.selected == 2


async def test_footer_only_offers_keys_that_work():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        assert app.screen.check_action("run", ()) is True
        assert app.screen.check_action("skip", ()) is False
        app.screen.phase = Phase.DEVELOPING
        assert app.screen.check_action("run", ()) is False
        assert app.screen.check_action("skip", ()) is True


async def test_loupe_enlarges_the_selected_frame():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await pilot.press("right")
        enlarged = app.screen.query_one("#enlarged", FrameView)
        assert enlarged.frame == app.screen.roll.frames[app.screen.selected]
        assert enlarged.progress == 1.0


async def test_escape_returns_to_the_shelf():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await pilot.press("escape")
        assert isinstance(app.screen, ShelfScreen)


async def test_rerun_resets_then_finishes():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await pilot.press("r")
        await settle(pilot)
        assert app.screen.phase is Phase.DONE


async def test_open_roll_waits_for_a_question_then_runs_it():
    app = make_app(single_frame(Path("sample.png")), run_now=False)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.screen.phase is Phase.READY
        app.screen.query_one("#ask").value = ""
        await pilot.press(*"red", "enter")
        await settle(pilot)
        assert app.screen.roll.questions["photo"] == "red"
        assert app.screen.phase is Phase.DONE
        assert app.receipt == "sample.png  1.25s  jev-test"


async def test_escape_works_while_a_request_is_in_flight():
    app = make_app(engine=stalled_engine)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.screen.phase is Phase.EXPOSING
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, ShelfScreen)
        assert app.receipt is None


async def test_quit_works_while_a_request_is_in_flight():
    app = make_app(engine=stalled_engine)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("q")
    assert app.receipt is None


async def test_run_key_is_ignored_while_exposing():
    app = make_app(engine=stalled_engine)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()
        assert app.screen.phase is Phase.EXPOSING


async def test_space_skips_the_reveal():
    app = Safelight(target=BALLOONS, engine=instant_engine)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.screen.phase is Phase.DEVELOPING
        await pilot.press("space")
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert app.screen.phase is Phase.DONE
        assert app.screen.tally() == (4, 6)


async def test_single_image_hides_the_redundant_panels():
    app = make_app(single_frame(Path("sample.png")), run_now=False)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.screen.query_one("#enlarged").display is False
        assert app.screen.query_one("#strip").display is False


@pytest.mark.parametrize("size", [(80, 24), (120, 30), (200, 60)])
async def test_layout_survives_common_terminal_sizes(size):
    app = make_app()
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        assert all(view.rows for view in app.screen.views)


@pytest.mark.parametrize(("count", "columns"), [(1, 1), (4, 2), (6, 3), (9, 3), (10, 4)])
def test_sheet_columns(count, columns):
    assert sheet_columns(count) == columns


def test_place_keeps_every_frame_visible_when_answers_collide():
    columns = place({0: 0.9, 1: 0.9, 2: 1.0, 3: 1.0}, 10)
    assert sorted(columns.values()) == [0, 1, 2, 3]
    assert all(0 <= column < 10 for column in columns)


def test_caption_leads_with_the_verdict_so_truncation_keeps_it():
    assert caption(BALLOONS.frames[1], 0.9).index("✗") < caption(BALLOONS.frames[1], 0.9).index("yes")
    assert caption(BALLOONS.frames[0], 0.9).startswith("✓")


async def test_summary_is_hidden_until_a_run_starts():
    app = make_app(single_frame(Path("sample.png")), run_now=False)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        summary = app.screen.query_one(Summary)
        assert summary.display is False
        await pilot.press("enter")
        await settle(pilot)
        assert summary.display is True


async def test_summary_sits_left_of_the_sheet_and_outsizes_a_frame():
    app = make_app()
    async with app.run_test(size=(130, 40)) as pilot:
        await settle(pilot)
        summary = app.screen.query_one(Summary)
        assert app.screen.query_one("#sheet").region.x >= summary.region.right
        assert summary.size.width > app.screen.views[0].size.width


async def test_summary_shows_the_final_score():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        assert score_of(app) == "4"
        assert str(app.screen.query_one("#unit").render()) == "of 6 right"
        assert len(app.screen.query_one(Tiles).colours) == 6


async def test_summary_updates_live_during_the_reveal():
    seen = []
    app = Safelight(target=BALLOONS, engine=instant_engine)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        while app.screen.phase is not Phase.DONE:
            seen.append(score_of(app))
            await pilot.pause(0.1)
    assert len(set(seen)) >= 3
    assert seen == sorted(seen)


async def test_clock_runs_in_the_headline_while_waiting():
    app = make_app(engine=stalled_engine)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.25)
        assert score_of(app) != "0.0"
        assert str(app.screen.query_one("#unit").render()) == "seconds"


async def test_open_question_makes_the_reading_the_headline():
    app = make_app(single_frame(Path("sample.png")), run_now=False)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await settle(pilot)
        assert score_of(app) == "0.90"
        assert str(app.screen.query_one("#unit").render()) == "yes"


async def test_rerun_keeps_the_pane_and_clears_its_results():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        summary = app.screen.query_one(Summary)
        summary.begin()
        assert summary.query_one(Tiles).colours == {}
        assert summary.display is True


@pytest.mark.parametrize("size", [(70, 15), (80, 24), (100, 18), (120, 30), (130, 34), (130, 40), (200, 60)])
async def test_summary_parts_never_overlap_or_spill(size):
    app = make_app()
    async with app.run_test(size=size) as pilot:
        await settle(pilot)
        summary = app.screen.query_one(Summary)
        parts = sorted(
            (child for child in summary.children if child.display),
            key=lambda child: child.region.y,
        )
        for upper, lower in zip(parts, parts[1:]):
            assert upper.region.bottom <= lower.region.y, (upper.id, lower.id)
        assert parts[-1].region.bottom <= summary.region.bottom


def test_counts_only_mention_misses_that_happened():
    assert counts_text(Counter(right=5)) == "5 right"
    assert "1 wrong" in counts_text(Counter(right=5, wrong=1))


@pytest.mark.parametrize(("count", "width"), [(6, 40), (1, 40), (12, 40), (7, 30)])
def test_tiles_fill_the_width_exactly(count, width):
    assert sum(spans(count, width)) + count - 1 == width
