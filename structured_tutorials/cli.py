# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

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
    parser.add_argument("-a", "--alternative", dest="alternatives", action="append", default=[])
    args = parser.parse_args(argv)

    tutorial = TutorialModel.from_file(args.path)
    runner = LocalTutorialRunner(tutorial, alternatives=tuple(args.alternatives))
    runner.validate_alternatives()
    runner.run()
