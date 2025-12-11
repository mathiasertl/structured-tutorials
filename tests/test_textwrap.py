# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test textwrapping."""

import pytest

from structured_tutorials.textwrap import wrap_command_filter


@pytest.mark.parametrize(
    ("command", "prompt", "text_width", "expected"),
    (
        ("foo", "user@example.com$ ", 75, "user@example.com$ foo"),
        ("bar", "root@example.net# ", 40, "root@example.net# bar"),
    ),
)
def test_no_wrapping(command: str, prompt: str, text_width: int, expected: str) -> None:
    """Some tests that show when no wrapping occurs."""
    assert wrap_command_filter(command, prompt, text_width) == expected


@pytest.mark.parametrize(
    ("command", "prompt", "text_width", "expected"),
    (
        ("aaa " * 6, "p$ ", 30, "p$ aaa aaa aaa aaa aaa aaa"),
        ("bbb " * 7, "p$ ", 30, "p$ bbb bbb bbb bbb bbb bbb bbb"),
        ("ccc " * 8, "p$ ", 30, "p$ ccc ccc ccc ccc ccc ccc ccc \\\n>    ccc"),
        ("ddd " * 9, "p$ ", 30, "p$ ddd ddd ddd ddd ddd ddd ddd \\\n>    ddd ddd"),
        # decrease the line length until and it'll wrap
        ("eee " * 7, "p$ ", 28, "p$ eee eee eee eee eee eee \\\n>    eee"),
        ("eee " * 7, "p$ ", 26, "p$ eee eee eee eee eee eee \\\n>    eee"),
        ("eee " * 7, "p$ ", 25, "p$ eee eee eee eee eee \\\n>    eee eee"),
    ),
)
def test_single_line_wrapping(command: str, prompt: str, text_width: int, expected: str) -> None:
    """Some tests that show when no wrapping occurs."""
    assert wrap_command_filter(command, prompt, text_width) == expected
    for line in expected.splitlines():
        assert len(line) <= text_width + 2


@pytest.mark.parametrize(
    ("command", "prompt", "text_width", "expected"),
    (
        # This still matches in a single line
        ("aaa aaa a -c dddd", "p$ ", 20, "p$ aaa aaa a -c dddd"),
        # ... but now we wrap, so -c is moved to the next line
        # ("bbb bbb bb -c dddd", "p$ ", 20, "p$ bbb bbb bb \\\n>    -c dddd"),
        # This still matches in one line...
        ("ccc ccc ccc -c -d", "p$ ", 20, "p$ ccc ccc ccc -c -d"),
        # ... but adding a character causes a split.
        ("ddd ddd dddd -c -d", "p$ ", 20, "p$ ddd ddd dddd -c \\\n>    -d"),
        # This still fits in one line...
        ("eee -c --long-opt", "p$ ", 20, "p$ eee -c --long-opt"),
        # ... but now the long opt wraps in the next line
        ("ffff -c --long-opt", "p$ ", 20, "p$ ffff -c \\\n>    --long-opt"),
    ),
)
def test_short_option_wrapping(command: str, prompt: str, text_width: int, expected: str) -> None:
    """Some tests that show when no wrapping occurs."""
    assert wrap_command_filter(command, prompt, text_width) == expected


@pytest.mark.parametrize(
    ("command", "prompt", "text_width", "expected"),
    (
        # Simple newlines (and any adjacent spaces) are treated as a single space
        ('echo    \n   "foo bar"', "p$ ", 75, 'p$ echo "foo bar"'),
        # A more complex multi-line example:
        (
            "docker run --rm -it -v `pwd`:/very/long/path -e DEMO=value \\\n"
            "    ubuntu:24.04\n"
            '    echo "Run a very long command"',
            "user@host:~$ ",
            75,
            "user@host:~$ docker run --rm -it -v `pwd`:/very/long/path -e DEMO=value \\\n"
            '>    ubuntu:24.04 echo "Run a very long command"',
        ),
        # Same as the above, but force newline after the docker image:
        (
            "docker run --rm -it -v `pwd`:/very/long/path -e DEMO=value \\\n"
            "    ubuntu:24.04\\\n"
            '    echo "Run a very long command"',
            "user@host:~$ ",
            75,
            "user@host:~$ docker run --rm -it -v `pwd`:/very/long/path -e DEMO=value \\\n"
            ">    ubuntu:24.04 \\\n"
            '>    echo "Run a very long command"',
        ),
        # empty lines are also skipped, allowing the user to structure parts of the command in YAML
        # Same as the above, but force newline after the docker image:
        (
            # add some empty newlines to the above prompt:
            "docker run --rm -it -v `pwd`:/very/long/path -e DEMO=value \\\n\\\n\\\n"
            "    ubuntu:24.04\\\n\\\n"
            '    echo "Run a very long command"',
            "user@host:~$ ",
            75,
            "user@host:~$ docker run --rm -it -v `pwd`:/very/long/path -e DEMO=value \\\n"
            ">    ubuntu:24.04 \\\n"
            '>    echo "Run a very long command"',
        ),
    ),
)
def test_multiline_commands(command: str, prompt: str, text_width: int, expected: str) -> None:
    """Test when the command already contains newlines to force a wrap."""
    assert wrap_command_filter(command, prompt, text_width) == expected


@pytest.mark.parametrize(
    ("command", "prompt", "text_width", "expected"),
    (
        # Whitespaces are preserved
        ('echo  "foo  bar"', "p$ ", 20, 'p$ echo  "foo  bar"'),
    ),
)
def test_multiple_space_filtering(command: str, prompt: str, text_width: int, expected: str) -> None:
    """Some tests that show when no wrapping occurs."""
    assert wrap_command_filter(command, prompt, text_width) == expected
