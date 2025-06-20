"""Tests for pydantic models."""

import pytest

from structured_tutorials.models import Command, Commands, Contexts


@pytest.mark.parametrize(
    ("command", "expected"),
    ((["ls"], ("ls",)), ("echo foo | cat", "echo foo | cat")),
)
def test_step_command_shell(command: list[str] | str, expected: tuple[str, ...] | str) -> None:
    """Test the `shell` parameter."""
    step = Command(command=command)
    assert step.command == expected


@pytest.mark.parametrize("returncode", (-1, 256))
def test_step_returncode_out_of_bounds(returncode: int) -> None:
    """Test limits in return code."""
    with pytest.raises(ValueError, match=r"returncode"):
        Command(command=["ls"], returncode=returncode)


def test_part_with_step_shortcuts() -> None:
    """Test shortcuts for commands in a part."""
    part = Commands(commands=["ls /", ["ls", "/"], {"command": ["ls", "/"]}])
    assert part.commands == (
        Command(command=("ls /"), id="0"),
        Command(command=("ls", "/"), id="1"),
        Command(command=("ls", "/"), id="2"),
    )


def test_context_default() -> None:
    """Test default values for context."""
    ctxs = Contexts(sphinx=None, execution={})
    assert ctxs.execution == {}
    assert ctxs.documentation == {"user": "user", "host": "host", "cwd": "~"}
