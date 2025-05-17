"""Runner for running commands locally."""

import shlex
import subprocess
from typing import Any

from structured_tutorials.models import CommandBase, File
from structured_tutorials.runners.base import RunnerBase, TutorialError


class LocalRunner(RunnerBase):
    """Runner to run commands locally."""

    def run_command(self, command: CommandBase, *, context: dict[str, Any]) -> None:
        cmd_str = shlex.join(command.command)
        print(f"+ {cmd_str}")
        proc = subprocess.run(command.command, check=False)
        if proc.returncode != command.returncode:
            raise TutorialError(f"{cmd_str}: Return code {proc.returncode} (expected: {command.returncode}).")

    def create_file(self, file: File, *, context: dict[str, Any]) -> None:
        pass
