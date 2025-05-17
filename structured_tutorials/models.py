"""Main models for loading tutorials."""

import shlex
from typing import Annotated, Any, Literal, Self

from annotated_types import Ge, Le
from pydantic import BaseModel, BeforeValidator, Field, model_validator


def none_as_dict(value: Any) -> Any:
    """Validate ``None`` as an empty ``dict``."""
    if value is None:
        return {}
    return value


def list_or_str_as_step(value: Any) -> Any:
    """Validate an argument list or a string as simple command."""
    if isinstance(value, str):
        return {"command": shlex.split(value)}
    elif isinstance(value, list | tuple):
        return {"command": value}
    return value


class StepDocumentation(BaseModel):
    """Model for documentation configuration."""

    show_stdout: str = ""


class CommandBase(BaseModel):
    """Base class for commands to run."""

    command: tuple[str, ...] | str
    returncode: Annotated[int, Ge(0), Le(255)] = 0
    shell: bool = False

    @model_validator(mode="after")
    def validate_shell_command(self) -> Self:
        if self.shell is False and isinstance(self.command, str):
            self.command = tuple(shlex.split(self.command))
        elif self.shell is True and isinstance(self.command, tuple):
            self.command = shlex.join(self.command)

        return self


class Command(CommandBase):
    """A step is a command in a part of a tutorial that you want to run."""

    sphinx: StepDocumentation = StepDocumentation()
    cleanup: tuple[CommandBase, ...] = tuple()


class Part(BaseModel):
    """A part splits a tutorial into individual subsections."""

    commands: tuple[Annotated[Command, BeforeValidator(list_or_str_as_step)], ...]


class Config(BaseModel):
    """Global configuration for a tutorial."""

    type: Literal["local", "vagrant"] = "local"


class Contexts(BaseModel):
    """A set of contexts for running or rendering tutorials."""

    sphinx: Annotated[dict[str, Any], BeforeValidator(none_as_dict)] = Field(default_factory=dict)
    execution: Annotated[dict[str, Any], BeforeValidator(none_as_dict)] = Field(default_factory=dict)


class Tutorial(BaseModel):
    """Top-level model for tutorials."""

    config: Annotated[Config, BeforeValidator(none_as_dict)] = Field(default=Config())
    context: Contexts = Contexts()
    parts: tuple[Part, ...]
