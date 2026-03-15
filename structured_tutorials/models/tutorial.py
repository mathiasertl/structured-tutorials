# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Module containing main tutorial model and global configuration models."""

from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Discriminator, Field, RootModel, Tag, model_validator
from pydantic_core.core_schema import ValidationInfo
from yaml import safe_load

from structured_tutorials.models.base import DictRootModelMixin
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
    required_executables: tuple[str, ...] = Field(default=tuple(), description="Required executables.")


class DocumentationAlternativesConfigurationModel(
    DictRootModelMixin[DocumentationAlternativeConfigurationModel],
    RootModel[dict[str, DocumentationAlternativeConfigurationModel]],
):
    """Configuration for alternatives when rendering documentation."""

    pass


class RuntimeAlternativesConfigurationModel(
    DictRootModelMixin[RuntimeAlternativeConfigurationModel],
    RootModel[dict[str, RuntimeAlternativeConfigurationModel]],
):
    """Configuration for alternatives at runtime."""

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


class RunnerConfig(BaseModel):
    """Configuration for the runner itself."""

    path: str = "structured_tutorials.runners.local.LocalTutorialRunner"
    options: dict[str, Any] = Field(default_factory=dict)


class RuntimeConfigurationModel(BaseModel):
    """Initial configuration for running the tutorial."""

    model_config = ConfigDict(extra="forbid", title="Runtime Configuration")

    runner: RunnerConfig = RunnerConfig()
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
    required_executables: tuple[str, ...] = Field(default=tuple(), description="Required executables.")

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

    root: Path = Field(
        json_schema_extra={"required": False},
        description="Directory from which relative file paths are resolved. Defaults to the path of the "
        "tutorial file.",
    )  # absolute path
    configuration: ConfigurationModel = Field(default=ConfigurationModel())
    parts: tuple[
        Annotated[
            PartModels
            | Annotated[PromptModel, Tag("prompt")]
            | Annotated[AlternativeModel, Tag("alternatives")],
            Discriminator(part_discriminator),
        ],
        ...,
    ] = Field(description="The individual parts of this tutorial.")

    @classmethod
    def model_json_schema(cls, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]  # pragma: no cover
        schema = super().model_json_schema(**kwargs)
        schema["required"].remove("root")
        return schema

    @model_validator(mode="after")
    def update_context(self, info: ValidationInfo) -> Self:
        if isinstance(info.context, dict):
            if path := info.context.get("path"):  # pragma: no branch
                assert isinstance(path, Path)
                self.configuration.run.context["tutorial_path"] = path
                self.configuration.run.context["tutorial_dir"] = path.parent
                self.configuration.doc.context["tutorial_path"] = path
                self.configuration.doc.context["tutorial_dir"] = path.parent

                if not self.root.is_absolute():
                    self.root = (path.parent / self.root).resolve()
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

        tutorial_data.setdefault("root", path.resolve().parent)
        tutorial = TutorialModel.model_validate(tutorial_data, context={"path": path})
        return tutorial
