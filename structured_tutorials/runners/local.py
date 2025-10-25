"""Runner that runs a tutorial on the local machine."""

import socket
import subprocess
import time
from copy import deepcopy

from jinja2 import Environment

from structured_tutorials.models import (
    CleanupCommandSpecification,
    CommandsPartModel,
    TestCommandSpecification,
    TestPortSpecification,
    TutorialModel,
)


class LocalTutorialRunner:
    """Runner implementation that runs a tutorial on the local machine."""

    def __init__(self, tutorial: TutorialModel):
        self.tutorial = tutorial
        self.context = deepcopy(tutorial.configuration.run.context)
        self.env = Environment(keep_trailing_newline=True)
        self.cleanup: list[CleanupCommandSpecification] = []

    def render(self, value: str) -> str:
        return self.env.from_string(value).render(self.context)

    def run_test(self, test: TestCommandSpecification | TestPortSpecification) -> None:
        # If an initial delay is configured, wait that long
        if test.delay > 0:
            time.sleep(test.delay)

        tries = 0
        while tries <= test.retry:
            tries += 1

            if isinstance(test, TestCommandSpecification):
                test_command = self.render(test.command)
                test_proc = subprocess.run(test_command, shell=True)

                if test.status_code == test_proc.returncode:
                    return
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect((test.host, test.port))
                except Exception:
                    pass
                else:
                    return

            wait = test.backoff_factor * (2 ** (tries - 1))
            if wait > 0 and tries <= test.retry:
                time.sleep(wait)

        raise RuntimeError("Test did not pass")

    def run_command(self, part: CommandsPartModel) -> None:
        for command_config in part.commands:
            # Render the command
            command = self.render(command_config.command)

            # Run the command and check status code
            proc = subprocess.run(command, shell=True)

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

            # Run test commands
            for test_command_config in command_config.run.test:
                self.run_test(test_command_config)

    def run_parts(self) -> None:
        for part in self.tutorial.parts:
            if isinstance(part, CommandsPartModel):
                self.run_command(part)
            # elif isinstance(part, FilePartModel):  # pragma: no cover
            #     source = self.tutorial.path.parent / part.source
            #     print(source)
            else:  # pragma: no cover
                raise RuntimeError(f"{part} is not a tutorial part")

    def run(self) -> None:
        try:
            self.run_parts()
        finally:
            for command_config in self.cleanup:
                command = self.env.from_string(command_config.command).render(self.context)
                subprocess.run(command, shell=True)
