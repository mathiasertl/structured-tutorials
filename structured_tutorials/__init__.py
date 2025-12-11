# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("structured-tutorials")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "not-installed"
