# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Dedicated tests for utility functions."""

import pytest

from structured_tutorials.typing import COUNT_TYPE
from structured_tutorials.utils import check_count


@pytest.mark.parametrize(
    ("value", "tested"),
    (
        ("foo", None),
        ("foo", 3),
        ("foo", (3, 3)),
        ("foo", (3, None)),
        ("foo", (None, 3)),
    ),
)
def test_check_count(value: str, tested: COUNT_TYPE) -> None:
    """Test check_count."""
    assert check_count(value, tested) is None


@pytest.mark.parametrize(
    ("value", "tested", "error"),
    (
        ("foo", 2, r"^3, but expected 2\.$"),
        ("foo", (2, 2), r"^3 is more then the maximum \(2\)\.$"),
        ("foo", (4, 5), r"^3 is less then the minimum \(4\)\.$"),
    ),
)
def test_check_count_with_error(value: str, tested: COUNT_TYPE, error: str) -> None:
    """Test check_count."""
    with pytest.raises(ValueError, match=error):
        check_count(value, tested)
