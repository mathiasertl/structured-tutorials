# Copyright (c) 2026 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Pydantic types used in this project."""

from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator

from structured_tutorials.models.validators import validate_relative_path

RelativePath = Annotated[Path, AfterValidator(validate_relative_path)]
