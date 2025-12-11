# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Tests for sphinx utility functions."""

from pathlib import Path

import pytest
from sphinx.errors import ExtensionError

from structured_tutorials.sphinx.utils import get_tutorial_path


@pytest.mark.parametrize(
    ("tutorial_path", "arg", "expected"),
    (
        (
            Path(".").absolute(),
            "tutorials/simple/simple.yaml",
            (Path(".").absolute() / "tutorials/simple/simple.yaml"),
        ),
        (
            Path(".").absolute(),
            "docs/tutorials/quickstart/tutorial.yaml",
            (Path(".").absolute() / "docs/tutorials/quickstart/tutorial.yaml"),
        ),
    ),
)
def test_get_tutorial_path(tutorial_path: Path, arg: str, expected: Path) -> None:
    """Test basic functionality."""
    assert get_tutorial_path(tutorial_path, arg) == expected


def test_with_absolute_path() -> None:
    """Test error when passing an absolute path."""
    with pytest.raises(ExtensionError, match=r"^/foo: Path must not be absolute\."):
        get_tutorial_path(Path(".").absolute(), "/foo")


def test_file_does_not_exist() -> None:
    """Test error when file does not exist."""
    with pytest.raises(ExtensionError, match=r"File not found\."):
        get_tutorial_path(Path(".").absolute(), "does/not/exist")
