# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Environment-based tests for commands."""

import os

import pytest
from pytest_subprocess import FakeProcess

from structured_tutorials.runners.local import LocalTutorialRunner

ENV = {"ENV_1": "VALUE_1", "ENV_2": "VALUE_2"}


@pytest.fixture
def clear_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixture that clears the entire environment."""
    for key in os.environ:
        monkeypatch.delenv(key, raising=False)
    return


@pytest.fixture
def environment(monkeypatch: pytest.MonkeyPatch, clear_environment: None) -> None:
    """Fixture that returns a controlled environment."""
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    return


@pytest.mark.tutorial("command-simple")
@pytest.mark.usefixtures("environment")
def test_simple_environment(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test a simple environment."""
    recorder = fp.register("ls")
    assert runner.environment == ENV
    runner.run()
    assert recorder.calls[0].kwargs["env"] == ENV


@pytest.mark.tutorial("command-clear-single-environment-variable")
@pytest.mark.usefixtures("environment")
def test_clear_single_environment_variable(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test a simple environment."""
    recorder = fp.register("ls")
    assert runner.environment == {"ENV_2": "VALUE_2"}
    runner.run()
    assert recorder.calls[0].kwargs["env"] == {"ENV_2": "VALUE_2"}


@pytest.mark.tutorial("command-clear-environment-globally")
def test_global_environment(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test a simple environment."""
    assert runner.environment == {}
    recorder1 = fp.register('echo "1: VALUE"', stdout="1: VALUE")
    recorder2 = fp.register('echo "2: $KEY"')
    recorder3 = fp.register('echo "3: $KEY"')
    recorder4 = fp.register('echo "4: $KEY"')
    runner.run()
    assert recorder1.calls[0].kwargs["env"] == {}
    assert recorder2.calls[0].kwargs["env"] == {"KEY": "OTHER VALUE", "KEY2": "VALUE2"}
    assert recorder3.calls[0].kwargs["env"] == {"KEY": "1: VALUE"}
    assert recorder4.calls[0].kwargs["env"] == {}


@pytest.mark.tutorial("command-env-variable-for-single-command")
def test_env_variable_for_single_command(fp: FakeProcess, runner: LocalTutorialRunner) -> None:
    """Test running a commands with environment variables."""
    recorder1 = fp.register("echo 1 $VARIABLE")
    recorder2 = fp.register("echo 2 $VARIABLE")
    runner.run()
    assert recorder1.calls[0].kwargs["env"]["VARIABLE"] == "VALUE 1"  # type: ignore[index]
    assert recorder2.calls[0].kwargs == {
        "shell": True,
        "stdin": None,
        "stderr": None,
        "stdout": None,
        "env": {"VARIABLE": "VALUE 2"},
    }
