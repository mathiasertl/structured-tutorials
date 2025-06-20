"""Sphinx extension."""

import shlex
from pathlib import Path
from typing import TYPE_CHECKING, Any

from docutils.nodes import Node, paragraph
from docutils.parsers.rst.states import RSTState
from docutils.statemachine import StringList
from jinja2 import Environment
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.environment import BuildEnvironment
from sphinx.errors import ConfigError, ExtensionError, SphinxError
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import ExtensionMetadata

from structured_tutorials import version
from structured_tutorials.models import Command, Commands, File, Tutorial
from structured_tutorials.tutorial import load_tutorial

_NEXT_PART = "tutorial-next-part"

LAST_PART = "__end__"

if TYPE_CHECKING:
    from sphinx.environment import _CurrentDocument


class CurrentDocumentMixin:
    """Mixin adding the current document property and context."""

    if TYPE_CHECKING:
        env: BuildEnvironment

    # NOTE: sphinx 8.2.0 introduced "current_document", temp_data is deprecated and kept only for
    #   backwards compatability: https://github.com/sphinx-doc/sphinx/pull/13151
    @property
    def current_document(self) -> "_CurrentDocument":
        if hasattr(self.env, "current_document"):
            return self.env.current_document
        else:
            return self.env.temp_data

    @property
    def context(self) -> dict[str, Any]:
        return self.current_document["tutorial-context"]  # type: ignore[no-any-return]

    @property
    def jinja(self) -> Environment:
        return self.current_document["tutorial-env"]  # type: ignore[no-any-return]


class TutorialDirective(CurrentDocumentMixin, SphinxDirective):
    """Directive to specify the currently rendered tutorial."""

    has_content = False
    required_arguments = 1
    optional_arguments = 0

    def get_tutorial_path(self, tutorial: str) -> Path:
        root: Path = self.config.tutorial_root
        tutorial_path = Path(tutorial)
        if tutorial_path.is_absolute():
            raise ExtensionError(f"{tutorial}: Path must not be absolute.")
        absolute_path = root / tutorial_path
        if not absolute_path.exists():
            raise ExtensionError(f"{absolute_path}: File not found.")
        return absolute_path

    def run(self) -> list[Node]:
        tutorial_arg = self.arguments[0].strip()

        tutorial_path = self.get_tutorial_path(tutorial_arg)
        tutorial = load_tutorial(tutorial_path)

        self.current_document["tutorial"] = tutorial
        self.current_document["tutorial-next-part"] = tutorial.parts[0].id  # next part to be rendered
        self.current_document["tutorial-env"] = Environment(keep_trailing_newline=True)
        self.current_document["tutorial-context"] = {
            **tutorial.context.documentation,
            "execution": False,
            "documentation": True,
        }

        # NOTE: `highlighting` directive returns a custom Element for unknown reasons
        return []


class PartDirective(CurrentDocumentMixin, SphinxDirective):
    """Directive to show a tutorial part."""

    required_arguments = 0
    optional_arguments = 1  # Next part to display

    def render(self, template: str, **extra_context: Any) -> str:
        return self.jinja.from_string(template).render({**self.context, **extra_context})

    def get_command(self, command: Command) -> dict[str, Any]:
        if isinstance(command.command, str):
            args = self.jinja.from_string(command.command).render(self.context)
        else:
            args = shlex.join(
                tuple(self.jinja.from_string(arg).render(self.context) for arg in command.command)
            )
        prompt = self.jinja.from_string(
            "{{ user }}@{{ host }}:{{ cwd }}{% if user == 'root' %}#{% else %}${% endif %}"
        ).render(self.context)

        data = {"args": args, "prompt": prompt, "output": self.render(command.documentation.output)}

        self.context.update(
            {key: self.render(value) for key, value in command.documentation.update_context.items()}
        )

        return data

    def render_commands(self, commands: Commands) -> str:
        # Render command strings
        command_strings = [self.get_command(cmd) for cmd in commands.commands]

        return self.render(
            """
.. code-block:: console

    {% for cmd in commands %}{{ cmd.prompt }} {{ cmd.args }}{% if cmd.output %}
    {{ cmd.output }}{% endif %}
    {% endfor %} 
""",
            commands=command_strings,
        )

    def render_file(self, file: File) -> str:
        return f"""
.. code-block:: console

    {file}
"""

    def run(self) -> list[paragraph]:
        node = paragraph()

        tutorial: Tutorial = self.current_document["tutorial"]
        if self.arguments:
            next_part_id: str = self.arguments[0].strip()
        else:
            next_part_id = self.current_document[_NEXT_PART]
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
                    self.current_document[_NEXT_PART] = LAST_PART
                else:
                    self.current_document[_NEXT_PART] = tutorial.parts[index + 1].id

                break  # no longer need to loop

        if part_rendered is False:
            raise ExtensionError(f"{next_part_id}: Part not found.")

        lines = StringList(text.splitlines())
        state: RSTState = self.state
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
