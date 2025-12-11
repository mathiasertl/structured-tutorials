# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Conftest module for pytest."""

from pathlib import Path

import pytest
from pytest_subprocess import FakeProcess
from sphinx.application import Sphinx

from structured_tutorials.models import TutorialModel

TEST_DIR = Path(__file__).parent.absolute()
ROOT_DIR = TEST_DIR.parent
TEST_DATA_DIR = TEST_DIR / "data"
TEST_TUTORIALS_DIR = TEST_DATA_DIR / "tutorials"
DOCS_DIR = ROOT_DIR / "docs"
DOCS_TUTORIALS_DIR = DOCS_DIR / "tutorials"

assert TEST_TUTORIALS_DIR.exists()
assert DOCS_TUTORIALS_DIR.exists()

test_tutorials = [x / "tutorial.yaml" for x in TEST_TUTORIALS_DIR.iterdir() if x.is_dir()]
docs_tutorials = [x / "tutorial.yaml" for x in DOCS_TUTORIALS_DIR.iterdir() if x.is_dir()]


@pytest.fixture(scope="session", params=test_tutorials + docs_tutorials)
def tutorial_paths(request: pytest.FixtureRequest) -> Path:
    """Parametrized fixture for all known tutorials."""
    assert isinstance(request.param, Path)
    return request.param


@pytest.fixture
def sphinx_app(tmpdir: Path) -> Sphinx:
    """Fixture for creating a Sphinx application."""
    # NOTE: This already calls setup()
    src_dir = TEST_DATA_DIR / "docs"
    build_dir = tmpdir / "_build"
    return Sphinx(src_dir, src_dir, build_dir / "html", build_dir / "doctrees", "html")


@pytest.fixture
def simple_tutorial(fp: FakeProcess) -> TutorialModel:
    """Fixture for running a simple tutorial."""
    fp.register(["ls"])
    fp.register(["touch", "/tmp/test.txt"])
    fp.register(["rm", "/tmp/test.txt"])
    return TutorialModel.from_file(TEST_TUTORIALS_DIR / "simple.yaml")
