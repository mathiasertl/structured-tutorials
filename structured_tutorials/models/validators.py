# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Validators for various models."""

import re
from typing import Any


def validate_regex(value: Any) -> Any:
    """Validate and compile a regular expression."""
    if isinstance(value, str):
        return re.compile(value.encode())
    return value  # pragma: no cover
