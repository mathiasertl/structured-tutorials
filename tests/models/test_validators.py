# Copyright (c) 2026 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Dedicated tests for validator functions."""

from pathlib import Path

import pytest

from structured_tutorials.models.validators import validate_relative_path


def test_validate_relative_path() -> None:
    """Test correct value for validate_relative_path()."""
    value = Path("test/")
    assert validate_relative_path(value) == value


def test_validate_relative_path_with_absolute_path() -> None:
    """Test error when passing an absolute path."""
    with pytest.raises(ValueError, match="Path must be relative"):
        validate_relative_path(Path("/test/"))
