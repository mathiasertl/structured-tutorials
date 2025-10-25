"""Runner that runs a tutorial on the local machine."""

import subprocess
from copy import deepcopy

from jinja2 import Environment

from structured_tutorials.models import CleanupCommandSpecification, CommandsPartModel, TutorialModel


class LocalTutorialRunner:
    """Runner implementation that runs a tutorial on the local machine."""

    def __init__(self, tutorial: TutorialModel):
        self.tutorial = tutorial
        self.context = deepcopy(tutorial.configuration.run.context)
        self.env = Environment(keep_trailing_newline=True)
        self.cleanup: list[CleanupCommandSpecification] = []

    def render(self, value: str) -> str:
        return self.env.from_string(value).render(self.context)

    def run_parts(self) -> None:
        for part in self.tutorial.parts:
            if isinstance(part, CommandsPartModel):
                for command_config in part.commands:
                    # Render the command
                    command = self.env.from_string(command_config.command).render(self.context)

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
