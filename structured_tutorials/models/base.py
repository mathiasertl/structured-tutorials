# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Base model classes."""

from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat, NonNegativeInt
from pydantic.fields import FieldInfo

# Type for commands to execute
CommandType = str | tuple[str, ...]


class CommandBaseModel(BaseModel):
    """Base model for commands."""

    model_config = ConfigDict(extra="forbid")

    status_code: Annotated[int, Field(ge=0, le=255)] = 0
    show_output: bool = Field(
        default=True, description="Set to `False` to always hide the output of this command."
    )


class TestSpecificationMixin:
    """Mixin for specifying tests."""

    delay: Annotated[float, Field(ge=0)] = 0
    retry: NonNegativeInt = 0
    backoff_factor: NonNegativeFloat = 0  # {backoff factor} * (2 ** ({number of previous retries}))


class ConfigurationMixin:
    """Mixin for configuration models."""

    skip: bool = Field(default=False, description="Skip this part.")
    update_context: dict[str, Any] = Field(default_factory=dict)


def default_tutorial_root_factory(data: dict[str, Any]) -> Path:
    """Default factory for the tutorial_root variable."""
    tutorial_root = data["path"].parent
    assert isinstance(tutorial_root, Path)
    return tutorial_root


def template_field_title_generator(field_name: str, field_info: FieldInfo) -> str:
    """Field title generator for template fields."""
    return f"{field_name.title()} (template)"
