"""Test app validation."""

from pathlib import Path

import pytest
from sphinx.application import Sphinx
from sphinx.errors import ConfigError

from tests.conftest import TEST_DATA_DIR


def test_tutorial_root_with_wrong_type(tmpdir: Path) -> None:
    """Test passing the wrong type."""
    src_dir = TEST_DATA_DIR / "docs"
    build_dir = tmpdir / "_build"
    with pytest.raises(ConfigError, match=r"^False: Must be of type Path\."):
        Sphinx(
            src_dir,
            src_dir,
            build_dir / "html",
            build_dir / "doctrees",
            "html",
            confoverrides={"tutorial_root": False},
        )


def test_tutorial_root_with_relative_path(tmpdir: Path) -> None:
    """Test passing a relative_path."""
    src_dir = TEST_DATA_DIR / "docs"
    build_dir = tmpdir / "_build"
    with pytest.raises(ConfigError, match=r"^foo: Path must be absolute\."):
        Sphinx(
            src_dir,
            src_dir,
            build_dir / "html",
            build_dir / "doctrees",
            "html",
            confoverrides={"tutorial_root": Path("foo")},
        )
