# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Main CLI entrypoint."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from structured_tutorials.models import TutorialModel
from structured_tutorials.output import setup_logging
from structured_tutorials.runners.local import LocalTutorialRunner


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry function for the command-line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("-a", "--alternative", dest="alternatives", action="append", default=[])
    parser.add_argument("--no-colors", action="store_true", default=False)
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Override root log level",
    )
    parser.add_argument(
        "--hide-commands",
        dest="show_commands",
        action="store_false",
        default=True,
        help="Do not show commands that are run by the tutorial.",
    )
    parser.add_argument(
        "--hide-command-output",
        dest="show_command_output",
        action="store_false",
        default=True,
        help="Do not show the output of commands that are run on the terminal.",
    )
    args = parser.parse_args(argv)

    setup_logging(level=args.log_level, no_colors=args.no_colors, show_commands=args.show_commands)

    tutorial = TutorialModel.from_file(args.path)
    runner = LocalTutorialRunner(
        tutorial, alternatives=tuple(args.alternatives), show_command_output=args.show_command_output
    )
    runner.validate_alternatives()
    runner.run()
