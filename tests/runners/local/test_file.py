# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Tests for file parts."""

from pathlib import Path

import pytest

from structured_tutorials.errors import RunTutorialException
from structured_tutorials.models import FilePartModel, TutorialModel
from structured_tutorials.runners.local import LocalTutorialRunner


@pytest.mark.doc_tutorial("file-copy")
def test_file_copy(tmp_path: Path, doc_tutorial: TutorialModel) -> None:
    """Test skipping a part when running."""
    # Update destination to copy to tmp_path
    for part in doc_tutorial.parts:
        assert isinstance(part, FilePartModel)
        part.destination = str(tmp_path) + part.destination
    runner = LocalTutorialRunner(doc_tutorial, interactive=False)
    runner.run()

    part = doc_tutorial.parts[0]
    assert isinstance(part, FilePartModel)
    assert Path(part.destination).exists()
    with open(part.destination) as stream:
        assert stream.read() == "inline contents: at runtime"

    part = doc_tutorial.parts[1]
    assert isinstance(part, FilePartModel)
    assert Path(part.destination).exists()
    with open(part.destination) as stream:
        assert stream.read() == "inline contents: {{ variable }}"

    part = doc_tutorial.parts[2]
    assert isinstance(part, FilePartModel)
    assert Path(part.destination).exists()
    with open(part.destination) as stream:
        assert stream.read() == "test: at runtime"

    part = doc_tutorial.parts[3]
    assert isinstance(part, FilePartModel)
    assert Path(part.destination).exists()
    with open(part.destination) as stream:
        assert stream.read() == "test: {{ variable }}"

    part = doc_tutorial.parts[4]
    assert isinstance(part, FilePartModel)
    destination = Path(part.destination) / "file_contents.txt"
    assert destination.exists()
    with open(destination) as stream:
        assert stream.read() == "test: {{ variable }}"


@pytest.mark.tutorial("file-contents-exists")
def test_file_part_with_destination_exists(
    caplog: pytest.LogCaptureFixture, tmp_path: Path, runner: LocalTutorialRunner
) -> None:
    """Test that file parts have a destination that already exists."""
    runner.context["tmp_path"] = tmp_path
    with pytest.raises(RunTutorialException):
        runner.run()
    assert f"{tmp_path}/destination.txt: Destination already exists" in caplog.text

    # Make sure we still have the old contents
    with open(tmp_path / "destination.txt") as stream:
        assert stream.read() == "foo"


@pytest.mark.tutorial("file-contents-destination-dir")
def test_file_part_with_contents_with_destination_template(
    caplog: pytest.LogCaptureFixture, tmp_path: Path, runner: LocalTutorialRunner
) -> None:
    """Test that file parts have a destination that already exists."""
    with pytest.raises(
        RunTutorialException,
        match=r"^dir/: Destination is directory, but no source given to derive filename\.$",
    ):
        runner.run()
    assert "dir/: Destination is directory, but no source given to derive filename." in caplog.text
