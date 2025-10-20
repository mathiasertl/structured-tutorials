"""Test the TutorialWrapper."""

import textwrap

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
    tutorial = TutorialModel.model_validate({"parts": [{"commands": commands}]})
    wrapper = TutorialWrapper(tutorial)
    assert wrapper.render_part() == f".. code-block:: console\n\n{textwrap.indent(expected, '    ')}"
