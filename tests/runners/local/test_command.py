# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test commands."""

import io
import os
import subprocess
from pathlib import Path
from unittest import mock

import pytest
from pytest_subprocess import FakeProcess

from structured_tutorials.runners.local import LocalTutorialRunner


@pytest.mark.doc_tutorial("cleanup")
def test_command_cleanup_from_docs(fp: FakeProcess, doc_runner: LocalTutorialRunner) -> None:
    """Test the cleanup from docs."""
    fp.register("mkdir -p /tmp/new-directory")
    fp.register("rm -r /tmp/new-directory")
    doc_runner.run()


@pytest.mark.doc_tutorial("cleanup-multiple")
def test_command_cleanup_from_docs_with_no_errors(fp: FakeProcess, doc_runner: LocalTutorialRunner) -> None:
    """Test the cleanup from docs."""
    fp.register("cmd1")
    fp.register("cmd2")
    fp.register("clean3")
    fp.register("clean1")
    fp.register("clean2")
    doc_runner.run()


@pytest.mark.doc_tutorial("cleanup-multiple")
def test_command_cleanup_from_docs_with_error(
    caplog: pytest.LogCaptureFixture, fp: FakeProcess, doc_runner: LocalTutorialRunner
) -> None:
    """Test the cleanup from docs."""
    fp.register("cmd1", returncode=1)
    fp.register("clean1")
    fp.register("clean2")
    doc_runner.run()
    assert "cmd1 failed with return code 1 (expected: 0)." in caplog.text


@pytest.mark.doc_tutorial("test-command")
def test_test_commands(fp: FakeProcess, doc_runner: LocalTutorialRunner) -> None:
    """Test the cleanup from docs."""
    fp.register("touch test.txt")
    fp.register("test -e test.txt")
    fp.register("rm test.txt")  # cleanup of part 1
    doc_runner.run()


@pytest.mark.tutorial("command-as-list")
def test_command_as_list(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test running a command as list."""
    recorder_main = fp.register(["echo", "word with spaces"])
    recorder_test = fp.register(["ls", "test with spaces"])
    recorder_cleanup = fp.register(["ls", "cleanup with spaces"])
    runner.run()
    expected = {"shell": False, "stdin": None, "stderr": None, "stdout": None}
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


@pytest.mark.tutorial("command-stdin")
def test_command_with_stdin(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test running processes with stdin."""
    stdin_one = b"stdin from yaml file: value"
    stdin_two = b"test: value"

    cat_one = fp.register("cat", stdout=stdin_one)
    cat_two = fp.register("cat", stdout=stdin_two)
    cat_three = fp.register("cat", stdout=b"test: {{ variable }}")
    runner.run()

    assert cat_one.calls[0].kwargs["stdin"] == -1  # type: ignore[index]
    assert cat_two.calls[0].kwargs["stdin"] == -1  # type: ignore[index]
    assert isinstance(cat_three.calls[0].kwargs["stdin"], io.BufferedReader)  # type: ignore[index]


@pytest.mark.tutorial("command-hide-output")
def test_command_hide_output(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test running a commands with hiding the output."""
    # NOTE: output passed to fp.register() does not register in `capsys` fixture
    recorder_main = fp.register("ls main")
    recorder_test = fp.register("ls test")
    recorder_cleanup = fp.register("ls cleanup")
    runner.run()
    expected = {"shell": True, "stdin": None, "stderr": subprocess.DEVNULL, "stdout": subprocess.DEVNULL}
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
    expected = {"shell": True, "stdin": None, "stderr": subprocess.PIPE, "stdout": subprocess.PIPE}
    assert recorder.calls[0].kwargs == expected
    output = capsys.readouterr()
    assert output.out == "--- stdout ---\nfoo bar bla\n--- stderr ---\nfoo bla bla\n"
    assert output.err == ""
    assert runner.context["stdout"] == "bar"
    assert runner.context["stderr"] == "bla"


@pytest.mark.tutorial("command-test-output-count")
def test_command_with_line_and_character_count(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test running a command and testing line/character count."""
    fp.register("echo foo", stdout="foo")
    runner.run()


@pytest.mark.tutorial("command-test-output-count")
def test_command_with_character_count_error(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test running a command that outputs too many characters."""
    fp.register("echo foo", stdout="foobar")
    with pytest.raises(RunTutorialException, match=r"^Character count error: 6, but expected 3\.$"):
        runner.run()


@pytest.mark.tutorial("command-test-output-count")
def test_command_with_line_count_error(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test running a command that outputs too many lines."""
    fp.register("echo foo", stdout="f\nb")
    with pytest.raises(RunTutorialException, match=r"^Line count error: 2, but expected 1\.$"):
        runner.run()


@pytest.mark.tutorial("command-test-output")
def test_command_with_invalid_output(
    caplog: pytest.LogCaptureFixture, fp: FakeProcess, runner: LocalTutorialRunner
) -> None:
    """Test running a commands with capturing the output."""
    fp.register("echo foo bar bla", stdout="wrong output")
    runner.run()
    assert "Process did not have the expected output: 'wrong output'" in caplog.text


@pytest.mark.doc_tutorial("test-command")
def test_test_commands_with_command_error(
    caplog: pytest.LogCaptureFixture, fp: FakeProcess, doc_runner: LocalTutorialRunner
) -> None:
    """Test the cleanup from docs."""
    fp.register("touch test.txt")
    fp.register("test -e test.txt", returncode=1)
    fp.register("rm test.txt")  # cleanup of part 1
    doc_runner.run()
    assert "Test did not pass" in caplog.text


@pytest.mark.tutorial("command-simple")
def test_command_with_error_with_interactive_mode(
    caplog: pytest.LogCaptureFixture, fp: FakeProcess, runner: LocalTutorialRunner
) -> None:
    """Test prompt when an error occurs when interactive mode is enabled."""
    fp.register("ls", returncode=1)
    runner.interactive = True  # force interactive mode
    with mock.patch("builtins.input", return_value="", autospec=True) as mock_input:
        runner.run()
    mock_input.assert_called_once_with(
        "An error occurred while running the tutorial.\n"
        f"Current working directory is {os.getcwd()}\n"
        "\n"
        "Press Enter to continue... "
    )
    assert "ls failed with return code 1 (expected: 0)." in caplog.text


@pytest.mark.doc_tutorial("test-port")
def test_test_commands_with_one_socket_error(fp: FakeProcess, doc_runner: LocalTutorialRunner) -> None:
    """Test the cleanup from docs."""
    fp.register("sleep 3s && ncat -e /bin/cat -k -l 1234 &")
    fp.register("pkill sleep")
    fp.register("pkill ncat")
    with (
        mock.patch("socket.socket", autospec=True) as mock_socket,
        mock.patch("time.sleep", autospec=True) as mock_sleep,
    ):
        connect_mock = mock.MagicMock(side_effect=[Exception("error"), True])
        mock_socket.return_value.connect = connect_mock
        doc_runner.run()

    assert mock_sleep.mock_calls == [mock.call(2), mock.call(1.0)]
    assert connect_mock.mock_calls == [mock.call(("localhost", 1234)), mock.call(("localhost", 1234))]


@pytest.mark.doc_tutorial("test-port")
def test_test_commands_with_socket_error(
    caplog: pytest.LogCaptureFixture, fp: FakeProcess, doc_runner: LocalTutorialRunner
) -> None:
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
        doc_runner.run()
    assert "Test did not pass" in caplog.text

    # 2-second sleep is the initial delay
    assert mock_sleep.mock_calls == [mock.call(2), mock.call(1.0), mock.call(2.0), mock.call(4.0)]
    assert connect_mock.mock_calls == [
        mock.call(("localhost", 1234)),
        mock.call(("localhost", 1234)),
        mock.call(("localhost", 1234)),
        mock.call(("localhost", 1234)),
    ]
