# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test local runner."""

from pathlib import Path
from unittest import mock

import pytest
from pytest_subprocess import FakeProcess

from structured_tutorials.errors import RunTutorialException
from structured_tutorials.models import TutorialModel
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
def test_exit_code_tutorial_with_error(
    caplog: pytest.LogCaptureFixture, fp: FakeProcess, doc_runner: LocalTutorialRunner
) -> None:
    """Test behavior if a command has the wrong status code."""
    fp.register(["false"], returncode=2)
    with pytest.raises(RunTutorialException):
        doc_runner.run()
    assert "false failed with return code 2 (expected: 1)." in caplog.text


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
