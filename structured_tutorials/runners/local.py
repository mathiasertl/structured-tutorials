# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Runner that runs a tutorial on the local machine."""

import logging
import os
import shutil
from pathlib import Path
from typing import Any

from structured_tutorials.runners.base import RunnerBase

log = logging.getLogger(__name__)


class LocalTutorialRunner(RunnerBase):
    """Runner implementation that runs a tutorial on the local machine."""

    def chdir(self, path: str, options: dict[str, Any]) -> None:
        os.chdir(str(path))

    def copy_file(self, source: Path, destination: Path, options: dict[str, Any]) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source, destination)

    def write_file_from_string(self, contents: str, destination: Path, options: dict[str, Any]) -> None:
        """Write a file from a string."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "w") as destination_stream:
            destination_stream.write(contents)
