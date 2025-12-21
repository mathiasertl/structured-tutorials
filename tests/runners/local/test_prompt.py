# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test prompts."""

from unittest import mock
from unittest.mock import call

import pytest

from structured_tutorials.errors import PromptNotConfirmedError
from structured_tutorials.models import TutorialModel
from structured_tutorials.runners.local import LocalTutorialRunner


@pytest.fixture
def runner(runner: LocalTutorialRunner) -> LocalTutorialRunner:
    """Fixture overrides module-level fixture to set interactive mode."""
    runner.interactive = True
    return runner


@pytest.mark.parametrize("answer", ("", "yes", "y", "no", "n", "foobar"))
@pytest.mark.tutorial("prompt-enter")
def test_enter_prompt(runner: LocalTutorialRunner, answer: str) -> None:
    """Run a tutorial with a simple enter-prompt."""
    with mock.patch("builtins.input", return_value=answer, autospec=True) as mock_input:
        runner.run()
    mock_input.assert_called_once_with("example: ")


@pytest.mark.tutorial("prompt-enter")
def test_prompt_with_noninteractive_mode(tutorial: TutorialModel) -> None:
    """Test running a tutorial with a prompt in non-interactive mode - prompt is skipped."""
    runner = LocalTutorialRunner(tutorial=tutorial, interactive=False)
    with mock.patch("builtins.input", return_value="", autospec=True) as mock_input:
        runner.run()
    mock_input.assert_not_called()


@pytest.mark.parametrize("answer", ("", "y", "yes"))
@pytest.mark.tutorial("prompt-confirm")
def test_confirm_prompt_confirms(answer: str, runner: LocalTutorialRunner) -> None:
    """Test confirm prompt where empty answer passes."""
    with mock.patch("builtins.input", return_value=answer, autospec=True) as mock_input:
        runner.run()
    mock_input.assert_called_once_with("example: ")


@pytest.mark.parametrize("answer", ("y", "yes"))
@pytest.mark.tutorial("prompt-confirm-default-false")
def test_confirm_prompt_confirms_with_default_false(answer: str, runner: LocalTutorialRunner) -> None:
    """Test confirm prompt where answer passes with default=False."""
    with mock.patch("builtins.input", return_value=answer, autospec=True) as mock_input:
        runner.run()
    mock_input.assert_called_once_with("example: ")


@pytest.mark.parametrize("answer", ("", "n", "no"))
@pytest.mark.tutorial("prompt-confirm-default-false")
def test_confirm_prompt_does_not_confirm_with_default_false(answer: str, runner: LocalTutorialRunner) -> None:
    """Test confirm prompt where answer does not confirm with default=False."""
    with mock.patch("builtins.input", return_value=answer, autospec=True) as mock_input:
        with pytest.raises(PromptNotConfirmedError, match=r"^State was not confirmed\.$"):
            runner.run()
    mock_input.assert_called_once_with("example: ")


@pytest.mark.tutorial("prompt-confirm-default-false")
def test_confirm_prompt_with_invalid_response(runner: LocalTutorialRunner) -> None:
    """Test confirm prompt where we first give an invalid response."""
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
                    "response": "confirm",
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
