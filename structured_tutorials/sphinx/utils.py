"""Utility functions for the sphinx extension."""

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

    def __init__(self, path: Path) -> None:
        self.tutorial = TutorialModel.from_file(path)
        self.next_part = 0
        self.env = Environment(keep_trailing_newline=True)
        self.context = {"execution": False, "documentation": True}

    def render_code_block(self, part: CommandsPartModel) -> str:
        """Render a CommandsPartModel as a code-block."""
        template = """.. code-block:: console
    {% for cmd in part.commands %}
    user@host:~# {{ cmd.command }}{% if cmd.doc.output %}
    {{ cmd.doc.output.rstrip('\n')|indent(4) }}{% endif %}
    {%- endfor %} 
        """
        return self.env.from_string(template).render({"part": part})

    def render_part(self) -> str:
        """Render the given part of the tutorial."""
        part = self.tutorial.parts[self.next_part]
        text = self.render_code_block(part)
        return text
