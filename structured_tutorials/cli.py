"""Main CLI entrypoint."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from structured_tutorials.models import TutorialModel
from structured_tutorials.runners.local import LocalTutorialRunner


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry function for the command-line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)

    tutorial = TutorialModel.from_file(args.path)
    runner = LocalTutorialRunner(tutorial)
    runner.run()
