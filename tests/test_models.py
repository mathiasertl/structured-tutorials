"""Test models."""

from pathlib import Path

from structured_tutorials.models import TutorialModel


def test_from_file(tutorial_paths: Path) -> None:
    """Test loading all known tutorials."""
    assert isinstance(TutorialModel.from_file(tutorial_paths), TutorialModel)
