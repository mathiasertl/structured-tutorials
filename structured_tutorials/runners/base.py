# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Base classes for runners."""

import abc
import io
import logging
import os
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from copy import deepcopy
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any

from jinja2 import Environment

from structured_tutorials.errors import (
    CommandOutputTestError,
    CommandTestError,
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
from structured_tutorials.models.parts import CleanupCommandModel, CommandModel
from structured_tutorials.models.tests import TestCommandModel, TestOutputModel, TestPortModel
from structured_tutorials.utils import chdir, check_count, cleanup, git_export

log = logging.getLogger(__name__)
command_logger = logging.getLogger("command")
part_log = logging.getLogger("part")


class RunnerBase(abc.ABC):
    """Base class for runners to provide shared functionality."""

    def __init__(
        self,
        tutorial: TutorialModel,
        path: Path | None = None,
        alternatives: tuple[str, ...] = (),
        show_command_output: bool = True,
        interactive: bool = True,
        context: dict[str, Any] | None = None,
    ):
        self.path = path
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
            return self.render(command, **context)

        return tuple(self.render(token, **context) for token in command)

    def test_output(self, proc: subprocess.CompletedProcess[bytes], test: TestOutputModel) -> None:
        if test.stream == "stderr":
            value = proc.stderr
        else:
            value = proc.stdout
        if test.strip:
            value = value.strip()

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
                elif len(selected) > 1:
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
        options: dict[str, Any] | None = None,
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

    def run_commands(self, part: CommandsPartModel, options: dict[str, Any] | None = None) -> None:
        assert part.run is not False  # Already checked by the caller
        if options is None:
            options = {}
        options = {**options, **part.run.options}

        for command_config in part.commands:
            if command_config.run is False:
                continue

            self.run_command(command_config, options)

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
        assert part.run is not False  # Already checked by the caller
        selected = set(self.alternatives) & set(part.alternatives)

        # Note: The CLI agent already verifies this - just assert this to be sure.
        assert len(selected) <= 1, "More then one part selected."
        options = part.run.options

        if selected:
            selected_part = part.alternatives[next(iter(selected))]
            if isinstance(selected_part, CommandsPartModel):
                self.run_commands(selected_part, options)
            elif isinstance(selected_part, FilePartModel):
                self.write_file(selected_part, options)
            else:  # pragma: no cover
                raise RuntimeError(f"{selected_part} is not supported as alternative.")

    def run_parts(self) -> None:
        for part in self.tutorial.parts:
            if isinstance(part, PromptModel):
                if self.interactive:
                    self.run_prompt(part)
                continue
            if part.run is False:
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

    def prepare_tutorial(self) -> None:
        """Function invoked before running the tutorial."""
        return

    def cleanup_tutorial(self) -> None:
        """Function invoked after running the tutorial."""
        return

    def update_environment_variable(self, key: str, value: str, options: dict[str, Any]) -> None:
        """Set an environment variable."""
        self.environment[key] = value

    def update_environment(self, env: dict[str, str], options: dict[str, Any]) -> None:
        env = {k: self.render(v) for k, v in env.items() if v is not None}
        for key, value in env.items():
            self.update_environment_variable(key, value, options)

    def write_file(self, part: FilePartModel, options: dict[str, Any] | None = None) -> None:
        """Write a file."""
        assert part.run is not False  # Already checked by the caller
        if options is None:
            options = {}
        options = {**options, **part.run.options}

        raw_destination = self.render(part.destination)
        destination = Path(raw_destination)

        if raw_destination.endswith(os.path.sep):
            # Model validation already validates that the destination does not look like a directory, if no
            # source is set, but this could be tricked if the destination is a template.
            if not part.source:
                raise RuntimeError(
                    f"{raw_destination}: Destination is directory, but no source given to derive filename."
                )

            destination.mkdir(parents=True, exist_ok=True)
            destination = destination / part.source.name
        elif destination.exists():
            raise RuntimeError(f"{destination}: Destination already exists.")

        # If template=False and source is set, we just copy the file as is, without ever reading it
        if not part.template and part.source:
            self.copy_file(self.tutorial.root / part.source, destination, options)
            return

        if part.source:
            with open(self.tutorial.root / part.source) as source_stream:
                template = source_stream.read()
        else:
            assert isinstance(part.contents, str)  # assured by model validation
            template = part.contents

        if part.template:
            contents = self.render(template)
        else:
            contents = template

        self.write_file_from_string(contents, destination, options)

    def run_test(
        self,
        test: TestCommandModel | TestPortModel | TestOutputModel,
        proc: subprocess.CompletedProcess[bytes],
        options: dict[str, Any],
    ) -> None:
        # If the test is for an output stream, we can run it right away (the process has already finished).
        if isinstance(test, TestOutputModel):
            self.test_output(proc, test)
            return

        # If an initial delay is configured, wait that long
        if test.delay > 0:
            time.sleep(test.delay)

        tries = 0
        while tries <= test.retry:
            tries += 1

            if isinstance(test, TestCommandModel):
                test_proc = self.run_shell_command(
                    test.command,
                    show_output=test.show_output,
                    environment=test.environment,
                    clear_environment=test.clear_environment,
                    options=options,
                )

                # Update environment regardless of success of command
                self.update_environment(test.update_environment, options)

                if test.status_code == test_proc.returncode:
                    return
                else:
                    log.error("%s: Test command failed.", shlex.join(test_proc.args))
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect((test.host, test.port))
                except Exception:
                    log.error("%s:%s: failed to connect.", test.host, test.port)
                else:
                    return

            wait = test.backoff_factor * (2 ** (tries - 1))
            if wait > 0 and tries <= test.retry:
                time.sleep(wait)

        raise CommandTestError("Test did not pass")

    def run_command(self, config: CommandModel, options: dict[str, Any]) -> None:
        assert config.run is not False  # Already checked by the caller
        # Capture output if any test is for the output.
        capture_output = any(isinstance(test, TestOutputModel) for test in config.run.test)
        options = {**options, **config.run.options}

        # Run the command and check status code
        if config.run.stdin and config.run.stdin.source and not config.run.stdin.template:
            with open(self.tutorial.root / config.run.stdin.source, "rb") as stdin:
                proc = self.run_shell_command(
                    config.command,
                    show_output=config.run.show_output,
                    capture_output=capture_output,
                    stdin=stdin,
                    environment=config.run.environment,
                    clear_environment=config.run.clear_environment,
                    options=options,
                )
        else:
            # Configure stdin
            proc_input = None
            if stdin_config := config.run.stdin:
                if stdin_config.contents:
                    proc_input = self.render(stdin_config.contents).encode("utf-8")
                elif stdin_config.template:  # source path, but template=True
                    assert stdin_config.source is not None
                    with open(self.tutorial.root / stdin_config.source) as stream:
                        stdin_template = stream.read()
                    proc_input = self.render(stdin_template).encode("utf-8")

                else:  # pragma: no cover
                    raise RuntimeError("Invalid configuration.")

            proc = self.run_shell_command(
                config.command,
                show_output=config.run.show_output,
                capture_output=capture_output,
                input=proc_input,
                environment=config.run.environment,
                clear_environment=config.run.clear_environment,
                options=options,
            )

        # Update list of cleanup commands
        self.cleanup = list(config.run.cleanup) + self.cleanup

        # Handle errors in commands
        if proc.returncode != config.run.status_code:
            raise RuntimeError(
                f"{config.command} failed with return code {proc.returncode} "
                f"(expected: {config.run.status_code})."
            )

        # Update the context from update_context
        self.context.update(config.run.update_context)

        if (command_chdir := config.chdir) is not None:
            rendered_command_chdir = self.render(str(command_chdir))
            log.info("Changing working directory to %s.", rendered_command_chdir)
            self.chdir(rendered_command_chdir, options)

        # Run test commands
        for test_command_config in config.run.test:
            self.run_test(test_command_config, proc, options)

        # Update environment (after test commands - they may update the context)
        self.update_environment(config.run.update_environment, options)

    @abc.abstractmethod
    def chdir(self, path: str, options: dict[str, Any]) -> None: ...

    @abc.abstractmethod
    def copy_file(self, source: Path, destination: Path, options: dict[str, Any]) -> None: ...

    @abc.abstractmethod
    def write_file_from_string(self, contents: str, destination: Path, options: dict[str, Any]) -> None: ...
