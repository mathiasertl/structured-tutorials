# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Utility functions for the sphinx extension."""

import os
import shlex
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from importlib import resources
from pathlib import Path
from typing import Any

from jinja2 import Environment
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.errors import ConfigError, ExtensionError

from structured_tutorials import templates
from structured_tutorials.errors import DestinationIsADirectoryError
from structured_tutorials.models import (
    AlternativeModel,
    CommandsPartModel,
    FilePartModel,
    PromptModel,
    TutorialModel,
)
from structured_tutorials.models.tutorial import DocumentationAlternativeConfigurationModel
from structured_tutorials.textwrap import wrap_command_filter

TEMPLATE_DIR = resources.files(templates)


def validate_configuration(app: Sphinx, config: Config) -> None:
    """Validate configuration directives, so that we can rely on values later."""
    root = config.structured_tutorials_root
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

    def __init__(
        self, tutorial: TutorialModel, context: dict[str, Any] | None = None, command_text_width: int = 75
    ) -> None:
        self.tutorial = tutorial
        self.next_part = 0
        self.env = Environment(keep_trailing_newline=True)
        self.env.filters["wrap_command"] = wrap_command_filter
        self.context = deepcopy(tutorial.configuration.context)
        self.context.update(deepcopy(tutorial.configuration.doc.context))
        if context:
            self.context.update(context)

        # settings from sphinx:
        self.command_text_width = command_text_width

    @contextmanager
    def update_context(self, context: dict[str, Any]) -> Iterator[None]:
        orig_context = self.context
        new_context = deepcopy(orig_context)
        new_context.update(context)
        try:
            self.context = new_context
            yield
        finally:
            self.context = orig_context

    @classmethod
    def from_file(
        cls, path: Path, context: dict[str, Any] | None = None, command_text_width: int = 75
    ) -> "TutorialWrapper":
        """Factory method for creating a TutorialWrapper from a file."""
        tutorial = TutorialModel.from_file(path)
        return cls(tutorial, context=context, command_text_width=command_text_width)

    def render(self, template: str) -> str:
        return self.env.from_string(template).render(self.context)

    def render_code_block(self, part: CommandsPartModel) -> str:
        """Render a CommandsPartModel as a code-block."""
        commands = []
        for command_config in part.commands:
            # Skip individual commands if marked as skipped for documentation
            if command_config.doc.skip:
                continue

            # Render the prompt
            prompt = self.env.from_string(self.context["prompt_template"]).render(self.context)

            # Render the command
            if isinstance(command_config.command, str):
                command = self.render(command_config.command)
            else:
                command = shlex.join(self.render(token) for token in command_config.command)

            # Render output
            output_template = command_config.doc.output.rstrip("\n")
            output = self.env.from_string(output_template).render(self.context)

            # Finally, render the command
            command_template = """{{ command|wrap_command(prompt, text_width) }}{% if output %}
{{ output }}{% endif %}"""
            command_context = {
                "prompt": prompt,
                "command": command,
                "output": output,
                "text_width": self.command_text_width,
            }
            rendered_command = self.env.from_string(command_template).render(command_context)
            commands.append(rendered_command)

            # Update the context from update_context
            self.context.update(command_config.doc.update_context)

        template_str = TEMPLATE_DIR.joinpath("commands_part.rst.template").read_text("utf-8")
        template = self.env.from_string(template_str)
        return template.render(
            {
                "commands": commands,
                "text_after": self.render(part.doc.text_after),
                "text_before": self.render(part.doc.text_before),
            }
        )

    def render_file(self, part: FilePartModel) -> str:
        content = part.contents
        if content is None:
            assert part.source is not None  # assured by model validation
            with open(self.tutorial.tutorial_root / part.source) as stream:
                content = stream.read()

        # Only render template if it is configured to be a template.
        if part.template:
            content = self.render(content)

        # Render the caption (default is the filename)
        if part.doc.caption:
            caption = self.render(part.doc.caption)
        elif part.doc.caption is not False:
            caption = self.render(str(part.destination))
            if caption.endswith(os.path.sep):
                # Model validation already validates that the destination does not look like a directory, if
                # no source is set, but this could be tricked if the destination is a template.
                if not part.source:
                    raise DestinationIsADirectoryError(
                        f"{caption}: Destination is directory, but no source given to derive filename."
                    )
                caption = os.path.join(caption, part.source.name)
        else:
            caption = ""

        if part.doc.ignore_spelling:
            caption = f":spelling:ignore:`{caption}`"

        # Read template from resources
        template_str = TEMPLATE_DIR.joinpath("file_part.rst.template").read_text("utf-8")

        # Render template
        template = self.env.from_string(template_str)
        value = template.render(
            {
                "part": part,
                "content": content,
                "caption": caption,
                "text_after": self.render(part.doc.text_after),
                "text_before": self.render(part.doc.text_before),
            }
        )
        return value

    def render_alternatives(self, part: AlternativeModel) -> str:
        tabs = []
        for key, alternate_part in part.alternatives.items():
            config = self.tutorial.configuration.doc.alternatives.get(
                key, DocumentationAlternativeConfigurationModel()
            )
            name = config.name or key

            additional_context = {"alternative": key, "alternative_name": name, **config.context}

            with self.update_context(additional_context):
                if isinstance(alternate_part, CommandsPartModel):
                    tabs.append((name, self.render_code_block(alternate_part).strip()))
                elif isinstance(alternate_part, FilePartModel):
                    tabs.append((name, self.render_file(alternate_part).strip()))
                else:  # pragma: no cover
                    raise ExtensionError("Alternative found unknown part type.")

        # Read template from resources
        template_str = TEMPLATE_DIR.joinpath("alternative_part.rst.template").read_text("utf-8")

        # Render template
        template = self.env.from_string(template_str)
        value = template.render(
            {
                "part": part,
                "tabs": tabs,
                "text_after": self.render(part.doc.text_after),
                "text_before": self.render(part.doc.text_before),
            }
        )
        return value.strip()

    def render_part(self, part_id: str | None = None) -> str:
        """Render the given part of the tutorial."""
        # Find the next part that is not skipped
        for part in self.tutorial.parts[self.next_part :]:
            self.next_part += 1

            # Ignore prompt models when rendering tutorials.
            if isinstance(part, PromptModel):
                continue

            # If the part is not configured to be skipped for docs, use it.
            if not part.doc.skip:
                if part_id is not None and part.id != part_id:
                    raise ExtensionError(f"{part_id}: Part is not the next part (next one is {part.id}).")
                break
        else:
            raise ExtensionError("No more parts left in tutorial.")

        if isinstance(part, CommandsPartModel):
            text = self.render_code_block(part)
        elif isinstance(part, FilePartModel):
            text = self.render_file(part)
        elif isinstance(part, AlternativeModel):
            text = self.render_alternatives(part)
        else:  # pragma: no cover
            raise ExtensionError(f"{part}: Unsupported part type.")

        self.context.update(part.doc.update_context)
        return text
