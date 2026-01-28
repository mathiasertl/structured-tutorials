# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Base classes for runners."""

import abc
import io
import logging
import os
import shlex
import subprocess
import sys
from copy import deepcopy
from subprocess import CompletedProcess
from typing import Any

from jinja2 import Environment

from structured_tutorials.errors import CommandOutputTestError, InvalidAlternativesSelectedError
from structured_tutorials.models import AlternativeModel, TutorialModel
from structured_tutorials.models.base import CommandType
from structured_tutorials.models.parts import CleanupCommandModel
from structured_tutorials.models.tests import TestOutputModel
from structured_tutorials.utils import check_count

command_logger = logging.getLogger("command")


class RunnerBase(abc.ABC):
    """Base class for runners to provide shared functionality."""

    def __init__(
        self,
        tutorial: TutorialModel,
        alternatives: tuple[str, ...] = (),
        show_command_output: bool = True,
        interactive: bool = True,
        context: dict[str, Any] | None = None,
    ):
        self.tutorial = tutorial

        # Create Jinja2 environment for rendering templates
        self.env = Environment(keep_trailing_newline=True)

        # Compute initial context
        self.context = deepcopy(tutorial.configuration.context)
        self.context.update(deepcopy(tutorial.configuration.run.context))
        if context:
            self.context.update(context)

        # Set up the environment for commands
        if tutorial.configuration.run.clear_environment:
            self.environment = {}
        else:
            self.environment = os.environ.copy()
        self.environment.update(tutorial.configuration.run.environment)  # type: ignore[arg-type]  # temporary
        self.environment = {k: self.render(v) for k, v in self.environment.items() if v is not None}

        # Handle alternatives
        self.alternatives = alternatives
        for alternative in alternatives:
            if config := tutorial.configuration.run.alternatives.get(alternative):
                self.environment.update(config.environment)
                self.context.update(config.context)

        self.cleanup: list[CleanupCommandModel] = []
        self.show_command_output = show_command_output
        self.interactive = interactive

    def render(self, value: str, **context: Any) -> str:
        return self.env.from_string(value).render({**self.context, **context})

    def render_command(self, command: CommandType, **context: Any) -> CommandType:
        if isinstance(command, str):
            return self.render(command)

        return tuple(self.render(token) for token in command)

    def test_output(self, proc: subprocess.CompletedProcess[bytes], test: TestOutputModel) -> None:
        if test.stream == "stderr":
            value = proc.stderr
        else:
            value = proc.stdout

        if test.regex:
            if (match := test.regex.search(value)) is not None:
                self.context.update({k: v.decode("utf-8") for k, v in match.groupdict().items()})
            else:
                decoded = value.decode("utf-8")
                raise CommandOutputTestError(f"Process did not have the expected output: '{decoded}'")

        # Test for line/character count of output
        if test.line_count:
            try:
                check_count(value.splitlines(), test.line_count)
            except ValueError as ex:
                raise CommandOutputTestError(f"Line count error: {ex}") from ex
        if test.character_count:
            try:
                check_count(value, test.character_count)
            except ValueError as ex:
                raise CommandOutputTestError(f"Character count error: {ex}") from ex

    def validate_alternatives(self) -> None:
        """Validate that for each alternative part, an alternative was selected."""
        chosen = set(self.alternatives)

        for part_no, part in enumerate(self.tutorial.parts, start=1):
            if isinstance(part, AlternativeModel):
                selected = chosen & set(part.alternatives)

                if part.required and len(selected) == 0:
                    raise InvalidAlternativesSelectedError(f"Part {part_no}: No alternative selected.")
                elif len(selected) != 1:
                    raise InvalidAlternativesSelectedError(
                        f"Part {part_no}: More then one alternative selected: {selected}"
                    )

    def run_shell_command(
        self,
        command: CommandType,
        show_output: bool,
        capture_output: bool = False,
        stdin: int | io.BufferedReader | None = None,
        input: bytes | None = None,
        environment: dict[str, Any] | None = None,
        clear_environment: bool = False,
    ) -> CompletedProcess[bytes]:
        # Only show output if runner itself is not configured to hide all output
        if show_output:
            show_output = self.show_command_output

        # Configure stdout/stderr streams
        if capture_output:
            stdout: int | None = subprocess.PIPE
            stderr: int | None = subprocess.PIPE
        elif show_output:
            stdout = stderr = None
        else:
            stdout = stderr = subprocess.DEVNULL

        # Configure environment
        if environment:
            # If environment is passed, we render variables as templates
            environment = {k: self.render(v) for k, v in environment.items()}
        elif environment is None:  # pragma: no cover  # dict is always passed directly
            # just to simplify the next branch -> environment is always a dict
            environment = {}
        if clear_environment:
            env = environment
        elif environment:
            env = {**self.environment, **environment}
        else:
            env = self.environment

        # Render the command (args) as template
        command = self.render_command(command)

        shell = True
        logged_command = command  # The command string we pass to the logger
        if isinstance(command, tuple):
            shell = False
            logged_command = shlex.join(logged_command)

        command_logger.info(logged_command)
        proc = subprocess.run(
            command, shell=shell, stdin=stdin, input=input, stdout=stdout, stderr=stderr, env=env
        )

        # If we want to show the output and capture it at the same time, we need can only show the streams
        # separately at the end.
        if capture_output and show_output:
            print("--- stdout ---")
            sys.stdout.buffer.write(proc.stdout + b"\n")
            sys.stdout.buffer.flush()
            print("--- stderr ---")
            sys.stdout.buffer.write(proc.stderr + b"\n")
            sys.stdout.buffer.flush()

        return proc

    @abc.abstractmethod
    def run(self) -> None:
        """Run the tutorial."""
