"""Test local runner."""

from structured_tutorials.models import TutorialModel
from structured_tutorials.runners.local import LocalTutorialRunner


def test_simple_tutorial(simple_tutorial: TutorialModel) -> None:
    """Test the local runner by running a simple tutorial."""
    runner = LocalTutorialRunner(simple_tutorial)
    runner.run()
