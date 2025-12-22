"""Standard Sphinx configuration module."""

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
from pathlib import Path

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "structured-tutorials"
copyright = "2025, Mathias Ertl"
author = "Mathias Ertl"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_rtd_theme",
    "sphinxcontrib.spelling",
    "structured_tutorials.sphinx",
    "sphinx_inline_tabs",
]
html_theme = "sphinx_rtd_theme"

DOC_ROOT = Path(__file__).parent
structured_tutorials_root = DOC_ROOT / "tutorials"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Nitpicky mode warns about references where the target cannot be found.
nitpicky = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = "alabaster"
html_static_path = ["_static"]
