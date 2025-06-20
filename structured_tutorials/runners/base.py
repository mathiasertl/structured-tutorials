"""Module for RunnerBase."""

import abc
import copy
import tempfile
from pathlib import Path
from typing import Any

from jinja2 import Environment

from structured_tutorials.models import Command, CommandBase, Commands, File, Tutorial


class TutorialError(Exception):
    """Base class for exceptions."""

    pass


class RunnerBase(abc.ABC):
    """Base class for tutorial runners."""

    def __init__(self, tutorial: Tutorial) -> None:
        self._performed_steps: list[Command | File] = []
        self.tutorial = tutorial
        self.env = Environment(keep_trailing_newline=True)

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

    def render_command(self, args: tuple[str, ...] | str, context: dict[str, Any]) -> tuple[str, ...] | str:
        if isinstance(args, str):
            return self.env.from_string(args).render(context)
        return tuple(self.env.from_string(arg).render(context) for arg in args)

    def handle_command(self, step: Command, context: dict[str, Any]) -> None:
        args = step.command
        if step.exec_command is not None:
            args = step.exec_command

        args = self.render_command(args, context)
        self.run_command(args, step, context=context)

    def handle_command_cleanup(self, step: Command, context: dict[str, Any]) -> None:
        for cleanup_command in step.cleanup:
            args = self.render_command(cleanup_command.command, context)
            self.run_command(args, cleanup_command, context=context)

    def run(self) -> None:
        context = copy.deepcopy(self.tutorial.context.execution)
        context["execution"] = True
        context["documentation"] = False
        try:
            for part in self.tutorial.parts:
                if isinstance(part, File):
                    self.handle_file_step(part, context)
                    self._performed_steps.append(part)
                elif isinstance(part, Commands):
                    for command in part.commands:
                        self.handle_command(command, context)
                        self._performed_steps.append(command)
                else:  # pragma: no cover
                    raise ValueError(f"{part}: Unknown step type.")
        finally:
            for performed_step in reversed(self._performed_steps):
                if isinstance(performed_step, Command):
                    self.handle_command_cleanup(performed_step, context=context)

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
