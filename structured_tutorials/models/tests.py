# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test specifications for commands."""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from structured_tutorials.models.base import CommandBaseModel, CommandType, TestSpecificationMixin
from structured_tutorials.models.validators import validate_regex
from structured_tutorials.typing import COUNT_TYPE, Self


class TestCommandModel(TestSpecificationMixin, CommandBaseModel):
    """Test a command by running another command."""

    model_config = ConfigDict(extra="forbid")

    command: CommandType = Field(description="The command to run.")


class TestPortModel(TestSpecificationMixin, BaseModel):
    """Test a command by checking if a port is open."""

    model_config = ConfigDict(extra="forbid")

    host: str = Field(description="The host to connect to.")
    port: Annotated[int, Field(ge=0, le=65535)] = Field(description="The port to connect to.")


class TestOutputModel(BaseModel):
    """Test a command by checking the output of a command."""

    model_config = ConfigDict(extra="forbid")

    stream: Literal["stdout", "stderr"] = Field(default="stdout", description="The output stream to use.")
    regex: Annotated[re.Pattern[bytes], BeforeValidator(validate_regex)] | None = Field(
        default=None, description="A regular expression to test."
    )
    line_count: COUNT_TYPE = Field(default=None, description="Test for the given line count.")
    character_count: COUNT_TYPE = Field(default=None, description="Test for the given character count.")

    @model_validator(mode="after")
    def validate_tests(self) -> Self:
        if not self.regex and not self.line_count and not self.character_count:
            raise ValueError("At least one test must be specified.")
        return self
