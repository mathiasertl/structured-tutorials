# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test the TutorialWrapper."""

import textwrap
from pathlib import Path
from typing import Any

import pytest
from sphinx.errors import ExtensionError

from structured_tutorials.errors import DestinationIsADirectoryError
from structured_tutorials.models import TutorialModel
from structured_tutorials.sphinx.utils import TutorialWrapper
from tests.conftest import TEST_TUTORIALS_DIR


@pytest.fixture
def wrapper(tutorial: TutorialModel) -> TutorialWrapper:
    """Fixture to get a wrapper from the tutorial fixture."""
    return TutorialWrapper(tutorial)


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


@pytest.mark.tutorial("command-as-list")
def test_command_as_list(wrapper: TutorialWrapper) -> None:
    """Test rendering a command as list."""
    assert wrapper.render_part() == ".. code-block:: console\n\n    user@host:~$ echo 'word with spaces'\n"


@pytest.mark.parametrize(
    ("file_config", "expected"),
    (
        # file0: Minimal example:
        ({"contents": "foo", "destination": "/ex"}, ":caption: /ex\n\nfoo"),
        # file1: Add language
        ({"contents": "foo", "doc": {"language": "yaml"}, "destination": "/ex"}, ":caption: /ex\n\nfoo"),
        # file2: Override caption
        (
            {"contents": "foo", "doc": {"caption": "my-caption"}, "destination": "/ex"},
            ":caption: my-caption\n\nfoo",
        ),
        # file3: Set caption to False (= no caption)
        #   NOTE: newline in test after {language} is the second newline at the start of expected
        ({"contents": "foo", "doc": {"caption": False}, "destination": "/ex"}, "\nfoo"),
        # file4: Add a single option
        (
            {"contents": "foo", "doc": {"linenos": True}, "destination": "/ex"},
            ":caption: /ex\n:linenos:\n\nfoo",
        ),
        # file5: Add two options
        (
            {"contents": "foo", "doc": {"linenos": True, "lineno_start": 2}, "destination": "/ex"},
            ":caption: /ex\n:linenos:\n:lineno-start: 2\n\nfoo",
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
                    "ignore_spelling": True,
                },
            },
            ":caption: :spelling:ignore:`/ex`\n"
            ":linenos:\n"
            ":lineno-start: 2\n"
            ":emphasize-lines: 2\n"
            ":name: my-name\n"
            "\nfoo",
        ),
    ),
)
def test_file_part_options(file_config: dict[str, Any], expected: str) -> None:
    """Test options for files."""
    tutorial = TutorialModel.model_validate({"path": Path.cwd(), "parts": [file_config]})
    wrapper = TutorialWrapper(tutorial)
    language = file_config.get("doc", {}).get("language", "")
    if language:
        language = f" {language}"
    assert wrapper.render_part() == f".. code-block::{language}\n{textwrap.indent(expected, '    ')}"


def test_file_part_with_source() -> None:
    """Test part of a file with source."""
    destination = "foo.txt"
    variable = "foo"
    contents = f"test: {variable}"
    tutorial = TutorialModel.model_validate(
        {
            "path": TEST_TUTORIALS_DIR / "fake.yaml",
            "configuration": {"doc": {"context": {"variable": variable}}},
            "parts": [{"source": "file_contents.txt", "destination": destination}],
        }
    )
    wrapper = TutorialWrapper(tutorial)
    assert wrapper.render_part() == f".. code-block::\n    :caption: {destination}\n\n    {contents}"


@pytest.mark.tutorial("file-copy-destination-dir")
def test_file_part_with_source_with_destination_directory(wrapper: TutorialWrapper) -> None:
    """Test caption when destination is a directory."""
    assert wrapper.render_part().startswith(".. code-block::\n    :caption: dir/file_contents.txt\n\n")


@pytest.mark.tutorial("file-contents-destination-dir")
def test_file_part_with_contents_with_destination_directory(wrapper: TutorialWrapper) -> None:
    """Test caption when destination is a directory."""
    with pytest.raises(DestinationIsADirectoryError):
        assert wrapper.render_part()


def test_file_part_with_source_without_template() -> None:
    """Test part of a file with source with disabled template rendering."""
    destination = "foo.txt"
    variable = "other"
    contents = "test: {{ variable }}"  # NOT expanded, b/c template is false
    tutorial = TutorialModel.model_validate(
        {
            "path": TEST_TUTORIALS_DIR / "fake.yaml",
            "configuration": {"doc": {"context": {"variable": variable}}},
            "parts": [{"source": "file_contents.txt", "destination": destination, "template": False}],
        }
    )
    wrapper = TutorialWrapper(tutorial)
    assert wrapper.render_part() == f".. code-block::\n    :caption: {destination}\n\n    {contents}"


def test_multiple_parts() -> None:
    """Test rendering multiple parts."""
    tutorial = TutorialModel.model_validate(
        {
            "path": TEST_TUTORIALS_DIR / "fake.yaml",
            "parts": [
                {"commands": [{"command": "ls foo"}, {"command": "ls bar"}]},
                {"commands": [{"command": "ls bla"}, {"command": "ls baz"}]},
            ],
        }
    )
    wrapper = TutorialWrapper(tutorial)

    expected = ".. code-block:: console\n\n    user@host:~$ ls foo\n    user@host:~$ ls bar\n"
    assert wrapper.render_part() == expected
    expected = ".. code-block:: console\n\n    user@host:~$ ls bla\n    user@host:~$ ls baz\n"
    assert wrapper.render_part() == expected


def test_multiple_parts_with_skip() -> None:
    """Test rendering multiple parts with a skipped part in the middle."""
    tutorial = TutorialModel.model_validate(
        {
            "path": TEST_TUTORIALS_DIR / "fake.yaml",
            "parts": [
                {"commands": [{"command": "ls foo"}, {"command": "ls bar"}]},
                {"commands": [{"command": "ls not-rendered"}], "doc": {"skip": True}},
                {"commands": [{"command": "ls bla"}, {"command": "ls baz"}]},
            ],
        }
    )
    wrapper = TutorialWrapper(tutorial)

    expected = ".. code-block:: console\n\n    user@host:~$ ls foo\n    user@host:~$ ls bar\n"
    assert wrapper.render_part() == expected
    expected = ".. code-block:: console\n\n    user@host:~$ ls bla\n    user@host:~$ ls baz\n"
    assert wrapper.render_part() == expected


def test_multiple_parts_with_index_error() -> None:
    """Test rendering multiple parts with a skipped part in the middle."""
    tutorial = TutorialModel.model_validate(
        {
            "path": TEST_TUTORIALS_DIR / "fake.yaml",
            "parts": [
                {"commands": [{"command": "ls foo"}, {"command": "ls bar"}]},
            ],
        }
    )
    wrapper = TutorialWrapper(tutorial)

    expected = ".. code-block:: console\n\n    user@host:~$ ls foo\n    user@host:~$ ls bar\n"
    assert wrapper.render_part() == expected
    with pytest.raises(ExtensionError, match=r"No more parts left in tutorial\."):
        wrapper.render_part()


@pytest.mark.parametrize(
    ("parts", "expected"),
    (
        (
            [
                {"commands": [{"command": "true 1"}]},
                {"prompt": "test"},
                {"commands": [{"command": "true 2"}]},
                {"commands": [{"command": "true 3"}]},
            ],
            ["user@host:~$ true 1\n", "user@host:~$ true 2\n", "user@host:~$ true 3\n"],
        ),
    ),
)
def test_prompt(parts: tuple[str, ...], expected: list[str]) -> None:
    """Test rendering a code block that is preceded by a prompt. First rendered part is code block."""
    tutorial = TutorialModel.model_validate({"path": Path.cwd(), "parts": parts})
    wrapper = TutorialWrapper(tutorial)
    assert wrapper.render_part() == f".. code-block:: console\n\n{textwrap.indent(expected[0], '    ')}"
    assert wrapper.render_part() == f".. code-block:: console\n\n{textwrap.indent(expected[1], '    ')}"
    assert wrapper.render_part() == f".. code-block:: console\n\n{textwrap.indent(expected[2], '    ')}"


@pytest.mark.parametrize(
    ("aliases", "alternatives", "expected"),
    (
        (
            {},
            {
                "foo": {"commands": [{"command": "ls foo"}]},
                "bar": {"commands": [{"command": "ls bar"}]},
            },
            ".. tab:: foo\n"
            "\n"
            "    .. code-block:: console\n"
            "\n"
            "        user@host:~$ ls foo\n"
            "\n"
            ".. tab:: bar\n"
            "\n"
            "    .. code-block:: console\n"
            "\n"
            "        user@host:~$ ls bar",
        ),
        (
            {"foo": "FOO", "bar": "BAR"},
            {
                "foo": {"contents": "foo", "destination": "foo.yaml"},
                "bar": {"contents": "bar", "destination": "bar.yaml"},
            },
            ".. tab:: FOO\n"
            "\n"
            "    .. code-block::\n"
            "        :caption: foo.yaml\n"
            "\n"
            "        foo\n"
            "\n"
            ".. tab:: BAR\n"
            "\n"
            "    .. code-block::\n"
            "        :caption: bar.yaml\n"
            "\n"
            "        bar",
        ),
    ),
)
def test_alternatives(aliases: dict[str, str], alternatives: dict[str, Any], expected: str) -> None:
    """Test alternative parts."""
    data = {
        "path": "/dummy.yaml",
        "configuration": {"doc": {"alternative_names": aliases}},
        "parts": [{"alternatives": alternatives}],
    }
    tutorial = TutorialModel.model_validate(data)
    wrapper = TutorialWrapper(tutorial)
    assert wrapper.render_part() == expected


@pytest.mark.tutorial("named-part")
def test_named_part(wrapper: TutorialWrapper) -> None:
    """Test naming individual parts by id."""
    assert wrapper.render_part() == ".. code-block::\n    :caption: bar.txt\n\n    foo"


@pytest.mark.tutorial("named-part")
def test_named_part_with_part_id(wrapper: TutorialWrapper) -> None:
    """Test naming individual parts by id."""
    assert wrapper.render_part("id-file") == ".. code-block::\n    :caption: bar.txt\n\n    foo"


@pytest.mark.tutorial("named-part")
def test_named_part_with_invalid_part_id(wrapper: TutorialWrapper) -> None:
    """Test naming the wrong ID when trying to render the next part."""
    with pytest.raises(ExtensionError, match=r"^wrong: Part is not the next part \(next one is id-file\)\.$"):
        wrapper.render_part("wrong")
