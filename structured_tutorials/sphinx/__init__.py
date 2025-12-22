"""Sphinx extension for rendering tutorials."""

from pathlib import Path

from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
from sphinx.util.typing import ExtensionMetadata

from structured_tutorials import __version__
from structured_tutorials.sphinx.directives import PartDirective, TutorialDirective
from structured_tutorials.sphinx.utils import validate_configuration


def setup(app: Sphinx) -> ExtensionMetadata:
    """Sphinx setup function."""
    # Add dependency on other extension:
    # app.setup_extension("sphinx.ext.autodoc")
    app.connect("config-inited", validate_configuration)
    app.add_config_value("structured_tutorials_root", Path(app.srcdir), "env", types=[Path])
    app.add_config_value("structured_tutorials_command_text_width", 75, "env", types=[int])

    app.add_directive("structured-tutorial", TutorialDirective)
    app.add_directive("structured-tutorial-part", PartDirective)

    try:
        app.setup_extension("sphinx_inline_tabs")
    except Exception as exc:  # pragma: no cover
        raise ExtensionError("structured_tutorials requires sphinx_inline_tabs") from exc

    # return metadata
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
