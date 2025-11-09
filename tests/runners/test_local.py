"""Test local runner."""

from pathlib import Path
from unittest import mock

import pytest
from pytest_subprocess import FakeProcess

from structured_tutorials.models import TutorialModel
from structured_tutorials.runners.local import LocalTutorialRunner
from tests.conftest import DOCS_TUTORIALS_DIR, TEST_TUTORIALS_DIR


def test_simple_tutorial(simple_tutorial: TutorialModel) -> None:
    """Test the local runner by running a simple tutorial."""
    runner = LocalTutorialRunner(simple_tutorial)
    runner.run()


def test_exit_code_tutorial(fp: FakeProcess) -> None:
    """Test status code specification."""
    fp.register(["true"])
    fp.register(["true"])
    fp.register(["false"], returncode=1)
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "exit_code" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    runner.run()


def test_exit_code_tutorial_with_unexpected_exit_code(fp: FakeProcess) -> None:
    """Test behavior if a command has the wrong status code."""
    fp.register(["true"])
    fp.register(["true"], returncode=1)
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "exit_code" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    with pytest.raises(RuntimeError, match=r"true failed with return code 1 \(expected: 0\)\.$"):
        runner.run()


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


def test_command_cleanup_from_docs_with_error(fp: FakeProcess) -> None:
    """Test the cleanup from docs."""
    fp.register("cmd1", returncode=1)
    fp.register("clean1")
    fp.register("clean2")
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "cleanup-multiple" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    with pytest.raises(RuntimeError, match=r"cmd1 failed with return code 1 \(expected: 0\)\.$"):
        runner.run()


def test_test_commands(fp: FakeProcess) -> None:
    """Test the cleanup from docs."""
    fp.register("touch test.txt")
    fp.register("test -e test.txt")
    fp.register("which ncat")
    fp.register("sleep 3s && ncat -e /bin/cat -k -l 1234 &")
    fp.register("pkill sleep")
    fp.register("pkill ncat")
    fp.register("rm test.txt")  # cleanup of part 1
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "test-command" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    with (
        mock.patch("socket.socket", autospec=True) as mock_socket,
        mock.patch("time.sleep", autospec=True) as mock_sleep,
    ):
        connect_mock = mock.MagicMock()
        mock_socket.return_value.connect = connect_mock
        runner.run()

    mock_sleep.assert_called_once_with(2)
    connect_mock.assert_called_once_with(("localhost", 1234))


def test_test_commands_with_command_error(fp: FakeProcess) -> None:
    """Test the cleanup from docs."""
    fp.register("touch test.txt")
    fp.register("test -e test.txt", returncode=1)
    fp.register("rm test.txt")  # cleanup of part 1
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "test-command" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    with pytest.raises(RuntimeError, match=r"^Test did not pass$"):
        runner.run()


def test_test_commands_with_one_socket_error(fp: FakeProcess) -> None:
    """Test the cleanup from docs."""
    fp.register("touch test.txt")
    fp.register("test -e test.txt")
    fp.register("which ncat")
    fp.register("sleep 3s && ncat -e /bin/cat -k -l 1234 &")
    fp.register("pkill sleep")
    fp.register("pkill ncat")
    fp.register("rm test.txt")  # cleanup of part 1
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "test-command" / "tutorial.yaml")
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


def test_test_commands_with_socket_error(fp: FakeProcess) -> None:
    """Test the cleanup from docs."""
    fp.register("touch test.txt")
    fp.register("test -e test.txt")
    fp.register("which ncat")
    fp.register("sleep 3s && ncat -e /bin/cat -k -l 1234 &")
    fp.register("pkill sleep")
    fp.register("pkill ncat")
    fp.register("rm test.txt")  # cleanup of part 1
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "test-command" / "tutorial.yaml")
    runner = LocalTutorialRunner(configuration)
    with (
        mock.patch("socket.socket", autospec=True) as mock_socket,
        mock.patch("time.sleep", autospec=True) as mock_sleep,
    ):
        connect_mock = mock.MagicMock(side_effect=Exception("error"))
        mock_socket.return_value.connect = connect_mock
        with pytest.raises(RuntimeError, match=r"^Test did not pass$"):
            runner.run()

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


def test_file_copy(tmp_path: Path) -> None:
    """Test skipping a part when running."""
    configuration = TutorialModel.from_file(DOCS_TUTORIALS_DIR / "file-copy" / "tutorial.yaml")
    # Update destination to copy to tmp_path
    for part in configuration.parts:
        part.destination = str(tmp_path) + part.destination
    runner = LocalTutorialRunner(configuration)
    runner.run()

    assert Path(configuration.parts[0].destination).exists()
    with open(configuration.parts[0].destination) as stream:
        assert stream.read() == "inline contents: at runtime"

    assert Path(configuration.parts[1].destination).exists()
    with open(configuration.parts[1].destination) as stream:
        assert stream.read() == "inline contents: {{ variable }}"

    assert Path(configuration.parts[2].destination).exists()
    with open(configuration.parts[2].destination) as stream:
        assert stream.read() == "test: at runtime"

    assert Path(configuration.parts[3].destination).exists()
    with open(configuration.parts[3].destination) as stream:
        assert stream.read() == "test: {{ variable }}"

    destination = Path(configuration.parts[4].destination) / "file_contents.txt"
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
    runner = LocalTutorialRunner(configuration)
    with pytest.raises(RuntimeError, match=rf"^{dest}: Destination already exists\.$"):
        runner.run()

    with open(dest) as stream:
        assert stream.read() == "foo"
