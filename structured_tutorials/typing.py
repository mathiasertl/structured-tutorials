# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Module that re-exports some type hints."""

try:
    from typing import Self
except ImportError:  # pragma: no cover
    # Note: only for py3.10
    from typing_extensions import Self


__all__ = [
    "Self",
]
