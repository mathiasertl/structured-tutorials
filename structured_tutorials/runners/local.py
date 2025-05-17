"""Runner that runs a tutorial on the local machine."""

import subprocess

from structured_tutorials.models import TutorialModel


class LocalTutorialRunner:
    """Runner implementation that runs a tutorial on the local machine."""

    def __init__(self, configuration: TutorialModel):
        self.configuration = configuration

    def run(self) -> None:
        for part in self.configuration.parts:
            for command in part.commands:
                subprocess.run(command.command, shell=True)
