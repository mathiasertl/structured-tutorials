# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Utility functions."""

import logging
import os
import random
import string
import subprocess
from collections.abc import Iterator, Sized
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from structured_tutorials.errors import PromptNotConfirmedError, RunTutorialException, StructuredTutorialError
from structured_tutorials.typing import COUNT_TYPE

if TYPE_CHECKING:
    from structured_tutorials.runners.base import RunnerBase

log = logging.getLogger(__name__)


def check_count(value: Sized, count: COUNT_TYPE) -> None:
    """Shared function to test a count."""
    if count is None:
        return
    if isinstance(count, int) and len(value) != count:
        raise ValueError(f"{len(value)}, but expected {count}.")
    if isinstance(count, tuple):
        if count[0] is not None and len(value) < count[0]:
            raise ValueError(f"{len(value)} is less then the minimum ({count[0]}).")
        if count[1] is not None and len(value) > count[1]:
            raise ValueError(f"{len(value)} is more then the maximum ({count[1]}).")


@contextmanager
def chdir(dest: str | Path) -> Iterator[Path]:
    """Context manager to temporarily switch to a different directory."""
    cwd = Path.cwd()
    try:
        os.chdir(dest)
        yield cwd
    finally:
        os.chdir(cwd)


def _prompt(interactive: bool) -> None:
    if interactive:
        input(f"""An error occurred while running the tutorial.
Current working directory is {os.getcwd()}

Press Enter to continue... """)


@contextmanager
def cleanup(runner: "RunnerBase") -> Iterator[None]:
    """Context manager to always run cleanup commands."""
    try:
        yield
    except PromptNotConfirmedError as ex:
        # The user did not confirm a prompt. We just log this fact as warning and continue with cleanup.
        # We do NOT prompt the user here, as we assume the user already inspected the state.
        log.warning(ex)
    except StructuredTutorialError as ex:
        log.error(ex)
        _prompt(runner.interactive)
        raise RunTutorialException(ex) from ex
    except Exception as ex:
        log.exception(ex)
        _prompt(runner.interactive)
        raise RunTutorialException(ex) from ex
    finally:
        if runner.cleanup:
            log.info("Running cleanup commands.")

        for command_config in runner.cleanup:
            runner.run_shell_command(
                command_config.command,
                command_config.show_output,
                environment=command_config.environment,
                clear_environment=command_config.clear_environment,
            )

            # Update environment for subsequent commands
            runner.environment.update(
                {k: runner.render(v) for k, v in command_config.update_environment.items()}
            )


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
