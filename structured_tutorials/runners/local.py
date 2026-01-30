# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Runner that runs a tutorial on the local machine."""

import logging
import os
import shlex
import shutil
import socket
import subprocess
import time
from pathlib import Path

from structured_tutorials.errors import CommandTestError
from structured_tutorials.models.parts import CommandsPartModel, FilePartModel
from structured_tutorials.models.tests import TestCommandModel, TestOutputModel, TestPortModel
from structured_tutorials.runners.base import RunnerBase

log = logging.getLogger(__name__)


class LocalTutorialRunner(RunnerBase):
    """Runner implementation that runs a tutorial on the local machine."""

    def run_test(
        self,
        test: TestCommandModel | TestPortModel | TestOutputModel,
        proc: subprocess.CompletedProcess[bytes],
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
                )

                # Update environment regardless of success of command
                self.environment.update({k: self.render(v) for k, v in test.update_environment.items()})

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

    def run_commands(self, part: CommandsPartModel) -> None:
        for command_config in part.commands:
            if command_config.run.skip:
                continue

            # Capture output if any test is for the output.
            capture_output = any(isinstance(test, TestOutputModel) for test in command_config.run.test)

            proc_input = None
            if stdin_config := command_config.run.stdin:
                if stdin_config.contents:
                    proc_input = self.render(stdin_config.contents).encode("utf-8")
                elif stdin_config.template:  # source path, but template=True
                    assert stdin_config.source is not None
                    with open(self.tutorial.tutorial_root / stdin_config.source) as stream:
                        stdin_template = stream.read()
                    proc_input = self.render(stdin_template).encode("utf-8")

            # Run the command and check status code
            if (
                command_config.run.stdin
                and command_config.run.stdin.source
                and not command_config.run.stdin.template
            ):
                with open(self.tutorial.tutorial_root / command_config.run.stdin.source, "rb") as stdin:
                    proc = self.run_shell_command(
                        command_config.command,
                        show_output=command_config.run.show_output,
                        capture_output=capture_output,
                        stdin=stdin,
                        environment=command_config.run.environment,
                        clear_environment=command_config.run.clear_environment,
                    )
            else:
                proc = self.run_shell_command(
                    command_config.command,
                    show_output=command_config.run.show_output,
                    capture_output=capture_output,
                    input=proc_input,
                    environment=command_config.run.environment,
                    clear_environment=command_config.run.clear_environment,
                )

            # Update list of cleanup commands
            self.cleanup = list(command_config.run.cleanup) + self.cleanup

            # Handle errors in commands
            if proc.returncode != command_config.run.status_code:
                raise RuntimeError(
                    f"{command_config.command} failed with return code {proc.returncode} "
                    f"(expected: {command_config.run.status_code})."
                )

            # Update the context from update_context
            self.context.update(command_config.run.update_context)

            if (command_chdir := command_config.run.chdir) is not None:
                rendered_command_chdir = self.render(str(command_chdir))
                rendered_command_chdir = self.render(str(command_chdir))
                log.info("Changing working directory to %s.", command_chdir)
                os.chdir(rendered_command_chdir)

            # Run test commands
            for test_command_config in command_config.run.test:
                self.run_test(test_command_config, proc)

            # Update environment (after test commands - they may update the context)
            self.environment.update(
                {k: self.render(v) for k, v in command_config.run.update_environment.items()}
            )

    def write_file(self, part: FilePartModel) -> None:
        """Write a file."""
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

        # Create any parent directories
        destination.parent.mkdir(parents=True, exist_ok=True)

        # If template=False and source is set, we just copy the file as is, without ever reading it
        if not part.template and part.source:
            shutil.copy(part.source, destination)
            return

        if part.source:
            with open(self.tutorial.tutorial_root / part.source) as source_stream:
                template = source_stream.read()
        else:
            assert isinstance(part.contents, str)  # assured by model validation
            template = part.contents

        if part.template:
            contents = self.render(template)
        else:
            contents = template

        with open(destination, "w") as destination_stream:
            destination_stream.write(contents)
