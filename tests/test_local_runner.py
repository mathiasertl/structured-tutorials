"""Test the local runner."""

import pytest
from pytest_subprocess.fake_process import FakeProcess

from structured_tutorials.models import Command
from structured_tutorials.runners.base import TutorialError
from structured_tutorials.tutorial import load_tutorial, run_tutorial
from tests.conftest import DATA_DIR


def test_minimal(fp: FakeProcess) -> None:
    """Test the minimal tutorial."""
    fp.register(["ls"])
    tutorial = load_tutorial(DATA_DIR / "minimal.yaml")
    run_tutorial(tutorial)
    assert list(fp.calls) == [("ls",)]


def test_minimal_with_error(fp: FakeProcess) -> None:
    """Test the minimal tutorial that throws an error."""
    fp.register(["ls"], returncode=1)
    tutorial = load_tutorial(DATA_DIR / "minimal.yaml")
    with pytest.raises(TutorialError, match=r"^ls: Return code 1 \(expected: 0\)\.$"):
        run_tutorial(tutorial)
    assert list(fp.calls) == [("ls",)]


def test_minimal_with_expected_error(fp: FakeProcess) -> None:
    """Test the minimal tutorial that throws an expected error."""
    fp.register(["ls"], returncode=1)
    tutorial = load_tutorial(DATA_DIR / "minimal.yaml")
    step = tutorial.parts[0].steps[0]
    assert isinstance(step, Command)
    step.returncode = 1
    run_tutorial(tutorial)
    assert list(fp.calls) == [("ls",)]
