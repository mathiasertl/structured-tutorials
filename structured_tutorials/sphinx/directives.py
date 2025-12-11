# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Directives for Sphinx."""

from typing import TYPE_CHECKING

from docutils.nodes import Node, paragraph
from docutils.parsers.rst.states import RSTState
from docutils.statemachine import StringList
from sphinx.environment import BuildEnvironment
from sphinx.util.docutils import SphinxDirective

from structured_tutorials.sphinx.utils import TutorialWrapper, get_tutorial_path

if TYPE_CHECKING:
    from sphinx.environment import _CurrentDocument


class CurrentDocumentMixin:
    """Mixin adding the current document property and context."""

    if TYPE_CHECKING:
        env: BuildEnvironment

    # NOTE: sphinx 8.2.0 introduced "current_document", temp_data is deprecated and kept only for
    #   backwards compatability: https://github.com/sphinx-doc/sphinx/pull/13151
    @property
    def current_document(self) -> "_CurrentDocument":  # pragma: no cover
        if hasattr(self.env, "current_document"):
            return self.env.current_document
        else:
            return self.env.temp_data


class TutorialDirective(CurrentDocumentMixin, SphinxDirective):
    """Directive to specify the currently rendered tutorial."""

    has_content = False
    required_arguments = 1
    optional_arguments = 0

    def run(self) -> list[Node]:
        tutorial_arg = self.arguments[0].strip()

        command_text_width: int = self.config.structured_tutorial_command_text_width
        tutorial_path = get_tutorial_path(self.config.tutorial_root, tutorial_arg)
        self.current_document["tutorial"] = TutorialWrapper.from_file(
            tutorial_path, command_text_width=command_text_width
        )

        # NOTE: `highlighting` directive returns a custom Element for unknown reasons
        return []


class PartDirective(CurrentDocumentMixin, SphinxDirective):
    """Directive to show a tutorial part."""

    required_arguments = 0
    optional_arguments = 0

    def run(self) -> list[paragraph]:
        # Render text
        tutorial_wrapper: TutorialWrapper = self.current_document["tutorial"]
        text = tutorial_wrapper.render_part()

        source, _lineno = self.get_source_info()

        # Create sphinx node
        node = paragraph()
        paragraph.source = source
        state: RSTState = self.state
        state.nested_parse(StringList(text.splitlines(), source=source), 0, node)
        return [node]
