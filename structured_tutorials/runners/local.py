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
                proc = subprocess.run(command.command, shell=True)
                if proc.returncode != command.run.status_code:
                    raise RuntimeError(
                        f"{command.command} failed with return code {proc.returncode} "
                        f"(expected: {command.run.status_code})."
                    )
