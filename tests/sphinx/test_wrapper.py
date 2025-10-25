"""Test the TutorialWrapper."""

import textwrap
from pathlib import Path
from typing import Any

import pytest

from structured_tutorials.models import TutorialModel
from structured_tutorials.sphinx.utils import TutorialWrapper


@pytest.mark.parametrize(
    ("commands", "expected"),
    (
        ([{"command": "true"}], "user@host:~$ true\n"),
        ([{"command": "true"}, {"command": "true"}], "user@host:~$ true\nuser@host:~$ true\n"),
        (
            [{"command": "true", "doc": {"output": "example"}}, {"command": "true"}],
            "user@host:~$ true\nexample\nuser@host:~$ true\n",
        ),
        (
            [{"command": "true", "doc": {"output": "example1\nexample2"}}, {"command": "true"}],
            "user@host:~$ true\nexample1\nexample2\nuser@host:~$ true\n",
        ),
        # Change CWD and update command prompt accordingly
        (
            [{"command": "cd test/", "doc": {"update_context": {"cwd": "~/test"}}}, {"command": "true"}],
            "user@host:~$ cd test/\nuser@host:~/test$ true\n",
        ),
        # run `sudo su` and update command prompt accordingly
        (
            [
                {"command": "sudo su", "doc": {"update_context": {"user": "root", "cwd": "/home/user"}}},
                {"command": "true"},
            ],
            "user@host:~$ sudo su\nroot@host:/home/user# true\n",
        ),
    ),
)
def test_code_block_output(commands: tuple[str, ...], expected: str) -> None:
    """Test rendering the output of code-blocks thoroughly."""
    tutorial = TutorialModel.model_validate({"path": Path.cwd(), "parts": [{"commands": commands}]})
    wrapper = TutorialWrapper(tutorial)
    assert wrapper.render_part() == f".. code-block:: console\n\n{textwrap.indent(expected, '    ')}"


@pytest.mark.parametrize(
    ("file", "expected"),
    (
        # file0: Minimal example:
        ({"contents": "foo", "destination": "/ex"}, ":caption: /ex\n\nfoo\n"),
        # file1: Add language
        ({"contents": "foo", "doc": {"language": "yaml"}, "destination": "/ex"}, ":caption: /ex\n\nfoo\n"),
        # file2: Override caption
        (
            {"contents": "foo", "doc": {"caption": "my-caption"}, "destination": "/ex"},
            ":caption: my-caption\n\nfoo\n",
        ),
        # file3: Set caption to False (= no caption)
        #   NOTE: newline in test after {language} is the second newline at the start of expected
        ({"contents": "foo", "doc": {"caption": False}, "destination": "/ex"}, "\nfoo\n"),
        # file4: Add a single option
        (
            {"contents": "foo", "doc": {"linenos": True}, "destination": "/ex"},
            ":caption: /ex\n:linenos:\n\nfoo\n",
        ),
        # file5: Add two options
        (
            {"contents": "foo", "doc": {"linenos": True, "lineno_start": 2}, "destination": "/ex"},
            ":caption: /ex\n:linenos:\n:lineno-start: 2\n\nfoo\n",
        ),
        # file6: Add all options
        (
            {
                "contents": "foo",
                "destination": "/ex",
                "doc": {
                    "language": "json",
                    "linenos": True,
                    "lineno_start": 2,
                    "emphasize_lines": "2",
                    "name": "my-name",
                },
            },
            ":caption: /ex\n:linenos:\n:lineno-start: 2\n:emphasize-lines: 2\n:name: my-name\n\nfoo\n",
        ),
    ),
)
def test_block_output(file: dict[str, Any], expected: str) -> None:
    """Test rendering the output of code-blocks thoroughly."""
    tutorial = TutorialModel.model_validate({"path": Path.cwd(), "parts": [file]})
    wrapper = TutorialWrapper(tutorial)
    language = file.get("doc", {}).get("language", "")
    assert wrapper.render_part() == f".. code-block:: {language}\n{textwrap.indent(expected, '    ')}"
