"""Tests for pydantic models."""

import pytest

from structured_tutorials.models import Command, Contexts, Part


@pytest.mark.parametrize(
    ("command", "shell", "expected"),
    (
        ("ls", False, ("ls",)),
        (["ls"], False, ("ls",)),
        (["ls"], True, "ls"),
        (["ls", "foo bar"], True, "ls 'foo bar'"),
        ("echo foo | cat", True, "echo foo | cat"),
    ),
)
def test_step_command_shell(command: list[str] | str, shell: bool, expected: tuple[str, ...] | str) -> None:
    """Test the `shell` parameter."""
    step = Command(command=command, shell=shell)
    assert step.command == expected


@pytest.mark.parametrize("returncode", (-1, 256))
def test_step_returncode_out_of_bounds(returncode: int) -> None:
    """Test limits in return code."""
    with pytest.raises(ValueError, match=r"returncode"):
        Command(command=["ls"], returncode=returncode)


def test_part_with_step_shortcuts() -> None:
    """Test shortcuts for steps in a part."""
    part = Part(commands=["ls /", ["ls", "/"], {"command": "ls /"}])
    assert part.commands == (
        Command(command=("ls", "/")),
        Command(command=("ls", "/")),
        Command(command=("ls", "/")),
    )


def test_context_default() -> None:
    """Test default values for context."""
    ctxs = Contexts(sphinx=None, execution={})
    assert ctxs.execution == {}
    assert ctxs.sphinx == {}
