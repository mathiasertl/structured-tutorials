# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Validators for various models."""

import re
from typing import Any

from pydantic import NonNegativeInt


def validate_regex(value: Any) -> Any:
    """Validate and compile a regular expression."""
    if isinstance(value, str):
        return re.compile(value.encode())
    return value  # pragma: no cover


def validate_count_tuple(
    value: tuple[NonNegativeInt | None, NonNegativeInt | None],
) -> tuple[NonNegativeInt | None, NonNegativeInt | None]:
    """Validate that min is larger than max in a count tuple."""
    count_min, count_max = value
    if count_min is not None and count_max is not None and count_min > count_max:
        raise ValueError(f"Minimum ({count_min}) is greater than maximum ({count_max}).")
    if count_min is None and count_max is None:
        raise ValueError("At least one of minimum or maximum must be specified.")
    return value
