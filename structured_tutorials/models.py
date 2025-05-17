import shlex
from typing import Annotated, Any, Literal

from annotated_types import Ge, Le
from pydantic import BaseModel, BeforeValidator, Field, RootModel


def none_as_dict(value: Any) -> Any:
    if value is None:
        return {}
    return value


def str_as_command(value: Any) -> Any:
    if isinstance(value, str):
        return shlex.split(value)
    return value


def list_or_str_as_step(value: Any) -> Any:
    if isinstance(value, str):
        return {"command": shlex.split(value)}
    elif isinstance(value, list | tuple):
        return {"command": value}
    return value


class StepDocumentation(BaseModel):
    show_stdout: str = ""


class StepBase(BaseModel):
    command: Annotated[tuple[str, ...], BeforeValidator(str_as_command)]
    returncode: Annotated[int, Ge(0), Le(255)] = 0


class Step(StepBase):
    documentation: StepDocumentation = StepDocumentation()
    cleanup: tuple[StepBase, ...] = tuple()


class Part(BaseModel):
    commands: tuple[Annotated[Step, BeforeValidator(list_or_str_as_step)], ...]


class Config(BaseModel):
    type: Literal["local", "vagrant"] = "local"


class Contexts(BaseModel):
    documentation: Annotated[dict[str, Any], BeforeValidator(none_as_dict)] = Field(default_factory=dict)
    execution: Annotated[dict[str, Any], BeforeValidator(none_as_dict)] = Field(default_factory=dict)


class Tutorial(BaseModel):
    config: Annotated[Config, BeforeValidator(none_as_dict)] = Field(default=Config())
    context: Contexts
    parts: tuple[Part, ...]
