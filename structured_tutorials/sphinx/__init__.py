"""Sphinx extension."""

from docutils.nodes import Body, paragraph
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import ExtensionMetadata

from structured_tutorials import version


class TutorialPartDirective(SphinxDirective):
    """test..."""

    def get_code_block(self) -> str:
        return """.. code-block:: console
user@host:~# ls foo
bla hugo bar
"""

    def run(self) -> list[paragraph]:
        node = paragraph()
        text = self.get_text()
        lines = StringList(text.splitlines())
        state: Body = self.state
        state.nested_parse(lines, 0, node)
        return [node]


def setup(app: Sphinx) -> ExtensionMetadata:
    """Sphinx setup function."""
    # Add dependency on other extension:
    # app.setup_extension("sphinx.ext.autodoc")
    app.add_directive("tutorial-part", TutorialPartDirective)

    # return metadata
    return {
        "version": version,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
