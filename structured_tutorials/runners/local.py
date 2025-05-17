"""Runner for running commands locally."""

import shlex
import subprocess
from typing import Any

from structured_tutorials.models import StepBase
from structured_tutorials.runners.base import RunnerBase, TutorialError


class LocalRunner(RunnerBase):
    """Runner to run commands locally."""

    def run_step(self, step: StepBase, *, context: dict[str, Any]) -> None:
        cmd_str = shlex.join(step.command)
        print(f"+ {cmd_str}")
        proc = subprocess.run(step.command, check=False)
        if proc.returncode != step.returncode:
            raise TutorialError(
                f"{shlex.join(step.command)}: Return code {proc.returncode} (expected: {step.returncode})."
            )
