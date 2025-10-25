"""Utility functions for the sphinx extension."""

from copy import deepcopy
from pathlib import Path

from jinja2 import Environment
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.errors import ConfigError, ExtensionError

from structured_tutorials.models import CommandsPartModel, FilePartModel, TutorialModel


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

    def render(self, template: str) -> str:
        return self.env.from_string(template).render(self.context)

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

    def render_file(self, part: FilePartModel) -> str:
        if part.template is False:
            return ""

        template = part.contents
        if template is None:
            with open(part.path) as stream:
                template = stream.read()

        content = self.render(template)

        # get options
        if part.doc.caption:
            caption = self.render(part.doc.caption)
        elif part.doc.caption is not False:
            caption = self.render(str(part.destination))
        else:
            caption = ""

        directive = """.. code-block:: {{ part.doc.language }}{% if caption %}
    :caption: {{ caption }}{% endif %}{% if part.doc.linenos or part.doc.lineno_start %}
    :linenos:{% endif %}{% if part.doc.lineno_start %}
    :lineno-start: {{ part.doc.lineno_start }}{% endif %}{% if part.doc.emphasize_lines %}
    :emphasize-lines: {{ part.doc.emphasize_lines }}{% endif %}{% if part.doc.name %}
    :name: {{ part.doc.name }}{% endif %}

    {{ content }}
"""
        return self.env.from_string(directive).render({"part": part, "content": content, "caption": caption})

    def render_part(self) -> str:
        """Render the given part of the tutorial."""
        part = self.tutorial.parts[self.next_part]
        if isinstance(part, CommandsPartModel):
            text = self.render_code_block(part)
        elif isinstance(part, FilePartModel):
            text = self.render_file(part)
        else:  # pragma: no cover
            raise ValueError("unsupported part type.")
        self.next_part += 1
        return text
