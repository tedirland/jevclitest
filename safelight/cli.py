"""Command line entry point."""
import argparse
from pathlib import Path

from safelight.app import Safelight
from safelight.rolls import Roll, load_roll, single_frame


def parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    result = argparse.ArgumentParser(
        prog="safelight",
        description="Image experiments for Jev.",
        epilog="""examples:
  safelight                      browse rolls in this folder
  safelight balloons             run a roll
  safelight sample.png           ask about one image
  safelight sample.png 'Is there a house in `photo`?'""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    result.add_argument("target", nargs="?", type=Path, help="a roll folder or an image")
    result.add_argument("question", nargs="?", help="question for a single image")
    return result


def resolve(target: Path | None, question: str | None, parser_: argparse.ArgumentParser) -> tuple[Roll | None, bool]:
    """Turn arguments into a roll, and whether to run it straight away."""
    if target is None:
        return None, False
    if target.is_dir() and (target / "expected.json").exists():
        if question:
            parser_.error(f"{target} asks its own question; a typed question only applies to one image")
        return load_roll(target), True
    if target.is_file():
        roll = single_frame(target)
        return (roll.with_question(question), True) if question else (roll, False)
    parser_.error(f"{target} is not an image or a folder with an expected.json")


def main() -> None:
    """Run Safelight, then leave a one-line receipt in the terminal."""
    arguments = parser()
    options = arguments.parse_args()
    roll, run_now = resolve(options.target, options.question, arguments)
    app = Safelight(target=roll, run_now=run_now)
    app.run()
    if app.receipt:
        print(app.receipt)
