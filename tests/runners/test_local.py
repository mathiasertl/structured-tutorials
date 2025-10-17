"""Test local runner."""

import pytest
from pytest_subprocess import FakeProcess

from structured_tutorials.models import TutorialModel
from structured_tutorials.runners.local import LocalTutorialRunner
from tests.conftest import DOCS_TUTORIALS_DIR


def test_simple_tutorial(simple_tutorial: TutorialModel) -> None:
    """Test the local runner by running a simple tutorial."""
    runner = LocalTutorialRunner(simple_tutorial)
    runner.run()


def test_exit_code_tutorial(fp: FakeProcess) -> None:
    """Test status code specification."""
    fp.register(["true"])
    fp.register(["true"])
    fp.register(["false"], returncode=1)
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "exit_code" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    runner.run()


def test_exit_code_tutorial_with_unexpected_exit_code(fp: FakeProcess) -> None:
    """Test behavior if a command has the wrong status code."""
    fp.register(["true"])
    fp.register(["true"], returncode=1)
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "exit_code" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    with pytest.raises(RuntimeError, match=r"true failed with return code 1 \(expected: 0\)\.$"):
        runner.run()
