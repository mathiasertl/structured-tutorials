# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Base classes for runners."""

import abc
import logging
import shlex
import subprocess
from copy import deepcopy
from subprocess import CompletedProcess
from typing import Any

from jinja2 import Environment

from structured_tutorials.models import AlternativeModel, CleanupCommandModel, TutorialModel

command_logger = logging.getLogger("command")


class RunnerBase(abc.ABC):
    """Base class for runners to provide shared functionality."""

    def __init__(
        self, tutorial: TutorialModel, alternatives: tuple[str, ...] = (), show_command_output: bool = True
    ):
        self.tutorial = tutorial
        self.context = deepcopy(tutorial.configuration.run.context)
        self.env = Environment(keep_trailing_newline=True)
        self.cleanup: list[CleanupCommandModel] = []
        self.alternatives = alternatives
        self.show_command_output = show_command_output

    def render(self, value: str, **context: Any) -> str:
        return self.env.from_string(value).render({**self.context, **context})

    def validate_alternatives(self) -> None:
        """Validate that for each alternative part, an alternative was selected."""
        chosen = set(self.alternatives)

        for part_no, part in enumerate(self.tutorial.parts, start=1):
            if isinstance(part, AlternativeModel):
                selected = chosen & set(part.alternatives)
                print(selected, part.required)
                if part.required and len(selected) == 0:
                    raise ValueError(f"Part {part_no}: No alternative selected.")
                elif len(selected) != 1:
                    raise ValueError(f"Part {part_no}: More then one alternative selected: {selected}")

    def run_shell_command(
        self, command: str | tuple[str], show_output: bool | None = None, capture_output: bool = False
    ) -> CompletedProcess[str]:
        if show_output is None:
            show_output = self.show_command_output

        if capture_output:
            stdout: int | None = subprocess.PIPE
            stderr: int | None = subprocess.PIPE
        elif show_output:
            stdout = stderr = None
        else:
            stdout = stderr = subprocess.DEVNULL

        logged_command = command
        if isinstance(command, str):
            shell = True
            logged_command = command
        else:
            shell = False
            logged_command = shlex.join(logged_command)

        command_logger.info(logged_command)
        proc = subprocess.run(command, shell=shell, stdout=stdout, stderr=stderr, text=True)

        if capture_output and show_output:
            print("--- stdout ---")
            print(proc.stdout)
            print("--- stderr ---")
            print(proc.stderr)

        return proc

    @abc.abstractmethod
    def run(self) -> None:
        """Run the tutorial."""
