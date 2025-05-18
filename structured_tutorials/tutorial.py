"""Tutorial-related functions."""

import os
import pathlib
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from yaml import safe_load

from structured_tutorials.models import Tutorial
from structured_tutorials.runners.local import LocalRunner


@contextmanager
def chdir(path: Path) -> Iterator[None]:
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_cwd)


def load_tutorial(path: pathlib.Path) -> Tutorial:
    """Load a tutorial from a YAML file."""
    with open(path) as stream:
        tutorial_data = safe_load(stream)
    tutorial = Tutorial.model_validate(tutorial_data, context={"path": path})
    return tutorial


def run_tutorial(tutorial: Tutorial) -> None:
    """Run a loaded tutorial."""
    if tutorial.config.type == "local":
        runner = LocalRunner(tutorial)

    with chdir(tutorial.config.working_directory):
        runner.run()
