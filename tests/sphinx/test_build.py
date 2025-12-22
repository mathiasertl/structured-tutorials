# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test building a minimal Sphinx application."""

from sphinx.application import Sphinx


def test_minimal_build(sphinx_app: Sphinx) -> None:
    """Test building a minimal tutorial."""
    sphinx_app.build()

    assert sphinx_app.outdir.is_dir(), f"Directory not found: {sphinx_app.outdir}"
    index_html = sphinx_app.outdir / "index.html"
    assert index_html.exists()

    # Make sure that extra context is included:
    variable_defined_in_config_path = sphinx_app.outdir / "variable_defined_in_config.html"
    assert variable_defined_in_config_path.exists()
    variable_defined_in_config = variable_defined_in_config_path.read_text()
    assert "variable-defined-in-config" in variable_defined_in_config
