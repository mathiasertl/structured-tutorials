"""Test the local runner."""

from pathlib import Path

import pytest
from pytest_subprocess.fake_process import FakeProcess

from structured_tutorials.models import Command, Commands
from structured_tutorials.runners.base import TutorialError
from structured_tutorials.tutorial import load_tutorial, run_tutorial
from tests.conftest import DATA_DIR, ROOT_DIR


def test_minimal(fp: FakeProcess) -> None:
    """Test the minimal tutorial."""
    fp.register(["ls"])
    tutorial = load_tutorial(DATA_DIR / "minimal.yaml")
    run_tutorial(tutorial)
    assert list(fp.calls) == ["ls"]


def test_minimal_with_error(fp: FakeProcess) -> None:
    """Test the minimal tutorial that throws an error."""
    fp.register(["ls"], returncode=1)
    tutorial = load_tutorial(DATA_DIR / "minimal.yaml")
    with pytest.raises(TutorialError, match=r"^ls: Return code 1 \(expected: 0\)\.$"):
        run_tutorial(tutorial)
    assert list(fp.calls) == ["ls"]


def test_minimal_with_expected_error(fp: FakeProcess) -> None:
    """Test the minimal tutorial that throws an expected error."""
    fp.register(["ls"], returncode=1)
    tutorial = load_tutorial(DATA_DIR / "minimal.yaml")
    assert isinstance(tutorial.parts[0], Commands)
    step = tutorial.parts[0].commands[0]
    assert isinstance(step, Command)
    step.returncode = 1
    run_tutorial(tutorial)
    assert list(fp.calls) == ["ls"]


def test_copy_file(tmpdir: Path, fp: FakeProcess) -> None:
    """Test copy_file tutorial."""
    fp.register(("test", "-e", str(tmpdir)), returncode=1)
    fp.register(("test", "-f", "tests/data/file.txt"))
    fp.register(("test", "-f", f"{tmpdir}/example.txt"))
    fp.register(("grep", "test_value", f"{tmpdir}/example.txt"))
    fp.register(("grep", "test_key", f"{tmpdir}/example.txt"), returncode=1)
    fp.register(("grep", "shell_value", f"{tmpdir}/example.txt"), returncode=1)
    fp.register(f"echo shell_value >> {tmpdir}/example.txt")
    fp.register(("grep", "shell_value", f"{tmpdir}/example.txt"))
    fp.register(("cat", f"{tmpdir}/example.txt"))
    tutorial = load_tutorial(DATA_DIR / "copy_file.yaml")
    tutorial.context.execution["destination"] = tmpdir
    assert tutorial.config.working_directory == ROOT_DIR
    run_tutorial(tutorial)
    assert len(fp.calls) == 9  # the four commands registered above
