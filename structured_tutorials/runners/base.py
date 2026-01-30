# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Base classes for runners."""

import abc
import io
import logging
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any

from jinja2 import Environment

from structured_tutorials.errors import (
    CommandOutputTestError,
    InvalidAlternativesSelectedError,
    PromptNotConfirmedError,
    RequiredExecutableNotFoundError,
)
from structured_tutorials.models import (
    AlternativeModel,
    CommandsPartModel,
    FilePartModel,
    PromptModel,
    TutorialModel,
)
from structured_tutorials.models.base import CommandType
from structured_tutorials.models.parts import CleanupCommandModel
from structured_tutorials.models.tests import TestOutputModel
from structured_tutorials.utils import chdir, check_count, cleanup, git_export

log = logging.getLogger(__name__)
command_logger = logging.getLogger("command")
part_log = logging.getLogger("part")


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
            environment: dict[str, str | None] = {}
        else:
            environment = os.environ.copy()  # type: ignore[assignment]
        environment.update(tutorial.configuration.run.environment)

        # Check for required executables
        for executable in tutorial.configuration.run.required_executables:
            if not shutil.which(executable, path=environment.get("PATH")):
                raise RequiredExecutableNotFoundError(f"{executable}: Executable not found.")

        # Handle alternatives
        self.alternatives = alternatives
        for alternative in alternatives:
            if config := tutorial.configuration.run.alternatives.get(alternative):
                environment.update(config.environment)
                self.context.update(config.context)

                for executable in config.required_executables:
                    if not shutil.which(executable, path=environment.get("PATH")):
                        raise RequiredExecutableNotFoundError(f"{executable}: Executable not found.")

        self.cleanup: list[CleanupCommandModel] = []
        self.show_command_output = show_command_output
        self.interactive = interactive

        self.environment = {k: self.render(v) for k, v in environment.items() if v is not None}

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

    def run_prompt(self, part: PromptModel) -> None:
        prompt = self.render(part.prompt).strip() + " "

        if part.response == "enter":
            input(prompt)
        else:  # type == confirm
            valid_inputs = ("n", "no", "yes", "y", "")
            while (response := input(prompt).strip().lower()) not in valid_inputs:
                print(f"Please enter a valid value ({'/'.join(valid_inputs)}).")

            if response in ("n", "no") or (response == "" and not part.default):
                error = self.render(part.error, response=response)
                raise PromptNotConfirmedError(error)

    def run_alternative(self, part: AlternativeModel) -> None:
        selected = set(self.alternatives) & set(part.alternatives)

        # Note: The CLI agent already verifies this - just assert this to be sure.
        assert len(selected) <= 1, "More then one part selected."

        if selected:
            selected_part = part.alternatives[next(iter(selected))]
            if isinstance(selected_part, CommandsPartModel):
                self.run_commands(selected_part)
            elif isinstance(selected_part, FilePartModel):
                self.write_file(selected_part)
            else:  # pragma: no cover
                raise RuntimeError(f"{selected_part} is not supported as alternative.")

    def run_parts(self) -> None:
        for part in self.tutorial.parts:
            if isinstance(part, PromptModel):
                if self.interactive:
                    self.run_prompt(part)
                continue
            if part.run.skip:
                continue

            if part.name:  # pragma: no cover
                part_log.info(part.name)
            else:
                part_log.info(f"Running part {part.id}...")

            if isinstance(part, CommandsPartModel):
                self.run_commands(part)
            elif isinstance(part, FilePartModel):
                self.write_file(part)
            elif isinstance(part, AlternativeModel):
                self.run_alternative(part)
            else:  # pragma: no cover
                raise RuntimeError(f"{part} is not a tutorial part")

            self.context.update(part.run.update_context)

    def run(self) -> None:
        if self.tutorial.configuration.run.temporary_directory:
            with tempfile.TemporaryDirectory() as tmpdir_name:
                log.info("Switching to temporary directory: %s", tmpdir_name)
                self.context["cwd"] = self.context["temp_dir"] = Path(tmpdir_name)
                self.context["orig_cwd"] = Path.cwd()

                with chdir(tmpdir_name), cleanup(self):
                    self.run_parts()
        elif self.tutorial.configuration.run.git_export:
            with tempfile.TemporaryDirectory() as tmpdir_name:
                work_dir = git_export(tmpdir_name)
                log.info("Creating git export at: %s", work_dir)
                self.context["cwd"] = self.context["export_dir"] = work_dir
                self.context["orig_cwd"] = Path.cwd()

                with chdir(work_dir), cleanup(self):
                    self.run_parts()
        else:
            with cleanup(self):
                self.run_parts()

    @abc.abstractmethod
    def run_commands(self, part: CommandsPartModel) -> None: ...

    @abc.abstractmethod
    def write_file(self, part: FilePartModel) -> None: ...
