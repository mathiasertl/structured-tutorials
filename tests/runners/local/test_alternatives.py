# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test alternatives."""

from pathlib import Path

import pytest
from pytest_subprocess import FakeProcess

from structured_tutorials.errors import InvalidAlternativesSelectedError
from structured_tutorials.models import TutorialModel
from structured_tutorials.runners.local import LocalTutorialRunner


@pytest.mark.tutorial("alternatives")
def test_alternatives(fp: FakeProcess, tutorial: TutorialModel) -> None:
    """Run a tutorial with alternatives."""
    fp.register("ls foo")
    runner = LocalTutorialRunner(tutorial, alternatives=("foo",))
    runner.run()

    fp.register("ls bar")
    runner = LocalTutorialRunner(tutorial, alternatives=("bar",))
    runner.run()


@pytest.mark.tutorial("alternatives-files")
def test_alternatives_with_file_part(tmp_path: Path, tutorial: TutorialModel) -> None:
    """Run a tutorial with alternatives containing files."""
    runner = LocalTutorialRunner(tutorial, alternatives=("foo",))
    runner.context["tmp_path"] = tmp_path
    runner.run()
    assert (tmp_path / "foo.txt").exists()

    runner = LocalTutorialRunner(tutorial, alternatives=("bar",))
    runner.context["tmp_path"] = tmp_path
    runner.run()
    assert (tmp_path / "bar.txt").exists()


@pytest.mark.tutorial("alternatives")
def test_alternatives_with_no_selected_part(tutorial: TutorialModel) -> None:
    """Run with an alternative that does not exist."""
    runner = LocalTutorialRunner(tutorial, alternatives=("bla",))
    with pytest.raises(InvalidAlternativesSelectedError):
        runner.validate_alternatives()
    # Running the tutorial itself does not check if an alternative is selected.
    runner.run()
