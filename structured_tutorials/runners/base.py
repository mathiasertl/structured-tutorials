"""Module for RunnerBase."""

import abc
import copy
from typing import Any

from structured_tutorials.models import Command, CommandBase, Tutorial


class TutorialError(Exception):
    """Base class for exceptions."""

    pass


class RunnerBase(abc.ABC):
    """Base class for tutorial runners."""

    def __init__(self, tutorial: Tutorial) -> None:
        self._performed_steps: list[Command] = []
        self.tutorial = tutorial

    def run(self) -> None:
        context = copy.deepcopy(self.tutorial.context.execution)
        try:
            for part in self.tutorial.parts:
                for step in part.commands:
                    self.run_step(step, context=context)
                    self._performed_steps.append(step)
        finally:
            for performed_step in reversed(self._performed_steps):
                for cleanup_step in performed_step.cleanup:
                    print(cleanup_step)
                    self.run_step(cleanup_step, context=context)

    @abc.abstractmethod
    def run_step(self, step: CommandBase, *, context: dict[str, Any]) -> None: ...
