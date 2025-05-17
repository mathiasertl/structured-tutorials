"""Main command line functions."""

import argparse
import pathlib

from structured_tutorials.tutorial import load_tutorial, run_tutorial


def main() -> None:
    """Main entry function for the command-line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=pathlib.Path)
    args = parser.parse_args()
    tutorial = load_tutorial(args.path)
    run_tutorial(tutorial)
