"""Basic tutorial structure."""

from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_core.core_schema import ValidationInfo
from yaml import safe_load


def default_cwd_factory(data: dict[str, Any]) -> Path:
    """Default factory for the path variable."""
    return data["path"].parent  # type: ignore[no-any-return]


class CommandBaseModel(BaseModel):
    """Base model for commands."""

    status_code: int = 0


class TestSpecificationMixin:
    """Mixin for specifying tests."""

    delay: int = 0
    retry: int = 0
    backoff_factor: float = 0  # {backoff factor} * (2 ** ({number of previous retries}))


class CleanupCommandModel(CommandBaseModel):
    """Model for cleanup commands."""

    command: str


class TestCommandModel(TestSpecificationMixin, CommandBaseModel):
    """Model for a test command for a normal command.."""

    command: str


class TestPortModel(TestSpecificationMixin, BaseModel):
    """Model for testing connectivity after a command is run."""

    host: str
    port: int


class CommandRuntimeConfigurationModel(CommandBaseModel):
    """Model for runtime configuration when running a single command."""

    update_context: dict[str, Any] = Field(default_factory=dict)
    cleanup: tuple[CleanupCommandModel, ...] = tuple()
    test: tuple[TestCommandModel | TestPortModel, ...] = tuple()


class CommandDocumentationConfigurationModel(BaseModel):
    """Model for documenting a single command."""

    output: str = ""
    update_context: dict[str, Any] = Field(default_factory=dict)


class CommandModel(BaseModel):
    """Model for a single command."""

    command: str
    run: CommandRuntimeConfigurationModel = CommandRuntimeConfigurationModel()
    doc: CommandDocumentationConfigurationModel = CommandDocumentationConfigurationModel()


class CommandsPartModel(BaseModel):
    """Model for a set of commands."""

    type: Literal["commands"] = "commands"
    commands: tuple[CommandModel, ...]


class FilePartModel(BaseModel):
    """Model for a file to be copied."""

    type: Literal["file"] = "file"
    contents: str | None = None
    source: Path | None = None
    destination: Path
    template: bool = True

    @model_validator(mode="after")
    def validate_contents_or_source(self) -> Self:
        if self.contents is None and self.source is None:
            raise ValueError("Either contents or source is required.")
        return self


class RuntimeConfigurationModel(BaseModel):
    """Model for configuration at runtime."""

    context: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def set_default_context(self) -> Self:
        self.context["doc"] = False
        self.context["run"] = True
        return self


class DocumentationConfigurationModel(BaseModel):
    """Model for configuration of the documentation."""

    context: dict[str, Any] = Field(default_factory=dict)

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


class ConfigurationModel(BaseModel):
    """Model for the initial configuration of a tutorial."""

    run: RuntimeConfigurationModel = RuntimeConfigurationModel()
    doc: DocumentationConfigurationModel = DocumentationConfigurationModel()


class TutorialModel(BaseModel):
    """Model representing the entire tutorial."""

    path: Path  # absolute path
    cwd: Path = Field(default_factory=default_cwd_factory)  # absolute path (input: relative to path)
    parts: tuple[CommandsPartModel | FilePartModel, ...]
    configuration: ConfigurationModel = ConfigurationModel()

    @field_validator("path", mode="after")
    @classmethod
    def resolve_path(cls, value: Path, info: ValidationInfo) -> Path:
        if not value.is_absolute():
            raise ValueError(f"{value}: Must be an absolute path.")
        return value

    @field_validator("cwd", mode="after")
    @classmethod
    def resolve_cwd(cls, value: Path, info: ValidationInfo) -> Path:
        if value.is_absolute():
            raise ValueError(f"{value}: Must be a relative path (relative to the tutorial file).")
        path: Path = info.data["path"]

        return (path.parent / value).resolve()

    @classmethod
    def from_file(cls, path: Path) -> "TutorialModel":
        """Load a tutorial from a YAML file."""
        with open(path) as stream:
            tutorial_data = safe_load(stream)
        tutorial_data["path"] = path.resolve()
        tutorial = TutorialModel.model_validate(tutorial_data, context={"path": path})
        return tutorial
