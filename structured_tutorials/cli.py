# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Main CLI entrypoint."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import yaml

from structured_tutorials.errors import InvalidAlternativesSelectedError
from structured_tutorials.models import TutorialModel
from structured_tutorials.output import error, setup_logging
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

    try:
        tutorial = TutorialModel.from_file(args.path)
    except yaml.YAMLError as exc:  # an invalid YAML file
        error(f"{args.path}: Invalid YAML file:")
        print(exc, file=sys.stderr)
        sys.exit(1)
    except ValueError as ex:  # thrown by Pydantic model loading
        error(f"{args.path}: File is not a valid Tutorial:")
        print(ex, file=sys.stderr)
        sys.exit(1)

    runner = LocalTutorialRunner(
        tutorial, alternatives=tuple(args.alternatives), show_command_output=args.show_command_output
    )

    try:
        runner.validate_alternatives()
    except InvalidAlternativesSelectedError as ex:
        error(ex)
        sys.exit(1)

    runner.run()
