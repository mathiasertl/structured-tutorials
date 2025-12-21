# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test local runner."""

import os
import subprocess
from pathlib import Path
from unittest import mock
from unittest.mock import call

import pytest
from pytest_subprocess import FakeProcess

from structured_tutorials.errors import CommandOutputTestError, CommandTestError, PromptNotConfirmedError
from structured_tutorials.models import FilePartModel, TutorialModel
from structured_tutorials.runners.local import LocalTutorialRunner
from tests.conftest import DOCS_TUTORIALS_DIR, TEST_TUTORIALS_DIR


@pytest.fixture
def runner(tutorial: TutorialModel) -> LocalTutorialRunner:
    """Fixture to retrieve a local tutorial runner based on the tutorial fixture."""
    return LocalTutorialRunner(tutorial, interactive=False)


@pytest.fixture
def doc_runner(doc_tutorial: TutorialModel) -> LocalTutorialRunner:
    """Fixture to retrieve a local tutorial runner based on an example from the documentation."""
    return LocalTutorialRunner(doc_tutorial, interactive=False)


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


def test_command_cleanup_from_docs(fp: FakeProcess) -> None:
    """Test the cleanup from docs."""
    fp.register("mkdir -p /tmp/new-directory")
    fp.register("rm -r /tmp/new-directory")
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "cleanup" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    runner.run()


def test_command_cleanup_from_docs_with_no_errors(fp: FakeProcess) -> None:
    """Test the cleanup from docs."""
    fp.register("cmd1")
    fp.register("cmd2")
    fp.register("clean3")
    fp.register("clean1")
    fp.register("clean2")
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "cleanup-multiple" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    runner.run()


@pytest.mark.doc_tutorial("cleanup-multiple")
def test_command_cleanup_from_docs_with_error(fp: FakeProcess, doc_runner: LocalTutorialRunner) -> None:
    """Test the cleanup from docs."""
    fp.register("cmd1", returncode=1)
    fp.register("clean1")
    fp.register("clean2")
    with pytest.raises(RuntimeError, match=r"cmd1 failed with return code 1 \(expected: 0\)\.$"):
        doc_runner.run()


def test_test_commands(fp: FakeProcess) -> None:
    """Test the cleanup from docs."""
    fp.register("touch test.txt")
    fp.register("test -e test.txt")
    fp.register("rm test.txt")  # cleanup of part 1
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "test-command" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    runner.run()


@pytest.mark.tutorial("command-as-list")
def test_command_as_list(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test running a command as list."""
    recorder_main = fp.register(["echo", "word with spaces"])
    recorder_test = fp.register(["ls", "test with spaces"])
    recorder_cleanup = fp.register(["ls", "cleanup with spaces"])
    runner.run()
    expected = {"shell": False, "stderr": None, "stdout": None, "text": True}
    assert recorder_main.calls[0].kwargs == expected
    assert recorder_test.calls[0].kwargs == expected
    assert recorder_cleanup.calls[0].kwargs == expected


@pytest.mark.tutorial("command-with-chdir")
def test_command_with_chdir(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test changing the working directory after a command."""
    fp.register("ls")
    with mock.patch("os.chdir", autospec=True) as mock_chdir:
        runner.run()
    mock_chdir.assert_called_once_with(Path("/does/not/exist"))


@pytest.mark.tutorial("command-hide-output")
def test_command_hide_output(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test running a commands with hiding the output."""
    # NOTE: output passed to fp.register() does not register in `capsys` fixture
    recorder_main = fp.register("ls main")
    recorder_test = fp.register("ls test")
    recorder_cleanup = fp.register("ls cleanup")
    runner.run()
    expected = {"shell": True, "stderr": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "text": True}
    assert recorder_main.calls[0].kwargs == expected
    assert recorder_test.calls[0].kwargs == expected
    assert recorder_cleanup.calls[0].kwargs == expected


@pytest.mark.tutorial("command-test-output")
def test_command_capture_output(
    capsys: pytest.CaptureFixture[str], fp: FakeProcess, runner: LocalTutorialRunner
) -> None:
    """Test running a commands with capturing the output."""
    recorder = fp.register("echo foo bar bla", stdout="foo bar bla", stderr="foo bla bla")
    runner.run()
    expected = {"shell": True, "stderr": subprocess.PIPE, "stdout": subprocess.PIPE, "text": True}
    assert recorder.calls[0].kwargs == expected
    output = capsys.readouterr()
    assert output.out == "--- stdout ---\nfoo bar bla\n--- stderr ---\nfoo bla bla\n"
    assert output.err == ""
    assert runner.context["stdout"] == "bar"
    assert runner.context["stderr"] == "bla"


@pytest.mark.tutorial("command-test-output")
def test_command_with_invalid_output(
    capsys: pytest.CaptureFixture[str], fp: FakeProcess, runner: LocalTutorialRunner
) -> None:
    """Test running a commands with capturing the output."""
    fp.register("echo foo bar bla", stdout="wrong output")
    with pytest.raises(CommandOutputTestError):
        runner.run()


@pytest.mark.doc_tutorial("test-command")
def test_test_commands_with_command_error(fp: FakeProcess, doc_runner: LocalTutorialRunner) -> None:
    """Test the cleanup from docs."""
    fp.register("touch test.txt")
    fp.register("test -e test.txt", returncode=1)
    fp.register("rm test.txt")  # cleanup of part 1
    with pytest.raises(CommandTestError, match=r"^Test did not pass$"):
        doc_runner.run()


@pytest.mark.tutorial("command-simple")
def test_command_with_error_with_interactive_mode(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test prompt when an error occurs when interactive mode is enabled."""
    fp.register("ls", returncode=1)
    runner.interactive = True  # force interactive mode
    with pytest.raises(RuntimeError, match=r"^ls failed with return code 1 \(expected: 0\)\.$"):
        with mock.patch("builtins.input", return_value="", autospec=True) as mock_input:
            runner.run()
    mock_input.assert_called_once_with(
        "An error occurred while running the tutorial.\n"
        f"Current working directory is {os.getcwd()}\n"
        "\n"
        "Press Enter to continue... "
    )


def test_test_commands_with_one_socket_error(fp: FakeProcess) -> None:
    """Test the cleanup from docs."""
    fp.register("sleep 3s && ncat -e /bin/cat -k -l 1234 &")
    fp.register("pkill sleep")
    fp.register("pkill ncat")
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "test-port" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    with (
        mock.patch("socket.socket", autospec=True) as mock_socket,
        mock.patch("time.sleep", autospec=True) as mock_sleep,
    ):
        connect_mock = mock.MagicMock(side_effect=[Exception("error"), True])
        mock_socket.return_value.connect = connect_mock
        runner.run()

    assert mock_sleep.mock_calls == [mock.call(2), mock.call(1.0)]
    assert connect_mock.mock_calls == [mock.call(("localhost", 1234)), mock.call(("localhost", 1234))]


@pytest.mark.doc_tutorial("test-port")
def test_test_commands_with_socket_error(fp: FakeProcess, doc_runner: LocalTutorialRunner) -> None:
    """Test the cleanup from docs."""
    fp.register("sleep 3s && ncat -e /bin/cat -k -l 1234 &")
    fp.register("pkill sleep")
    fp.register("pkill ncat")
    with (
        mock.patch("socket.socket", autospec=True) as mock_socket,
        mock.patch("time.sleep", autospec=True) as mock_sleep,
    ):
        connect_mock = mock.MagicMock(side_effect=Exception("error"))
        mock_socket.return_value.connect = connect_mock
        with pytest.raises(CommandTestError, match=r"^Test did not pass$"):
            doc_runner.run()

    # 2-second sleep is the initial delay
    assert mock_sleep.mock_calls == [mock.call(2), mock.call(1.0), mock.call(2.0), mock.call(4.0)]
    assert connect_mock.mock_calls == [
        mock.call(("localhost", 1234)),
        mock.call(("localhost", 1234)),
        mock.call(("localhost", 1234)),
        mock.call(("localhost", 1234)),
    ]


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


def test_alternatives_with_command(fp: FakeProcess) -> None:
    """Test enter function."""
    configuration = TutorialModel.model_validate(
        {
            "path": "/dummy.yaml",
            "parts": [
                {
                    "alternatives": {
                        "foo": {"commands": [{"command": "ls foo"}]},
                        "bar": {"commands": [{"command": "ls bar"}]},
                    }
                },
            ],
        }
    )
    fp.register("ls foo")
    runner = LocalTutorialRunner(configuration, alternatives=("foo",))
    runner.run()

    fp.register("ls bar")
    runner = LocalTutorialRunner(configuration, alternatives=("bar",))
    runner.run()


def test_alternatives_with_file_part(tmp_path: Path) -> None:
    """Test enter function."""
    configuration = TutorialModel.model_validate(
        {
            "path": tmp_path / "dummy.yaml",
            "parts": [
                {
                    "alternatives": {
                        "foo": {"contents": "foo", "destination": str(tmp_path / "foo.txt")},
                        "bar": {"contents": "bar", "destination": str(tmp_path / "bar.txt")},
                    }
                },
            ],
        }
    )
    runner = LocalTutorialRunner(configuration, alternatives=("foo",))
    runner.run()
    assert (tmp_path / "foo.txt").exists()

    runner = LocalTutorialRunner(configuration, alternatives=("bar",))
    runner.run()
    assert (tmp_path / "bar.txt").exists()


def test_alternatives_with_no_selected_part(tmp_path: Path) -> None:
    """Test enter function."""
    configuration = TutorialModel.model_validate(
        {
            "path": tmp_path / "dummy.yaml",
            "parts": [
                {
                    "alternatives": {
                        "foo": {"commands": [{"command": "ls foo"}]},
                        "bar": {"commands": [{"command": "ls bar"}]},
                    }
                },
            ],
        }
    )
    runner = LocalTutorialRunner(configuration, alternatives=("bla",))
    runner.run()


@pytest.mark.parametrize("prompt", ("test", "test    "))
@pytest.mark.parametrize("answer", ("", "yes", "y", "no", "n", "foobar"))
def test_enter_prompt(prompt: str, answer: str) -> None:
    """Test enter function."""
    configuration = TutorialModel.model_validate({"path": "/dummy.yaml", "parts": [{"prompt": prompt}]})
    runner = LocalTutorialRunner(configuration)
    with mock.patch("builtins.input", return_value=answer, autospec=True) as mock_input:
        runner.run()
    mock_input.assert_called_once_with(f"{prompt.strip()} ")


@pytest.mark.tutorial("prompt-simple")
def test_prompt_with_noninteractive_mode(runner: LocalTutorialRunner) -> None:
    """Test running a tutorial with a prompt in non-interactive mode - prompt is skipped."""
    with mock.patch("builtins.input", return_value="", autospec=True) as mock_input:
        runner.run()
    mock_input.assert_not_called()


@pytest.mark.parametrize("answer", ("", "y", "yes"))
def test_confirm_prompt_confirms(answer: str) -> None:
    """Test confirm prompt where empty answer passes."""
    configuration = TutorialModel.model_validate(
        {"path": "/dummy.yaml", "parts": [{"prompt": "example:", "type": "confirm"}]}
    )
    runner = LocalTutorialRunner(configuration)
    with mock.patch("builtins.input", return_value=answer, autospec=True) as mock_input:
        runner.run()
    mock_input.assert_called_once_with("example: ")


@pytest.mark.parametrize("answer", ("y", "yes"))
def test_confirm_prompt_confirms_with_default_false(answer: str) -> None:
    """Test confirm prompt where answer passes with default=False."""
    configuration = TutorialModel.model_validate(
        {"path": "/dummy.yaml", "parts": [{"prompt": "example:", "type": "confirm", "default": False}]}
    )
    runner = LocalTutorialRunner(configuration)
    with mock.patch("builtins.input", return_value=answer, autospec=True) as mock_input:
        runner.run()
    mock_input.assert_called_once_with("example: ")


@pytest.mark.parametrize("answer", ("", "n", "no"))
@pytest.mark.tutorial("prompt-confirm")
def test_confirm_prompt_does_not_confirm_with_default_false(answer: str, runner: LocalTutorialRunner) -> None:
    """Test confirm prompt where answer does not confirm with default=False."""
    runner.interactive = True  # force interactive mode
    with mock.patch("builtins.input", return_value=answer, autospec=True) as mock_input:
        with pytest.raises(PromptNotConfirmedError, match=r"^State was not confirmed\.$"):
            runner.run()
    mock_input.assert_called_once_with("example: ")


def test_confirm_prompt_with_invalid_response() -> None:
    """Test confirm prompt where we first give an invalid response."""
    configuration = TutorialModel.model_validate(
        {
            "path": "/dummy.yaml",
            "parts": [{"prompt": "example:", "type": "confirm", "default": False}],
        }
    )
    runner = LocalTutorialRunner(configuration)
    with mock.patch("builtins.input", side_effect=["foobar", "y"], autospec=True) as mock_input:
        runner.run()
    mock_input.assert_has_calls([call("example: "), call("example: ")])


def test_confirm_prompt_does_not_confirm_error_template() -> None:
    """Test confirm prompt where answer does not confirm with default=False."""
    answer = "no"
    value = "example value"
    configuration = TutorialModel.model_validate(
        {
            "path": "/dummy.yaml",
            "configuration": {"run": {"context": {"example": value}}},
            "parts": [
                {
                    "prompt": "example:",
                    "type": "confirm",
                    "default": False,
                    "error": "{{ response }}: {{ example }}: This is wrong.",
                }
            ],
        }
    )
    runner = LocalTutorialRunner(configuration)
    with mock.patch("builtins.input", return_value=answer, autospec=True) as mock_input:
        with pytest.raises(PromptNotConfirmedError, match=rf"^{answer}: {value}: This is wrong\.$"):
            runner.run()
    mock_input.assert_called_once_with("example: ")


def test_prompt_template() -> None:
    """Test that the prompt is rendered as a template."""
    configuration = TutorialModel.model_validate(
        {
            "path": "/dummy.yaml",
            "configuration": {"run": {"context": {"example": "dest/"}}},
            "parts": [{"prompt": "Go to {{ example }}"}],
        }
    )
    runner = LocalTutorialRunner(configuration)
    with mock.patch("builtins.input", return_value="", autospec=True) as mock_input:
        runner.run()
    mock_input.assert_called_once_with("Go to dest/ ")


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
