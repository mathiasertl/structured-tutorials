"""Test the local runner."""

import pytest

from structured_tutorials.runners.base import TutorialError
from structured_tutorials.tutorial import load_tutorial, run_tutorial
from tests.conftest import DATA_DIR


def test_minimal(fp) -> None:
    """Test the minimal tutorial."""
    fp.register(["ls"])
    tutorial = load_tutorial(DATA_DIR / "minimal.yaml")
    run_tutorial(tutorial)


def test_minimal_with_error(fp) -> None:
    """Test the minimal tutorial."""
    fp.register(["ls"], returncode=1)
    tutorial = load_tutorial(DATA_DIR / "minimal.yaml")
    with pytest.raises(TutorialError, match=r"^ls: Return code 1 \(expected: 0\)\.$"):
        run_tutorial(tutorial)
