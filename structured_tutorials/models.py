"""Basic tutorial structure."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from yaml import safe_load


class RunCommandSpecification(BaseModel):
    """Model specifying expected behavior when actually running a command."""

    status_code: int = 0


class CommandDocumentation(BaseModel):
    """Model specifying details for documentation."""

    output: str = ""


class CommandModel(BaseModel):
    """Model representing a command in a tutorial."""

    command: str
    run: RunCommandSpecification = RunCommandSpecification()
    doc: CommandDocumentation = CommandDocumentation()


class CommandsPartModel(BaseModel):
    """Model representing a part of the tutorial."""

    type: Literal["commands"] = "commands"
    commands: tuple[CommandModel, ...]


class TutorialModel(BaseModel):
    """Model representing a tutorial."""

    path: Path | None = None
    parts: tuple[CommandsPartModel, ...]

    @classmethod
    def from_file(cls, path: Path) -> "TutorialModel":
        """Load a tutorial from a YAML file."""
        with open(path) as stream:
            tutorial_data = safe_load(stream)
        tutorial_data["path"] = path
        tutorial = TutorialModel.model_validate(tutorial_data, context={"path": path})
        return tutorial
