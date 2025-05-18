"""Module for RunnerBase."""

import abc
import copy
import tempfile
from pathlib import Path
from typing import Any

from jinja2 import Environment

from structured_tutorials.models import Command, CommandBase, File, Tutorial


class TutorialError(Exception):
    """Base class for exceptions."""

    pass


class RunnerBase(abc.ABC):
    """Base class for tutorial runners."""

    def __init__(self, tutorial: Tutorial) -> None:
        self._performed_steps: list[Command | File] = []
        self.tutorial = tutorial
        self.env = Environment()

    def handle_file_step(self, step: File, context: dict[str, Any]) -> None:
        source = Path(self.env.from_string(str(step.source)).render(context))
        destination = Path(self.env.from_string(str(step.destination)).render(context))

        if source.is_dir():
            self.copy_directory(source, destination, step, context=context)
        elif step.template is False:
            self.create_file(source, destination, step, context=context)
        else:
            # If the file is a template, render it to a file and pass it instead.
            with open(source) as template_stream:
                template_str = template_stream.read()
            template = self.env.from_string(template_str)
            contents = template.render(context)

            with tempfile.NamedTemporaryFile("w") as tmpfile:
                tmpfile.write(contents)
                tmpfile.flush()

                self.create_file(Path(tmpfile.name), destination, step, context=context)

    def handle_command(self, step: Command, context: dict[str, Any]) -> None:
        if isinstance(step.command, str):
            args = self.env.from_string(step.command).render(context)
        else:
            print(step.command)
            args = tuple(self.env.from_string(arg).render(context) for arg in step.command)
        self.run_command(args, step, context=context)

    def run(self) -> None:
        context = copy.deepcopy(self.tutorial.context.execution)
        try:
            for part in self.tutorial.parts:
                for step in part.steps:
                    if isinstance(step, Command):
                        self.handle_command(step, context)
                    elif isinstance(step, File):
                        self.handle_file_step(step, context)
                    else:  # pragma: no cover
                        raise ValueError(f"{step}: Unknown step type.")
                    self._performed_steps.append(step)
        finally:
            for performed_step in reversed(self._performed_steps):
                if isinstance(performed_step, Command):
                    for cleanup_step in performed_step.cleanup:
                        self.run_command(cleanup_step, context=context)

    @abc.abstractmethod
    def run_command(
        self, args: str | tuple[str, ...], step: CommandBase, *, context: dict[str, Any]
    ) -> None: ...

    @abc.abstractmethod
    def create_file(
        self, source: Path, destination: Path, step: File, *, context: dict[str, Any]
    ) -> None: ...

    @abc.abstractmethod
    def copy_directory(
        self, source: Path, destination: Path, step: File, *, context: dict[str, Any]
    ) -> None: ...
