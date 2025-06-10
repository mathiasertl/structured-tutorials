"""Main models for loading tutorials."""

from pathlib import Path
from typing import Annotated, Any, Literal, Self

from annotated_types import Ge, Le
from pydantic import BaseModel, BeforeValidator, Field, model_validator
from pydantic_core.core_schema import ValidationInfo


def none_as_dict(value: Any) -> Any:
    """Validate ``None`` as an empty ``dict``."""
    if value is None:
        return {}
    return value


def list_or_str_as_step(value: Any) -> Any:
    """Validate an argument list or a string as simple command."""
    if isinstance(value, str | list | tuple):
        return {"command": value}
    return value


class CommandDocumentation(BaseModel):
    """Model for documentation configuration."""

    output: str = ""
    update_context: dict[str, Any] = Field(default_factory=dict)


class CommandBase(BaseModel):
    """Base class for commands to run.

    The `command` specifies the command to run. It can be either a list of strings or a simple string. When
    running a tutorial locally, using a string implies passing ``shell=True`` to ``subprocess.run()``, but
    the exact semantics may differ with other runners.

    The `returncode` specifies the expected return code of the command and defaults to ``0``. If ``None`` is
    specified, the returncode is ignored when running the tutorial.
    """

    command: tuple[str, ...] | str
    returncode: Annotated[int, Ge(0), Le(255)] | None = 0


class Command(CommandBase):
    """A command in a part of a tutorial that you want to run."""

    id: str = ""
    exec_command: tuple[str, ...] | str | None = None
    documentation: CommandDocumentation = CommandDocumentation()
    cleanup: tuple[CommandBase, ...] = tuple()


class File(BaseModel):
    """A file you want to create at the given destination."""

    id: str = ""
    source: Path
    destination: Path
    template: bool = True  # False for big files


class Commands(BaseModel):
    """A part splits a tutorial into individual subsections."""

    id: str = ""
    commands: tuple[Annotated[Command, BeforeValidator(list_or_str_as_step)], ...]

    @model_validator(mode="after")
    def populate_ids(self) -> Self:
        for id, step in enumerate(self.commands):
            if step.id == "":
                step.id = str(id)
        return self


class Config(BaseModel):
    """Global configuration for a tutorial."""

    type: Literal["local", "vagrant"] = "local"
    working_directory: Path = Path.cwd()


class Contexts(BaseModel):
    """A set of contexts for running or rendering tutorials."""

    documentation: Annotated[dict[str, Any], BeforeValidator(none_as_dict)] = Field(
        default_factory=lambda: {"user": "user", "host": "host", "cwd": "~"}
    )
    execution: Annotated[dict[str, Any], BeforeValidator(none_as_dict)] = Field(default_factory=dict)


class Tutorial(BaseModel):
    """Top-level model for tutorials."""

    config: Annotated[Config, BeforeValidator(none_as_dict)] = Field(default=Config())
    context: Contexts = Contexts()
    parts: tuple[Commands | File, ...]

    @model_validator(mode="after")
    def validate_working_directory(self, info: ValidationInfo) -> Self:
        if isinstance(info.context, dict):
            if (path := info.context.get("path")) and not self.config.working_directory.is_absolute():
                self.config.working_directory = (path.parent / self.config.working_directory).resolve()

        for part in self.parts:
            if isinstance(part, File) and not part.source.is_absolute():
                part.source = self.config.working_directory / part.source

        return self

    @model_validator(mode="after")
    def update_default_documentation_context(self) -> Self:
        self.context.documentation.setdefault("user", "user")
        self.context.documentation.setdefault("host", "host")
        self.context.documentation.setdefault("cwd", "cwd")
        return self

    @model_validator(mode="after")
    def populate_ids(self) -> Self:
        for id, part in enumerate(self.parts):
            if part.id == "":
                part.id = str(id)
        return self
