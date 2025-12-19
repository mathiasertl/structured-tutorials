# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test specifications for commands."""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from structured_tutorials.models.base import CommandBaseModel, TestSpecificationMixin
from structured_tutorials.models.validators import validate_regex


class TestCommandModel(TestSpecificationMixin, CommandBaseModel):
    """Model for a test command for a normal command."""

    model_config = ConfigDict(extra="forbid")

    command: str


class TestPortModel(TestSpecificationMixin, BaseModel):
    """Model for testing connectivity after a command is run."""

    model_config = ConfigDict(extra="forbid")

    host: str
    port: Annotated[int, Field(ge=0, le=65535)]


class TestOutputModel(BaseModel):
    """Test the output of the command."""

    model_config = ConfigDict(extra="forbid")
    stream: Literal["stdout", "stderr"] = "stdout"
    regex: Annotated[re.Pattern[str], BeforeValidator(validate_regex)] = Field(
        description="A regular expression to test."
    )
