import shlex
import subprocess

from structured_tutorials.models import StepBase
from structured_tutorials.runners.base import RunnerBase


class LocalRunner(RunnerBase):
    def run_step(self, step: StepBase) -> None:
        cmd_str = shlex.join(step.command)
        print(f"+ {cmd_str}")
        proc = subprocess.run(step.command, check=False)
        if proc.returncode != step.returncode:
            raise RuntimeError(
                f"{shlex.join(step.command)}: Return code {proc.returncode} (expected: {step.returncode})."
            )
