"""Utility functions for the sphinx extension."""

from copy import deepcopy
from pathlib import Path

from jinja2 import Environment
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.errors import ConfigError, ExtensionError

from structured_tutorials.models import CommandsPartModel, TutorialModel


def validate_configuration(app: Sphinx, config: Config) -> None:
    """Validate configuration directives, so that we can rely on values later."""
    root = config.tutorial_root
    if not isinstance(root, Path):
        raise ConfigError(f"{root}: Must be of type Path.")
    if not root.is_absolute():
        raise ConfigError(f"{root}: Path must be absolute.")


def get_tutorial_path(tutorial_root: Path, arg: str) -> Path:
    """Get the full tutorial path and verify existence."""
    tutorial_path = Path(arg)
    if tutorial_path.is_absolute():
        raise ExtensionError(f"{tutorial_path}: Path must not be absolute.")

    absolute_path = tutorial_root / tutorial_path
    if not absolute_path.exists():
        raise ExtensionError(f"{absolute_path}: File not found.")
    return absolute_path


class TutorialWrapper:
    """Wrapper class for rendering a tutorial.

    This class exists mainly to wrap the main logic into a separate class that is more easily testable.
    """

    def __init__(self, tutorial: TutorialModel) -> None:
        self.tutorial = tutorial
        self.next_part = 0
        self.env = Environment(keep_trailing_newline=True)
        self.context = deepcopy(tutorial.configuration.doc.context)

    @classmethod
    def from_file(cls, path: Path) -> "TutorialWrapper":
        """Factory method for creating a TutorialWrapper from a file."""
        tutorial = TutorialModel.from_file(path)
        return cls(tutorial)

    def render_code_block(self, part: CommandsPartModel) -> str:
        """Render a CommandsPartModel as a code-block."""
        commands = []
        for command_config in part.commands:
            # Render the prompt
            prompt = self.env.from_string(self.context["prompt_template"]).render(self.context)

            # Render the command
            command = self.env.from_string(command_config.command).render(self.context)

            # Render output
            output_template = command_config.doc.output.rstrip("\n")
            output = self.env.from_string(output_template).render(self.context)

            # Finally, render the command
            command_template = """{{ prompt }}{{ command }}{% if output %}
{{ output }}{% endif %}"""
            command_context = {"prompt": prompt, "command": command, "output": output}
            rendered_command = self.env.from_string(command_template).render(command_context)
            commands.append(rendered_command)

            # Update the context from update_context
            self.context.update(command_config.doc.update_context)

        template = """.. code-block:: console

{% for cmd in commands %}{{ cmd|indent(4, first=True) }}
{% endfor %}"""
        return self.env.from_string(template).render({"commands": commands})

    def render_part(self) -> str:
        """Render the given part of the tutorial."""
        part = self.tutorial.parts[self.next_part]
        if isinstance(part, CommandsPartModel):
            text = self.render_code_block(part)
        else:  # pragma: no cover
            raise ValueError("unsupported part type.")
        return text
