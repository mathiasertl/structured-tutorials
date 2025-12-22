# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test the cli entry point function."""

from collections.abc import Iterator
from pathlib import Path
from unittest import mock
from unittest.mock import patch

import pytest
from pytest_subprocess import FakeProcess

from structured_tutorials.cli import main
from structured_tutorials.errors import RunTutorialException
from structured_tutorials.models import TutorialModel


@pytest.fixture(autouse=True)
def mock_setup_logging() -> Iterator[None]:
    """Fixture to mock logging setup - so that it is not called multiple times."""
    with patch("structured_tutorials.cli.setup_logging", autospec=True):
        yield


def test_simple_tutorial(fp: FakeProcess, simple_tutorial: TutorialModel) -> None:
    """Test the cli entry point function by running a simple tutorial."""
    main([str(simple_tutorial.path)])


def test_simple_tutorial_with_run_exception(fp: FakeProcess, simple_tutorial: TutorialModel) -> None:
    """Test the cli entry point function by running a simple tutorial."""
    with mock.patch("structured_tutorials.cli.LocalTutorialRunner.run", side_effect=RunTutorialException()):
        main([str(simple_tutorial.path)])


@pytest.mark.tutorial_path("command-undefined-variable")
def test_undefined_variable(fp: FakeProcess, tutorial_path: Path) -> None:
    """Test running a tutorial with an undefined variable."""
    fp.register("ls ")
    main([str(tutorial_path)])


@pytest.mark.tutorial_path("command-undefined-variable")
def test_undefined_variable_with_definition(fp: FakeProcess, tutorial_path: Path) -> None:
    """Test running a tutorial with an undefined variable, but passing it through the command-line."""
    fp.register("ls foo")
    main([str(tutorial_path), "-D", "variable", "foo"])


@pytest.mark.tutorial_path("invalid-yaml")
def test_invalid_yaml_file(capsys: pytest.CaptureFixture[str], tutorial_path: Path) -> None:
    """Test error when loading an invalid YAML file."""
    assert main([str(tutorial_path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid-yaml.yaml: Invalid YAML file:" in captured.err


@pytest.mark.tutorial_path("invalid-model")
def test_invalid_model(capsys: pytest.CaptureFixture[str], tutorial_path: Path) -> None:
    """Test error when loading an invalid model."""
    assert main([str(tutorial_path)]) == 1
    captured = capsys.readouterr()

    assert captured.out == ""
    assert "invalid-model.yaml: File is not a valid Tutorial" in captured.err


@pytest.mark.tutorial_path("empty")
def test_empty_file(capsys: pytest.CaptureFixture[str], tutorial_path: Path) -> None:
    """Test error when loading an empty file (equal to an empty model)."""
    assert main([str(tutorial_path)]) == 1
    captured = capsys.readouterr()

    assert captured.out == ""
    assert (
        "empty.yaml: File is not a valid Tutorial:\n"
        "File does not contain a mapping at top level." in captured.err
    )


@pytest.mark.tutorial_path("alternatives")
def test_invalid_alternative(capsys: pytest.CaptureFixture[str], tutorial_path: Path) -> None:
    """Test error when loading an empty file (equal to an empty model)."""
    assert main(["-a", "wrong", str(tutorial_path)]) == 1
    captured = capsys.readouterr()

    assert captured.out == ""
    assert "Part 1: No alternative selected." in captured.err
