# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Collect functions related to output."""

import logging
import logging.config
import sys
from typing import Any, ClassVar, Literal

from colorama import Fore, Style, just_fix_windows_console
from termcolor import colored

just_fix_windows_console()  # needed on Windows

LOG_LEVELS = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def error(text: str) -> None:
    """Output a red/bold line on stderr."""
    print(colored(text, "red", attrs=["bold"]), file=sys.stderr)


class ColorFormatter(logging.Formatter):
    """Base class for color-based formatters."""

    def __init__(self, *args: Any, no_colors: bool = False, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Decide once at formatter creation time
        self.use_colors = sys.stderr.isatty() and no_colors is False


class LevelColorFormatter(ColorFormatter):
    """Formatter that colors the log level."""

    COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }

    def format(self, record: logging.LogRecord) -> str:
        if not self.use_colors:
            return super().format(record)

        level_name = record.levelname
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{level_name.ljust(8)}{Style.RESET_ALL}"
        try:
            return super().format(record)
        finally:
            record.levelname = level_name  # restore for other handlers


class BoldFormatter(ColorFormatter):
    """Formatter that outputs all messages in bold, if colors are used."""

    def format(self, record: logging.LogRecord) -> str:
        if not self.use_colors:
            return super().format(record)

        original = record.msg
        record.msg = f"{Style.BRIGHT}{original}{Style.RESET_ALL}"
        try:
            return super().format(record)
        finally:
            record.msg = original  # restore for other handlers


class CommandFormatter(logging.Formatter):
    """Formatter that prepends any log message with a '+ ' (same as `set -x` on a shell)."""

    def format(self, record: logging.LogRecord) -> str:
        original = record.msg
        record.msg = f"+ {original}"
        try:
            return super().format(record)
        finally:
            record.msg = original  # restore for other handlers


def setup_logging(level: LOG_LEVELS, no_colors: bool, show_commands: bool) -> None:
    """Setup logging for the process."""
    command_log_level: LOG_LEVELS = "INFO" if show_commands else "WARNING"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colored": {
                "()": "structured_tutorials.output.LevelColorFormatter",
                "format": "%(levelname)-8s | %(message)s",
                "no_colors": no_colors,
            },
            "bold": {
                "()": "structured_tutorials.output.BoldFormatter",
                "format": "%(message)s",
                "no_colors": no_colors,
            },
            "command": {
                "()": "structured_tutorials.output.CommandFormatter",
                "format": "%(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
            "part": {
                "class": "logging.StreamHandler",
                "formatter": "bold",
            },
            "command": {
                "class": "logging.StreamHandler",
                "formatter": "command",
            },
        },
        "loggers": {
            "part": {
                "handlers": ["part"],
                "propagate": False,
                "level": level,
            },
            "command": {
                "handlers": ["command"],
                "propagate": False,
                "level": command_log_level,
            },
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
    }

    logging.config.dictConfig(config)
