"""Sphinx extension."""

from pathlib import Path

from docutils.nodes import Body, Node, paragraph
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.errors import ConfigError, ExtensionError, SphinxError
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import ExtensionMetadata

from structured_tutorials import version
from structured_tutorials.models import Commands, File, Tutorial
from structured_tutorials.tutorial import load_tutorial

_NEXT_PART = "tutorial-next-part"

LAST_PART = "__end__"


class TutorialDirective(SphinxDirective):
    """Directive to specify the currently rendered tutorial."""

    has_content = False
    required_arguments = 1
    optional_arguments = 0

    def get_tutorial_path(self, tutorial: str) -> str:
        root: Path = self.config.tutorial_root
        tutorial_path = Path(tutorial)
        if tutorial_path.is_absolute():
            raise ExtensionError(f"{tutorial}: Path must not be absolute.")
        absolute_path = root / tutorial_path
        if not absolute_path.exists():
            raise ExtensionError(f"{absolute_path}: File not found.")
        return absolute_path

    def run(self) -> list[Node]:
        tutorial = self.arguments[0].strip()

        tutorial_path = self.get_tutorial_path(tutorial)
        tutorial = load_tutorial(tutorial_path)
        self.env.current_document["tutorial"] = tutorial
        self.env.current_document["tutorial-next-part"] = tutorial.parts[0].id  # next part to be rendered
        # NOTE: `highlighting` directive returns a custom Element for unknown reasons
        return []


class PartDirective(SphinxDirective):
    """Directive to show a tutorial part."""

    required_arguments = 0
    optional_arguments = 1  # Next part to display

    def render_commands(self, commands: Commands) -> str:
        return f"""
.. code-block:: console

    user@host:~# ls
    Command: {commands}
"""

    def render_file(self, file: File) -> str:
        return f"""
.. code-block:: console

    {file}
"""

    def run(self) -> list[paragraph]:
        node = paragraph()

        tutorial: Tutorial = self.env.current_document["tutorial"]
        if self.arguments:
            next_part_id: str = self.arguments[0].strip()
        else:
            next_part_id = self.env.current_document[_NEXT_PART]
            if next_part_id == LAST_PART:
                raise SphinxError("Part without id found, but last part was already rendered.")

        part_rendered = False
        for index, part in enumerate(tutorial.parts):
            if part.id == next_part_id:  # Found the part we want to render
                part_rendered = True
                if isinstance(part, Commands):
                    text = self.render_commands(part)
                else:
                    text = self.render_file(part)

                if len(tutorial.parts) <= index + 1:
                    self.env.current_document[_NEXT_PART] = LAST_PART
                else:
                    self.env.current_document[_NEXT_PART] = tutorial.parts[index + 1].id

                break  # no longer need to loop

        if part_rendered is False:
            raise ExtensionError(f"{next_part_id}: Part not found.")

        lines = StringList(text.splitlines())
        state: Body = self.state
        state.nested_parse(lines, 0, node)
        return [node]


def validate_configuration(app: Sphinx, config: Config) -> None:
    """Validate configuration directives, so that we can rely on values later."""
    root = config.tutorial_root
    if not isinstance(root, Path):
        raise ConfigError(f"{root}: Must be of type Path.")
    if not root.is_absolute():
        raise ConfigError(f"{root}: Path must be absolute.")


def setup(app: Sphinx) -> ExtensionMetadata:
    """Sphinx setup function."""
    # Add dependency on other extension:
    # app.setup_extension("sphinx.ext.autodoc")
    app.connect("config-inited", validate_configuration)
    app.add_config_value("tutorial_root", Path(app.srcdir), "env", types=[Path])

    app.add_directive("tutorial", TutorialDirective)
    app.add_directive("part", PartDirective)

    # return metadata
    return {
        "version": version,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
