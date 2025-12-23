# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Module that re-exports some type hints."""

from typing import Annotated

from pydantic import AfterValidator, NonNegativeInt

from structured_tutorials.models.validators import validate_count_tuple

try:
    from typing import Self
except ImportError:  # pragma: no cover
    # Note: only for py3.10
    from typing_extensions import Self

COUNT_TUPLE = Annotated[
    tuple[NonNegativeInt | None, NonNegativeInt | None], AfterValidator(validate_count_tuple)
]
COUNT_TYPE = NonNegativeInt | COUNT_TUPLE | None

__all__ = [
    "COUNT_TYPE",
    "Self",
]
