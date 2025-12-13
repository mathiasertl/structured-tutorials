# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Basic tutorial structure."""

import os
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.fields import FieldInfo
from pydantic_core.core_schema import ValidationInfo
from yaml import safe_load

PositiveInt = Annotated[int, Field(ge=0)]
PositiveFloat = Annotated[float, Field(ge=0)]

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


class TestSpecificationMixin:
    """Mixin for specifying tests."""

    delay: Annotated[float, Field(ge=0)] = 0
    retry: PositiveInt = 0
    backoff_factor: PositiveFloat = 0  # {backoff factor} * (2 ** ({number of previous retries}))


class ConfigurationMixin:
    """Mixin for configuration models."""

    skip: bool = Field(default=False, description="Skip this part.")


class CleanupCommandModel(CommandBaseModel):
    """Model for cleanup commands."""

    model_config = ConfigDict(extra="forbid")

    command: str


class TestCommandModel(TestSpecificationMixin, CommandBaseModel):
    """Model for a test command for a normal command."""

    model_config = ConfigDict(extra="forbid")

    command: str


class TestPortModel(TestSpecificationMixin, BaseModel):
    """Model for testing connectivity after a command is run."""

    model_config = ConfigDict(extra="forbid")

    host: str
    port: Annotated[int, Field(ge=0, le=65535)]


class CommandRuntimeConfigurationModel(ConfigurationMixin, CommandBaseModel):
    """Model for runtime configuration when running a single command."""

    model_config = ConfigDict(extra="forbid")

    update_context: dict[str, Any] = Field(default_factory=dict)
    cleanup: tuple[CleanupCommandModel, ...] = tuple()
    test: tuple[TestCommandModel | TestPortModel, ...] = tuple()


class CommandDocumentationConfigurationModel(ConfigurationMixin, BaseModel):
    """Model for documenting a single command."""

    model_config = ConfigDict(extra="forbid")

    output: str = ""
    update_context: dict[str, Any] = Field(default_factory=dict)


class CommandModel(BaseModel):
    """Model for a single command."""

    model_config = ConfigDict(extra="forbid")

    command: str
    run: CommandRuntimeConfigurationModel = CommandRuntimeConfigurationModel()
    doc: CommandDocumentationConfigurationModel = CommandDocumentationConfigurationModel()


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
    lineno_start: PositiveInt | Literal[False] = False
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


class RuntimeConfigurationModel(BaseModel):
    """Initital configuration for running the tutorial."""

    model_config = ConfigDict(extra="forbid", title="Runtime Configuration")

    context: dict[str, Any] = Field(
        default_factory=dict, description="Key/value pairs for the initial context when rendering templates."
    )
    temporary_directory: bool = Field(
        default=False, description="Switch to an empty temporary directory before running the tutorial."
    )
    git_export: bool = Field(
        default=False,
        description="Export a git archive to a temporary directory before running the tutorial.",
    )

    @model_validator(mode="after")
    def set_default_context(self) -> Self:
        self.context["doc"] = False
        self.context["run"] = True
        self.context["cwd"] = Path.cwd()
        return self


class DocumentationConfigurationModel(BaseModel):
    """Initial configuration for rendering the tutorial as documentation."""

    model_config = ConfigDict(extra="forbid", title="Documentation Configuration")

    context: dict[str, Any] = Field(
        default_factory=dict, description="Key/value pairs for the initial context when rendering templates."
    )

    @model_validator(mode="after")
    def set_default_context(self) -> Self:
        self.context["run"] = False
        self.context["doc"] = True
        self.context.setdefault("user", "user")
        self.context.setdefault("host", "host")
        self.context.setdefault("cwd", "~")
        self.context.setdefault(
            "prompt_template",
            "{{ user }}@{{ host }}:{{ cwd }}{% if user == 'root' %}#{% else %}${% endif %} ",
        )
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


class ConfigurationModel(BaseModel):
    """Initial configuration of a tutorial."""

    model_config = ConfigDict(extra="forbid", title="Tutorial Configuration")

    run: RuntimeConfigurationModel = RuntimeConfigurationModel()
    doc: DocumentationConfigurationModel = DocumentationConfigurationModel()


class TutorialModel(BaseModel):
    """Root structure for the entire tutorial."""

    model_config = ConfigDict(extra="forbid", title="Tutorial")

    # absolute path to YAML file
    path: Path = Field(
        description="Absolute path to the tutorial file. This field is populated automatically while loading the tutorial.",  # noqa: E501
    )
    tutorial_root: Path = Field(
        default_factory=default_tutorial_root_factory,
        description="Directory from which relative file paths are resolved. Defaults to the path of the "
        "tutorial file.",
    )  # absolute path (input: relative to path)
    parts: tuple[CommandsPartModel | FilePartModel | PromptModel, ...] = Field(
        description="The individual parts of this tutorial."
    )
    configuration: ConfigurationModel = Field(default=ConfigurationModel())

    @field_validator("path", mode="after")
    @classmethod
    def validate_path(cls, value: Path, info: ValidationInfo) -> Path:
        if not value.is_absolute():
            raise ValueError(f"{value}: Must be an absolute path.")
        return value

    @field_validator("tutorial_root", mode="after")
    @classmethod
    def resolve_tutorial_root(cls, value: Path, info: ValidationInfo) -> Path:
        if value.is_absolute():
            raise ValueError(f"{value}: Must be a relative path (relative to the tutorial file).")
        path: Path = info.data["path"]

        return (path.parent / value).resolve()

    @model_validator(mode="after")
    def update_context(self) -> Self:
        self.configuration.run.context["tutorial_path"] = self.path
        self.configuration.run.context["tutorial_dir"] = self.path.parent
        self.configuration.doc.context["tutorial_path"] = self.path
        self.configuration.doc.context["tutorial_dir"] = self.path.parent
        return self

    @classmethod
    def from_file(cls, path: Path) -> "TutorialModel":
        """Load a tutorial from a YAML file."""
        with open(path) as stream:
            tutorial_data = safe_load(stream)
        tutorial_data["path"] = path.resolve()
        tutorial = TutorialModel.model_validate(tutorial_data, context={"path": path})
        return tutorial
