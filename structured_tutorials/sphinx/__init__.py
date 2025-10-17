"""Sphinx extension for rendering tutorials."""

from pathlib import Path

from sphinx.application import Sphinx
from sphinx.util.typing import ExtensionMetadata

from structured_tutorials import __version__
from structured_tutorials.sphinx.directives import PartDirective, TutorialDirective
from structured_tutorials.sphinx.utils import validate_configuration


def setup(app: Sphinx) -> ExtensionMetadata:
    """Sphinx setup function."""
    # Add dependency on other extension:
    # app.setup_extension("sphinx.ext.autodoc")
    app.connect("config-inited", validate_configuration)
    app.add_config_value("tutorial_root", Path(app.srcdir), "env", types=[Path])

    app.add_directive("structured-tutorial", TutorialDirective)
    app.add_directive("structured-tutorial-part", PartDirective)

    # return metadata
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
