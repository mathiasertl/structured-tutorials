# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Module containing main tutorial model and global configuration models."""

from pathlib import Path
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Discriminator,
    Field,
    RootModel,
    Tag,
    field_validator,
    model_validator,
)
from pydantic_core.core_schema import ValidationInfo
from yaml import safe_load

from structured_tutorials.models.base import DictRootModelMixin, default_tutorial_root_factory
from structured_tutorials.models.parts import AlternativeModel, PartModels, PromptModel, part_discriminator
from structured_tutorials.typing import Self


class DocumentationAlternativeConfigurationModel(BaseModel):
    """Additional documentation configuration for alternatives."""

    model_config = ConfigDict(extra="forbid", title="Additional configuration for alternatives.")

    context: dict[str, Any] = Field(
        default_factory=dict, description="Key/value pairs for the initial context for an alternative."
    )
    name: str = Field(default="", description="Name of the alternative (used e.g. in tab titles).")


class RuntimeAlternativeConfigurationModel(BaseModel):
    """Additional runtime configuration for alternatives."""

    model_config = ConfigDict(extra="forbid", title="Additional configuration for alternatives.")

    context: dict[str, Any] = Field(
        default_factory=dict, description="Key/value pairs for the initial context for an alternative."
    )
    environment: dict[str, str | None] = Field(
        default_factory=dict, description="Additional environment variables for all commands."
    )


class DocumentationAlternativesConfigurationModel(
    DictRootModelMixin[DocumentationAlternativeConfigurationModel],
    RootModel[dict[str, DocumentationAlternativeConfigurationModel]],
):
    pass


class RuntimeAlternativesConfigurationModel(
    DictRootModelMixin[RuntimeAlternativeConfigurationModel],
    RootModel[dict[str, RuntimeAlternativeConfigurationModel]],
):
    pass


class DocumentationConfigurationModel(BaseModel):
    """Initial configuration for rendering the tutorial as documentation."""

    model_config = ConfigDict(extra="forbid", title="Documentation Configuration")

    context: dict[str, Any] = Field(
        default_factory=dict, description="Key/value pairs for the initial context when rendering templates."
    )
    alternatives: DocumentationAlternativesConfigurationModel = Field(
        default_factory=lambda: DocumentationAlternativesConfigurationModel({})
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


class RuntimeConfigurationModel(BaseModel):
    """Initial configuration for running the tutorial."""

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
    environment: dict[str, str | None] = Field(
        default_factory=dict,
        description="Additional environment variables for all commands."
        "Set a value to `None` to clear it from the global environment.",
    )
    clear_environment: bool = Field(default=False, description="Clear the environment for all commands.")
    alternatives: RuntimeAlternativesConfigurationModel = Field(
        default_factory=lambda: RuntimeAlternativesConfigurationModel({})
    )

    @model_validator(mode="after")
    def set_default_context(self) -> Self:
        self.context["doc"] = False
        self.context["run"] = True
        self.context["cwd"] = Path.cwd()
        return self


class ConfigurationModel(BaseModel):
    """Initial configuration of a tutorial."""

    model_config = ConfigDict(extra="forbid", title="Tutorial Configuration")

    run: RuntimeConfigurationModel = RuntimeConfigurationModel()
    doc: DocumentationConfigurationModel = DocumentationConfigurationModel()
    context: dict[str, Any] = Field(
        default_factory=dict, description="Initial context for both documentation and runtime."
    )


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
    parts: tuple[
        Annotated[
            PartModels
            | Annotated[PromptModel, Tag("prompt")]
            | Annotated[AlternativeModel, Tag("alternatives")],
            Discriminator(part_discriminator),
        ],
        ...,
    ] = Field(description="The individual parts of this tutorial.")
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

    @model_validator(mode="after")
    def update_part_data(self) -> Self:
        for part_no, part in enumerate(self.parts):
            part.index = part_no
            if not part.id:
                part.id = str(part_no)
        return self

    @classmethod
    def from_file(cls, path: Path) -> "TutorialModel":
        """Load a tutorial from a YAML file."""
        with open(path) as stream:
            tutorial_data = safe_load(stream)

        # e.g. an empty YAML file will return None
        if not isinstance(tutorial_data, dict):
            raise ValueError("File does not contain a mapping at top level.")

        tutorial_data["path"] = path.resolve()
        tutorial = TutorialModel.model_validate(tutorial_data, context={"path": path})
        return tutorial
