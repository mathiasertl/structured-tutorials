# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test local runner."""

from pathlib import Path
from unittest import mock

import pytest
from pytest_subprocess import FakeProcess

from structured_tutorials.models import FilePartModel, TutorialModel
from structured_tutorials.runners.local import LocalTutorialRunner
from tests.conftest import DOCS_TUTORIALS_DIR, TEST_TUTORIALS_DIR


def test_simple_tutorial(simple_tutorial: TutorialModel) -> None:
    """Test the local runner by running a simple tutorial."""
    runner = LocalTutorialRunner(simple_tutorial)
    runner.run()


@pytest.mark.doc_tutorial("exit_code")
def test_exit_code_tutorial(fp: FakeProcess, doc_runner: LocalTutorialRunner) -> None:
    """Test status code specification."""
    fp.register(["false"], returncode=1)
    doc_runner.run()


@pytest.mark.doc_tutorial("exit_code")
def test_exit_code_tutorial_with_error(fp: FakeProcess, doc_runner: LocalTutorialRunner) -> None:
    """Test behavior if a command has the wrong status code."""
    fp.register(["false"], returncode=2)
    with pytest.raises(RuntimeError, match=r"false failed with return code 2 \(expected: 1\)\.$"):
        doc_runner.run()


def test_templates_tutorial(fp: FakeProcess) -> None:
    """Test rendering of templates."""
    fp.register("echo run (run)")
    configuration = TutorialModel.from_file(TEST_TUTORIALS_DIR / "templates.yaml")
    runner = LocalTutorialRunner(configuration)
    runner.run()


def test_skip_part(fp: FakeProcess) -> None:
    """Test skipping a part or commands when running."""
    fp.register("ls /etc")
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "skip-part-run" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    runner.run()


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


def test_file_part_with_destination_exists(tmp_path: Path) -> None:
    """Test that file parts have a destination that already exists.."""
    dest = tmp_path / "test.txt"
    configuration = TutorialModel.model_validate(
        {
            "path": "/dummy.yaml",
            "parts": [
                {"contents": "foo", "destination": str(dest)},
                {"contents": "bar", "destination": str(dest)},
            ],
        }
    )
    runner = LocalTutorialRunner(configuration, interactive=False)
    with pytest.raises(RuntimeError, match=rf"^{dest}: Destination already exists\.$"):
        runner.run()

    with open(dest) as stream:
        assert stream.read() == "foo"


def test_file_part_with_contents_with_destination_template(tmp_path: Path) -> None:
    """Test that file parts have a destination that already exists."""
    configuration = TutorialModel.model_validate(
        {
            "path": "/dummy.yaml",
            "configuration": {"run": {"context": {"example": "dest/"}}},
            "parts": [
                {"contents": "foo", "destination": "{{ example }}"},
            ],
        }
    )
    runner = LocalTutorialRunner(configuration, interactive=False)
    with pytest.raises(
        RuntimeError, match=r"^dest/: Destination is directory, but no source given to derive filename\.$"
    ):
        runner.run()


def test_temporary_directory(tmp_path: Path, fp: FakeProcess) -> None:
    """Test running in temporary directory."""
    fp.register("pwd")
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "temporary-directory" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    with (
        mock.patch(
            "structured_tutorials.runners.local.tempfile.TemporaryDirectory.__enter__",
            return_value=str(tmp_path),
        ),
    ):
        runner.run()


def test_git_export(tmp_path: Path, fp: FakeProcess) -> None:
    """Test running git-export."""
    export_path = tmp_path / "git-export-HEAD-xxxxxxxxxxxx"
    fp.register(["git", "archive", "HEAD"])
    fp.register(["tar", "-x", "-C", str(export_path)])
    fp.register(f'echo "Running in {export_path}"')
    fp.register(["test", "-e", "README.md"])
    fp.register(["test", "!", "-e", ".git"])
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "git-export" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    with (
        mock.patch("structured_tutorials.utils.random.choice", return_value="x"),
        mock.patch(
            "structured_tutorials.runners.local.tempfile.TemporaryDirectory.__enter__",
            return_value=str(tmp_path),
        ),
    ):
        runner.run()
