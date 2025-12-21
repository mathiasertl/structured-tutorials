# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Utility functions."""

import logging
import os
import random
import string
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from structured_tutorials.runners.base import RunnerBase

log = logging.getLogger(__name__)


@contextmanager
def chdir(dest: str | Path) -> Iterator[Path]:
    """Context manager to temporarily switch to a different directory."""
    cwd = Path.cwd()
    try:
        os.chdir(dest)
        yield cwd
    finally:
        os.chdir(cwd)


@contextmanager
def cleanup(runner: RunnerBase) -> Iterator[None]:
    """Context manager to always run cleanup commands."""
    try:
        yield
    finally:
        if runner.cleanup:
            log.info("Running cleanup commands.")

        for command_config in runner.cleanup:
            runner.run_shell_command(command_config.command, command_config.show_output)


def git_export(destination: str | Path, ref: str = "HEAD") -> Path:
    """Export the git repository to `django-ca-{ref}/` in the given destination directory.

    `ref` may be any valid git reference, usually a git tag.
    """
    # Add a random suffix to the export destination to improve build isolation (e.g. Docker Compose will use
    # that directory name as a name for Docker images/containers).
    random_suffix = "".join(random.choice(string.ascii_lowercase) for i in range(12))
    destination = Path(destination) / f"git-export-{ref}-{random_suffix}"

    if not destination.exists():  # pragma: no cover  # created by caller
        destination.mkdir(parents=True)

    with subprocess.Popen(["git", "archive", ref], stdout=subprocess.PIPE) as git_archive_cmd:
        with subprocess.Popen(["tar", "-x", "-C", str(destination)], stdin=git_archive_cmd.stdout) as tar:
            # TYPEHINT NOTE: stdout is not None b/c of stdout=subprocess.PIPE
            stdout = git_archive_cmd.stdout
            assert stdout is not None, "stdout not captured."
            stdout.close()
            tar.communicate()

    return destination
