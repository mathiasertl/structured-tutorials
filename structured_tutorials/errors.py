# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Collection of errors thrown by this project."""


class StructuredTutorialError(Exception):
    """Base class for all exceptions thrown by this project."""


class InvalidAlternativesSelectedError(StructuredTutorialError):
    """Exception raised when an invalid alternative is selected."""
