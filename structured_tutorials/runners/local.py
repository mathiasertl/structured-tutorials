# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Runner that runs a tutorial on the local machine."""

import logging
import os
import shlex
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

from structured_tutorials.errors import CommandOutputTestError, CommandTestError, PromptNotConfirmedError
from structured_tutorials.models.parts import AlternativeModel, CommandsPartModel, FilePartModel, PromptModel
from structured_tutorials.models.tests import TestCommandModel, TestOutputModel, TestPortModel
from structured_tutorials.runners.base import RunnerBase
from structured_tutorials.utils import chdir, cleanup, git_export

log = logging.getLogger(__name__)
part_log = logging.getLogger("part")


class LocalTutorialRunner(RunnerBase):
    """Runner implementation that runs a tutorial on the local machine."""

    def run_test(
        self, test: TestCommandModel | TestPortModel | TestOutputModel, proc: subprocess.CompletedProcess[str]
    ) -> None:
        # If the test is for an output stream, we can run it right away (the process has already finished).
        if isinstance(test, TestOutputModel):
            if test.stream == "stderr":
                value = proc.stderr
            else:
                value = proc.stdout

            if (match := test.regex.search(value)) is not None:
                self.context.update(match.groupdict())
                return
            else:
                raise CommandOutputTestError(f"Process did not have the expected output: '{value}'")

        # If an initial delay is configured, wait that long
        if test.delay > 0:
            time.sleep(test.delay)

        tries = 0
        while tries <= test.retry:
            tries += 1

            if isinstance(test, TestCommandModel):
                test_proc = self.run_shell_command(test.command, show_output=test.show_output)

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

            # Run the command and check status code
            proc = self.run_shell_command(
                command_config.command,
                show_output=command_config.run.show_output,
                capture_output=capture_output,
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

            if command_config.run.chdir is not None:
                log.info("Changing working directory to %s.", command_config.run.chdir)
                os.chdir(command_config.run.chdir)

            # Run test commands
            for test_command_config in command_config.run.test:
                self.run_test(test_command_config, proc)

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
        for part_no, part in enumerate(self.tutorial.parts, start=1):
            part_log.info(f"Running part {part_no}...")
            if isinstance(part, PromptModel):
                if self.interactive:
                    self.run_prompt(part)
                continue

            if part.run.skip:
                continue

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
