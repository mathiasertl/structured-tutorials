"""Runner for running steps locally."""

import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from structured_tutorials.models import CommandBase, File
from structured_tutorials.runners.base import RunnerBase, TutorialError


class LocalRunner(RunnerBase):
    """Runner to run steps locally."""

    def run_command(self, args: str | tuple[str], step: CommandBase, *, context: dict[str, Any]) -> None:
        if isinstance(args, str):
            cmd_str = args
        else:
            cmd_str = shlex.join(args)
        print(f"+ {cmd_str}")

        proc = subprocess.run(args, shell=step.shell, check=False)
        if step.returncode is not None and proc.returncode != step.returncode:
            raise TutorialError(f"{cmd_str}: Return code {proc.returncode} (expected: {step.returncode}).")

    def create_file(self, source: Path, destination: Path, step: File, *, context: dict[str, Any]) -> None:
        destination.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy2(source, destination)

    def copy_directory(self, source: Path, destination: Path, step: File, *, context: dict[str, Any]) -> None:
        raise NotImplementedError
