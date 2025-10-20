"""Basic tutorial structure."""

from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator
from yaml import safe_load


class RunCommandSpecification(BaseModel):
    """Model specifying expected behavior when actually running a command."""

    status_code: int = 0
    update_context: dict[str, Any] = Field(default_factory=dict)


class CommandDocumentation(BaseModel):
    """Model specifying details for documentation."""

    output: str = ""
    update_context: dict[str, Any] = Field(default_factory=dict)


class CommandModel(BaseModel):
    """Model representing a command in a tutorial."""

    command: str
    run: RunCommandSpecification = RunCommandSpecification()
    doc: CommandDocumentation = CommandDocumentation()


class CommandsPartModel(BaseModel):
    """Model representing a part of the tutorial."""

    type: Literal["commands"] = "commands"
    commands: tuple[CommandModel, ...]


class RunConfiguration(BaseModel):
    """Model representing a tutorial configuration."""

    context: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def set_default_context(self) -> Self:
        self.context["doc"] = False
        self.context["run"] = True
        return self


class DocumentationConfiguration(BaseModel):
    """Model representing a tutorial configuration."""

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
    """Model representing a configuration model."""

    run: RunConfiguration = RunConfiguration()
    doc: DocumentationConfiguration = DocumentationConfiguration()


class TutorialModel(BaseModel):
    """Model representing a tutorial."""

    path: Path | None = None
    parts: tuple[CommandsPartModel, ...]
    configuration: ConfigurationModel = ConfigurationModel()

    @classmethod
    def from_file(cls, path: Path) -> "TutorialModel":
        """Load a tutorial from a YAML file."""
        with open(path) as stream:
            tutorial_data = safe_load(stream)
        tutorial_data["path"] = path
        tutorial = TutorialModel.model_validate(tutorial_data, context={"path": path})
        return tutorial
