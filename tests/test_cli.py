# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test the cli entry point function."""

from structured_tutorials.cli import main
from structured_tutorials.models import TutorialModel


def test_simple_tutorial(simple_tutorial: TutorialModel) -> None:
    """Test the cli entry point function by running a simple tutorial."""
    main([str(simple_tutorial.path)])
