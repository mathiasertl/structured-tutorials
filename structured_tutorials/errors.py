# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Collection of errors thrown by this project."""


class StructuredTutorialError(Exception):
    """Base class for all exceptions thrown by this project."""


class RunTutorialException(StructuredTutorialError):
    """Exception that is raised when we capture an exception while running (and not yet cleaning up)."""


class InvalidAlternativesSelectedError(StructuredTutorialError):
    """Exception raised when an invalid alternative is selected."""


class RequiredExecutableNotFoundError(RunTutorialException):
    """Exception raised when a required executable is not found."""


class PartError(StructuredTutorialError):
    """Base class for all errors happening in a specific part."""


class CommandsPartError(PartError):
    """Base class for all errors happening in a specific commands part."""


class CommandTestError(CommandsPartError):
    """Base class for exceptions when a test for a command fails."""


class CommandOutputTestError(CommandTestError):
    """Exception raised when an output test fails."""


class FilePartError(PartError):
    """Exception raised for errors in file parts."""


class DestinationIsADirectoryError(FilePartError):
    """Exception raised when a destination is a directory."""


class PromptNotConfirmedError(PartError):
    """Exception raised when a user does not confirm the current state in a prompt part."""
