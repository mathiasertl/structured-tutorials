"""Conftest module for pytest."""

from pathlib import Path

import pytest

TEST_DIR = Path(__file__).parent.absolute()
ROOT_DIR = TEST_DIR.parent
DATA_DIR = TEST_DIR / "data"
