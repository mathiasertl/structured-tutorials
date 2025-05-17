"""Main models for loading tutorials."""

import shlex
from typing import Annotated, Any, Literal

from annotated_types import Ge, Le
from pydantic import BaseModel, BeforeValidator, Field


def none_as_dict(value: Any) -> Any:
    """Validate ``None`` as an empty ``dict``."""
    if value is None:
        return {}
    return value


def str_as_command(value: Any) -> Any:
    """Validate a ``str`` as an argument list."""
    if isinstance(value, str):
        return shlex.split(value)
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


class StepBase(BaseModel):
    """Base class for commands to run."""

    command: Annotated[tuple[str, ...], BeforeValidator(str_as_command)]
    returncode: Annotated[int, Ge(0), Le(255)] = 0


class Step(StepBase):
    """A step is a command in a part of a tutorial that you want to run."""

    sphinx: StepDocumentation = StepDocumentation()
    cleanup: tuple[StepBase, ...] = tuple()


class Part(BaseModel):
    """A part splits a tutorial into individual subsections."""

    commands: tuple[Annotated[Step, BeforeValidator(list_or_str_as_step)], ...]


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
    context: Contexts
    parts: tuple[Part, ...]
