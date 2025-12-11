"""Test models."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from structured_tutorials.models import (
    CommandBaseModel,
    FilePartModel,
    TestCommandModel,
    TestPortModel,
    TutorialModel,
)


def test_from_file(tutorial_paths: Path) -> None:
    """Test loading all known tutorials."""
    assert isinstance(TutorialModel.from_file(tutorial_paths), TutorialModel)


def test_default_context(simple_tutorial: TutorialModel) -> None:
    """Test the context that is always present."""
    assert simple_tutorial.configuration.run.context == {
        "cwd": Path.cwd(),
        "doc": False,
        "run": True,
        "tutorial_dir": simple_tutorial.tutorial_root,
        "tutorial_path": simple_tutorial.path,
    }
    assert simple_tutorial.configuration.doc.context == {
        "cwd": "~",
        "doc": True,
        "run": False,
        "host": "host",
        "user": "user",
        "prompt_template": "{{ user }}@{{ host }}:{{ cwd }}{% if user == 'root' %}#{% else %}${% endif %} ",
        "tutorial_dir": simple_tutorial.tutorial_root,
        "tutorial_path": simple_tutorial.path,
    }


@pytest.mark.parametrize(
    ("data", "expected_path", "expected_tutorial_root"),
    (
        ({"path": Path("/foo/bar/test.yaml")}, Path("/foo/bar/test.yaml"), Path("/foo/bar")),
        (
            {"path": Path("/foo/bar/test.yaml"), "tutorial_root": Path("..")},
            Path("/foo/bar/test.yaml"),
            Path("/foo/"),
        ),
        (
            {"path": Path("/foo/bar/test.yaml"), "tutorial_root": Path("bla")},
            Path("/foo/bar/test.yaml"),
            Path("/foo/bar/bla"),
        ),
    ),
)
def test_path_and_tutorial_root(
    data: dict[str, Any], expected_path: Path, expected_tutorial_root: Path
) -> None:
    """Test path and initial tutorial_root validation."""
    model = TutorialModel.model_validate({**data, "parts": []})
    assert model.path == expected_path
    assert model.tutorial_root == expected_tutorial_root


def test_relative_path() -> None:
    """Test for validation error if tutorial is created with relative path."""
    with pytest.raises(ValueError, match=r"foo/test\.yaml: Must be an absolute path\."):
        TutorialModel.model_validate({"path": "foo/test.yaml", "parts": []})


def test_absolute_tutorial_root() -> None:
    """Test for validation error if tutorial is created with an absolute tutorial_root."""
    with pytest.raises(ValueError, match=r"/foo: Must be a relative path \(relative to the tutorial file\)"):
        TutorialModel.model_validate({"path": "/foo/test.yaml", "tutorial_root": "/foo", "parts": []})


def test_file_part_with_absolute_source() -> None:
    """Test that file parts have an absolute source (if set)."""
    with pytest.raises(ValueError, match=r"/foo: Must be a relative path"):
        FilePartModel.model_validate({"source": "/foo", "destination": "foo.txt"})


def test_file_part_with_no_source_and_no_contents() -> None:
    """Test that file parts have either contents or a source."""
    with pytest.raises(ValueError, match=r"Either contents or source is required\."):
        FilePartModel.model_validate({"destination": "foo.txt"})


def test_file_part_with_both_source_and_contents() -> None:
    """Test that file parts have either contents or a source."""
    with pytest.raises(ValueError, match=r"Only one of contents or source is allowed\."):
        FilePartModel.model_validate({"source": "test.txt", "contents": "foo", "destination": "foo.txt"})


def test_file_part_with_no_source_and_destination_dir() -> None:
    """Test error when content is given but destination is a directory."""
    with pytest.raises(
        ValueError, match=r"test/: Destination must not be a directory if contents is given\."
    ):
        FilePartModel.model_validate({"contents": "foo", "destination": "test/"})


@pytest.mark.parametrize(
    ("model", "data", "error"),
    (
        (CommandBaseModel, {"status_code": -1}, r"status_code\s*Input should be greater than or equal to 0"),
        (CommandBaseModel, {"status_code": 256}, r"status_code\s*Input should be less than or equal to 255"),
        (TestCommandModel, {"delay": -1}, r"delay\s*Input should be greater than or equal to 0"),
        (TestCommandModel, {"retry": -1}, r"retry\s*Input should be greater than or equal to 0"),
        (
            TestCommandModel,
            {"backoff_factor": -1},
            r"backoff_factor\s*Input should be greater than or equal to 0",
        ),
        (
            TestPortModel,
            {"host": "example.com", "port": 443, "delay": -1},
            r"delay\s*Input should be greater than or equal to 0",
        ),
        (
            TestPortModel,
            {"host": "example.com", "port": 443, "retry": -1},
            r"retry\s*Input should be greater than or equal to 0",
        ),
        (
            TestPortModel,
            {"host": "example.com", "port": 443, "backoff_factor": -1},
            r"backoff_factor\s*Input should be greater than or equal to 0",
        ),
        (
            TestPortModel,
            {"host": "example.com", "port": -1},
            r"port\s*Input should be greater than or equal to 0",
        ),
        (
            TestPortModel,
            {"host": "example.com", "port": 65536},
            r"port\s*Input should be less than or equal to 65535",
        ),
    ),
)
def test_annotated_field_constraints(model: type[BaseModel], data: dict[str, Any], error: str) -> None:
    """Test annotated field constraints."""
    with pytest.raises(ValueError, match=error):
        model.model_validate(data)
