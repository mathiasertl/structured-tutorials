# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test the cli entry point function."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest

from structured_tutorials.cli import main
from structured_tutorials.models import TutorialModel


@pytest.fixture(autouse=True)
def mock_setup_logging() -> Iterator[None]:
    """Fixture to mock logging setup - so that it is not called multiple times."""
    with patch("structured_tutorials.cli.setup_logging", autospec=True):
        yield


def test_simple_tutorial(simple_tutorial: TutorialModel) -> None:
    """Test the cli entry point function by running a simple tutorial."""
    main([str(simple_tutorial.path)])


@pytest.mark.tutorial_path("invalid-yaml")
def test_invalid_yaml_file(capsys: pytest.CaptureFixture[str], tutorial_path: Path) -> None:
    """Test error when loading an invalid YAML file."""
    with pytest.raises(SystemExit) as exc_info:
        main([str(tutorial_path)])
    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert captured.out == ""
    assert "invalid-yaml.yaml: Invalid YAML file:" in captured.err


@pytest.mark.tutorial_path("invalid-model")
def test_invalid_model(capsys: pytest.CaptureFixture[str], tutorial_path: Path) -> None:
    """Test error when loading an invalid model."""
    with pytest.raises(SystemExit) as exc_info:
        main([str(tutorial_path)])
    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert captured.out == ""
    assert "invalid-model.yaml: File is not a valid Tutorial" in captured.err


@pytest.mark.tutorial_path("empty")
def test_empty_file(capsys: pytest.CaptureFixture[str], tutorial_path: Path) -> None:
    """Test error when loading an empty file (equal to an empty model)."""
    with pytest.raises(SystemExit) as exc_info:
        main([str(tutorial_path)])
    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert captured.out == ""
    assert (
        "empty.yaml: File is not a valid Tutorial:\n"
        "File does not contain a mapping at top level." in captured.err
    )


@pytest.mark.tutorial_path("alternatives")
def test_invalid_alternative(capsys: pytest.CaptureFixture[str], tutorial_path: Path) -> None:
    """Test error when loading an empty file (equal to an empty model)."""
    with pytest.raises(SystemExit) as exc_info:
        main(["-a", "wrong", str(tutorial_path)])
    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert captured.out == ""
    assert "Part 1: No alternative selected." in captured.err
