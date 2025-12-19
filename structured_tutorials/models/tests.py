# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test specifications for commands."""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from structured_tutorials.models.base import CommandBaseModel, CommandType, TestSpecificationMixin
from structured_tutorials.models.validators import validate_regex


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
    regex: Annotated[re.Pattern[str], BeforeValidator(validate_regex)] = Field(
        description="A regular expression to test."
    )
