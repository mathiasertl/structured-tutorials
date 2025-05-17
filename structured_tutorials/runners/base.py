"""Module for RunnerBase."""

import abc
import copy
from typing import Any

from structured_tutorials.models import Command, CommandBase, File, Tutorial


class TutorialError(Exception):
    """Base class for exceptions."""

    pass


class RunnerBase(abc.ABC):
    """Base class for tutorial runners."""

    def __init__(self, tutorial: Tutorial) -> None:
        self._performed_steps: list[Command | File] = []
        self.tutorial = tutorial

    def run(self) -> None:
        context = copy.deepcopy(self.tutorial.context.execution)
        try:
            for part in self.tutorial.parts:
                for step in part.steps:
                    if isinstance(step, Command):
                        self.run_command(step, context=context)
                    elif isinstance(step, File):
                        self.create_file(step, context=context)
                    else:  # pragma: no cover
                        raise ValueError(f"{step}: Unknown step type.")
                    self._performed_steps.append(step)
        finally:
            for performed_step in reversed(self._performed_steps):
                if isinstance(performed_step, Command):
                    for cleanup_step in performed_step.cleanup:
                        self.run_command(cleanup_step, context=context)

    @abc.abstractmethod
    def run_command(self, command: CommandBase, *, context: dict[str, Any]) -> None: ...

    @abc.abstractmethod
    def create_file(self, file: File, *, context: dict[str, Any]) -> None: ...
