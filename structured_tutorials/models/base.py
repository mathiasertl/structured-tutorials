# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Base model classes."""

from pathlib import Path
from typing import Annotated, Any, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeFloat,
    NonNegativeInt,
    field_validator,
    model_validator,
)
from pydantic.fields import FieldInfo

# Type for commands to execute
CommandType = str | tuple[str, ...]

TEMPLATE_DESCRIPTION = "This value is rendered as a template with the current context."


def default_tutorial_root_factory(data: dict[str, Any]) -> Path:
    """Default factory for the tutorial_root variable."""
    tutorial_root = data["path"].parent
    assert isinstance(tutorial_root, Path)
    return tutorial_root


def template_field_title_generator(field_name: str, field_info: FieldInfo) -> str:
    """Field title generator for template fields."""
    return f"{field_name.title()} (template)"


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


class FileMixin:
    """Mixin for specifying a file (used in file part and for stdin of commands)."""

    contents: str | None = Field(
        default=None,
        field_title_generator=template_field_title_generator,
        description=f"Contents of the file. {TEMPLATE_DESCRIPTION}",
    )
    source: Path | None = Field(
        default=None,
        field_title_generator=template_field_title_generator,
        description="The source path of the file to create. Unless `template` is `False`, the file is loaded "
        "into memory and rendered as template.",
    )
    template: bool = Field(
        default=True, description="Whether the file contents should be rendered in a template."
    )

    @field_validator("source", mode="after")
    @classmethod
    def validate_source(cls, value: Path) -> Path:
        if value.is_absolute():
            raise ValueError(f"{value}: Must be a relative path (relative to the current cwd).")
        return value

    @model_validator(mode="after")
    def validate_contents_or_source(self) -> Self:
        if self.contents is None and self.source is None:
            raise ValueError("Either contents or source is required.")
        if self.contents is not None and self.source is not None:
            raise ValueError("Only one of contents or source is allowed.")
        return self
