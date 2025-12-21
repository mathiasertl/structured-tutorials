# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Basic tutorial structure."""

import os
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, field_validator, model_validator

from structured_tutorials.models.base import (
    CommandBaseModel,
    CommandType,
    ConfigurationMixin,
    template_field_title_generator,
)
from structured_tutorials.models.tests import TestCommandModel, TestOutputModel, TestPortModel

TEMPLATE_DESCRIPTION = "This value is rendered as a template with the current context."


class CleanupCommandModel(CommandBaseModel):
    """Command to clean up artifacts created by the current part."""

    model_config = ConfigDict(extra="forbid")

    command: CommandType = Field(description="Command that cleans up artifacts created by the main command.")


class CommandRuntimeConfigurationModel(ConfigurationMixin, CommandBaseModel):
    """Model for runtime configuration when running a single command."""

    model_config = ConfigDict(extra="forbid")

    update_context: dict[str, Any] = Field(default_factory=dict)
    chdir: Path | None = Field(default=None, description="Change working directory to this path.")
    cleanup: tuple[CleanupCommandModel, ...] = tuple()
    test: tuple[TestCommandModel | TestPortModel | TestOutputModel, ...] = tuple()


class CommandDocumentationConfigurationModel(ConfigurationMixin, BaseModel):
    """Model for documenting a single command."""

    model_config = ConfigDict(extra="forbid")

    output: str = ""
    update_context: dict[str, Any] = Field(default_factory=dict)


class CommandModel(BaseModel):
    """A single command to run in this part."""

    model_config = ConfigDict(extra="forbid")

    command: CommandType = Field(description="The command to run.")
    run: CommandRuntimeConfigurationModel = Field(
        default=CommandRuntimeConfigurationModel(), description="The runtime configuration."
    )
    doc: CommandDocumentationConfigurationModel = Field(
        default=CommandDocumentationConfigurationModel(), description="The documentation configuration."
    )


class CommandsRuntimeConfigurationModel(ConfigurationMixin, BaseModel):
    """Runtime configuration for an entire commands part."""

    model_config = ConfigDict(extra="forbid")


class CommandsDocumentationConfigurationModel(ConfigurationMixin, BaseModel):
    """Documentation configuration for an entire commands part."""

    model_config = ConfigDict(extra="forbid")


class CommandsPartModel(BaseModel):
    """A tutorial part consisting of one or more commands."""

    model_config = ConfigDict(extra="forbid", title="Command part")

    type: Literal["commands"] = "commands"
    commands: tuple[CommandModel, ...]

    run: CommandsRuntimeConfigurationModel = CommandsRuntimeConfigurationModel()
    doc: CommandsDocumentationConfigurationModel = CommandsDocumentationConfigurationModel()


class FileRuntimeConfigurationModel(ConfigurationMixin, BaseModel):
    """Configure a file part when running the tutorial."""

    model_config = ConfigDict(extra="forbid", title="File part runtime configuration")


class FileDocumentationConfigurationModel(ConfigurationMixin, BaseModel):
    """Configure a file part when rendering it as documentation.

    For the `language`, `caption`, `linenos`, `lineno_start`, `emphasize_lines` and `name` options, please
    consult the [sphinx documentation](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-code-block).
    """

    model_config = ConfigDict(extra="forbid", title="File part documentation configuration")

    # sphinx options:
    language: str = Field(default="", description="The language used for the code block directive.")
    caption: str | Literal[False] = Field(
        default="",
        description=f"The caption. Defaults to the `destination` of this part. {TEMPLATE_DESCRIPTION}",
    )
    linenos: bool = False
    lineno_start: NonNegativeInt | Literal[False] = False
    emphasize_lines: str = ""
    name: str = ""
    ignore_spelling: bool = Field(
        default=False,
        description="If true, wrap the caption in `:spelling:ignore:` (see"
        " [sphinxcontrib.spelling](https://sphinxcontrib-spelling.readthedocs.io/en/latest/)).",
    )


class FilePartModel(BaseModel):
    """A tutorial part for creating a file.

    Note that exactly one of `contents` or `source` is required.
    """

    model_config = ConfigDict(extra="forbid", title="File part")

    type: Literal["file"] = "file"
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
    destination: str = Field(
        field_title_generator=template_field_title_generator,
        description=f"The destination path of the file. {TEMPLATE_DESCRIPTION}",
    )
    template: bool = Field(
        default=True, description="Whether the file contents should be rendered in a template."
    )

    doc: FileDocumentationConfigurationModel = FileDocumentationConfigurationModel()
    run: FileRuntimeConfigurationModel = FileRuntimeConfigurationModel()

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

    @model_validator(mode="after")
    def validate_destination(self) -> Self:
        if not self.source and self.destination.endswith(os.sep):
            raise ValueError(f"{self.destination}: Destination must not be a directory if contents is given.")
        return self


class PromptModel(BaseModel):
    """Allows you to inspect the current state of the tutorial manually."""

    model_config = ConfigDict(extra="forbid", title="Prompt Configuration")
    prompt: str = Field(description=f"The prompt text. {TEMPLATE_DESCRIPTION}")
    type: Literal["enter", "confirm"] = "enter"
    default: bool = Field(
        default=True, description="For type=`confirm`, the default if the user just presses enter."
    )
    error: str = Field(
        default="State was not confirmed.",
        description="For `type=confirm`, the error message if the user does not confirm the current state. "
        "{TEMPLATE_DESCRIPTION} The context will also include the `response` variable, representing the user "
        "response.",
    )


PartModels = CommandsPartModel | FilePartModel


class AlternativeRuntimeConfigurationModel(ConfigurationMixin, BaseModel):
    """Configure an alternative part when running the tutorial."""

    model_config = ConfigDict(extra="forbid", title="File part runtime configuration")


class AlternativeDocumentationConfigurationModel(ConfigurationMixin, BaseModel):
    """Configure an alternative part when documenting the tutorial."""

    model_config = ConfigDict(extra="forbid", title="File part runtime configuration")


class AlternativeModel(BaseModel):
    """A tutorial part that has several different alternatives.

    When rendering documentation, alternatives are rendered in tabs. When running a tutorial, the runner has
    to specify exactly one (or at most one, if `required=False`) of the alternatives that should be run.

    An alternative can contain parts for files or commands.
    """

    model_config = ConfigDict(extra="forbid", title="Alternatives")

    alternatives: dict[str, PartModels]
    required: bool = Field(default=True, description="Whether one of the alternatives is required.")
    doc: AlternativeDocumentationConfigurationModel = AlternativeDocumentationConfigurationModel()
    run: AlternativeRuntimeConfigurationModel = AlternativeRuntimeConfigurationModel()
