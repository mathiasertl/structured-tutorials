"""Test models."""

from pathlib import Path
from typing import Any

import pytest

from structured_tutorials.models import FilePartModel, TutorialModel


def test_from_file(tutorial_paths: Path) -> None:
    """Test loading all known tutorials."""
    assert isinstance(TutorialModel.from_file(tutorial_paths), TutorialModel)


@pytest.mark.parametrize(
    ("data", "expected_path", "expected_cwd"),
    (
        ({"path": Path("/foo/bar/test.yaml")}, Path("/foo/bar/test.yaml"), Path("/foo/bar")),
        ({"path": Path("/foo/bar/test.yaml"), "cwd": Path("..")}, Path("/foo/bar/test.yaml"), Path("/foo/")),
        (
            {"path": Path("/foo/bar/test.yaml"), "cwd": Path("bla")},
            Path("/foo/bar/test.yaml"),
            Path("/foo/bar/bla"),
        ),
    ),
)
def test_path_and_cwd(data: dict[str, Any], expected_path: Path, expected_cwd: Path) -> None:
    """Test path and initial cwd validation."""
    model = TutorialModel.model_validate({**data, "parts": []})
    assert model.path == expected_path
    assert model.cwd == expected_cwd


def test_relative_path() -> None:
    """Test for validation error if tutorial is created with relative path."""
    with pytest.raises(ValueError, match=r"foo/test\.yaml: Must be an absolute path\."):
        TutorialModel.model_validate({"path": "foo/test.yaml", "parts": []})


def test_absolute_cwd() -> None:
    """Test for validation error if tutorial is created with an absolute cwd."""
    with pytest.raises(ValueError, match=r"/foo: Must be a relative path \(relative to the tutorial file\)"):
        TutorialModel.model_validate({"path": "/foo/test.yaml", "cwd": "/foo", "parts": []})


def test_file_part_with_no_source_and_no_contents() -> None:
    """Test that file parts have either contents or a source."""
    with pytest.raises(ValueError, match=r"Either contents or source is required\."):
        FilePartModel.model_validate({"destination": "foo.txt"})
