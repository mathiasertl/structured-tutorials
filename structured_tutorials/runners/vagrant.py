# Copyright (c) 2026 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Class for running the VagrantRunner."""

import io
import logging
import os.path
import shlex
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any

from pydantic import BaseModel, Field

from structured_tutorials.errors import (
    ConfigurationException,
    RequiredExecutableNotFoundError,
    RunTutorialException,
)
from structured_tutorials.models.base import CommandType
from structured_tutorials.models.types import RelativePath
from structured_tutorials.runners.base import RunnerBase

log = logging.getLogger(__name__)
command_logger = logging.getLogger("command")


class PrepareBoxOptions(BaseModel):
    """Options for preparing a box."""

    name: str
    cwd: RelativePath


class VagrantOptions(BaseModel):
    """Options for running vagrant."""

    environment: dict[str, Any] = Field(default_factory=dict)
    cwds: dict[str, str] = Field(default_factory=dict)
    prepare_box: PrepareBoxOptions | None = None


class VagrantRunner(RunnerBase):
    """Runner to run Vagrant tutorials."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Check if vagrant is installed
        if not shutil.which("vagrant", path=self.environment.get("PATH")):
            raise RequiredExecutableNotFoundError("vagrant: Executable not found.")

        self.config = VagrantOptions.model_validate(self.tutorial.configuration.run.runner.options)
        self.config.environment.setdefault("VAGRANT_CWD", str(self.tutorial.root))
        self.config.environment.setdefault("PATH", os.environ["PATH"])
        self.cwds: dict[str, str] = self.config.cwds.copy()

    def vagrant(
        self, args: Sequence[str], env: dict[str, str] | None = None, check: bool = True
    ) -> subprocess.CompletedProcess[bytes]:
        """Run a vagrant command.

        NOTE: This method is intended to be run by boilerplate parts (e.g. preparation, cleanup) of running
        the tutorial, and *not* for commands from the tutorial.
        """
        command = ["vagrant", *args]
        joined_command = shlex.join(command)
        command_logger.info(joined_command)
        env = {**os.environ, **self.config.environment, **(env or {})}
        proc = subprocess.run(command, env=env, capture_output=not self.show_command_output)
        if check and proc.returncode != 0:
            raise RunTutorialException(f"{joined_command} exited with status code {proc.returncode}.")
        return proc

    def chdir(self, path: str, options: dict[str, Any]) -> None:
        machine = options.get("machine", "default")
        self.cwds[machine] = path

    def run_shell_command(
        self,
        command: CommandType,
        show_output: bool,
        capture_output: bool = False,
        stdin: int | io.BufferedReader | None = None,
        input: bytes | None = None,
        environment: dict[str, Any] | None = None,
        clear_environment: bool = False,
        options: dict[str, Any] | None = None,
    ) -> CompletedProcess[bytes]:
        if options is None:  # pragma: no cover  # doesn't happen in real time
            options = {}

        machine = options.get("machine", "default")
        command = self.render_command(command)
        if isinstance(command, tuple):
            command = shlex.join(command)

        cmd = command
        cwd = self.cwds.get(machine)
        if cwd:
            cmd = f"{shlex.join(['cd', cwd])} && {command}"

        vagrant_command = ["vagrant", "ssh", machine, "-c", cmd]

        proc = super().run_shell_command(
            tuple(vagrant_command),
            show_output=show_output,
            capture_output=capture_output,
            stdin=stdin,
            input=input,
            environment=self.config.environment,
            clear_environment=True,
        )
        return proc

    def prepare_vagrantfile(self, path: Path) -> None:
        """Render a Vagrantfile in the given directory."""
        if not path.exists():
            raise ConfigurationException(f"{path}: Directory not found.")

        vagrantfile_path = path / "Vagrantfile"
        template_path = vagrantfile_path.with_suffix(".jinja")
        if os.path.exists(template_path):
            with open(template_path) as template_stream:
                template = template_stream.read()

            contents = self.render(template)
            with open(vagrantfile_path, "w") as vagrant_file_stream:
                vagrant_file_stream.write(contents)
        elif not os.path.exists(vagrantfile_path):
            raise ConfigurationException(f"Vagrantfile not found: {vagrantfile_path}")

    def prepare_box(self, config: PrepareBoxOptions) -> None:
        """Prepare the box before running the tutorial, if requested."""
        vagrant_cwd = self.tutorial.root / config.cwd
        self.context["box"] = config.name  # update context with name of box

        # Render the Vagrantfile to prepare the box
        self.prepare_vagrantfile(vagrant_cwd)

        result = subprocess.run(
            ["vagrant", "box", "list", "--machine-readable"], capture_output=True, text=True, check=True
        )
        if any(
            row.split(",")[2] == "box-name" and row.split(",")[3] == config.name
            for row in result.stdout.splitlines()
        ):
            log.info("Box '%s' already exists, skip creation.", config.name)
            return

        log.info("Preparing Vagrant box in %s", vagrant_cwd)
        env = {"VAGRANT_CWD": str(vagrant_cwd)}
        try:
            self.vagrant(["up"], env=env)
            self.vagrant(["package", "--output", f"{config.name}.box"], env=env)
        finally:
            self.vagrant(["destroy", "-f"], env=env)

        self.vagrant(["box", "add", config.name, f"{config.name}.box"], env=env)

    def update_environment_variable(self, key: str, value: str, options: dict[str, str]) -> None:
        self.run_shell_command(
            f'echo export {key}="{value}" >> ~/.profile', show_output=False, options=options
        )

    def prepare_tutorial(self) -> None:
        """Prepare tutorial for running."""
        if prepare_box_config := self.config.prepare_box:
            self.prepare_box(prepare_box_config)

        # Render the main Vagrantfile for the tutorial
        self.prepare_vagrantfile(Path(self.config.environment["VAGRANT_CWD"]))
        self.vagrant(["up"])

    def cleanup_tutorial(self) -> None:
        """Cleanup tutorial after running."""
        self.vagrant(["destroy", "-f"])

    def copy_file(self, source: Path, destination: Path, options: dict[str, Any]) -> None:
        machine = options.get("machine", "default")
        self.vagrant(["upload", str(source), str(destination), machine])

    def write_file_from_string(self, contents: str, destination: Path, options: dict[str, Any]) -> None:
        # Only way to write a file from string is to write it to a temporary file on the host system
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(contents)
            temp_file.flush()
            self.copy_file(Path(temp_file.name), destination, options)
