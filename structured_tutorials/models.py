"""Basic tutorial structure."""

from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core.core_schema import ValidationInfo
from yaml import safe_load

PositiveInt = Annotated[int, Field(ge=0)]
PositiveFloat = Annotated[float, Field(ge=0)]


def default_cwd_factory(data: dict[str, Any]) -> Path:
    """Default factory for the path variable."""
    return data["path"].parent  # type: ignore[no-any-return]


class CommandBaseModel(BaseModel):
    """Base model for commands."""

    model_config = ConfigDict(extra="forbid")

    status_code: Annotated[int, Field(ge=0, le=255)] = 0


class TestSpecificationMixin:
    """Mixin for specifying tests."""

    model_config = ConfigDict(extra="forbid")

    delay: Annotated[float, Field(ge=0)] = 0
    retry: PositiveInt = 0
    backoff_factor: PositiveFloat = 0  # {backoff factor} * (2 ** ({number of previous retries}))


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


class CommandRuntimeConfigurationModel(CommandBaseModel):
    """Model for runtime configuration when running a single command."""

    model_config = ConfigDict(extra="forbid")

    update_context: dict[str, Any] = Field(default_factory=dict)
    cleanup: tuple[CleanupCommandModel, ...] = tuple()
    test: tuple[TestCommandModel | TestPortModel, ...] = tuple()


class CommandDocumentationConfigurationModel(BaseModel):
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


class CommandsPartModel(BaseModel):
    """Model for a set of commands."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["commands"] = "commands"
    commands: tuple[CommandModel, ...]


class FileDocumentationConfigurationModel(BaseModel):
    # sphinx options:
    language: str = ""
    caption: str | Literal[False] = ""
    linenos: bool = False
    lineno_start: PositiveInt | Literal[False] = False
    emphasize_lines: str = ""
    name: str = ""


class FilePartModel(BaseModel):
    """Model for a file to be copied."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["file"] = "file"
    contents: str | None = None
    source: Path | None = None
    destination: Path
    template: bool = True

    doc: FileDocumentationConfigurationModel = FileDocumentationConfigurationModel()

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


class RuntimeConfigurationModel(BaseModel):
    """Model for configuration at runtime."""

    model_config = ConfigDict(extra="forbid")

    context: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def set_default_context(self) -> Self:
        self.context["doc"] = False
        self.context["run"] = True
        return self


class DocumentationConfigurationModel(BaseModel):
    """Model for configuration of the documentation."""

    model_config = ConfigDict(extra="forbid")

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

    model_config = ConfigDict(extra="forbid")

    run: RuntimeConfigurationModel = RuntimeConfigurationModel()
    doc: DocumentationConfigurationModel = DocumentationConfigurationModel()


class TutorialModel(BaseModel):
    """Model representing the entire tutorial."""

    model_config = ConfigDict(extra="forbid")

    path: Path  # absolute path
    cwd: Path = Field(default_factory=default_cwd_factory)  # absolute path (input: relative to path)
    parts: tuple[CommandsPartModel | FilePartModel, ...]
    configuration: ConfigurationModel = ConfigurationModel()

    @field_validator("path", mode="after")
    @classmethod
    def validate_path(cls, value: Path, info: ValidationInfo) -> Path:
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
