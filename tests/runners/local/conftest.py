# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Pytest configuration for testing the LocalTutorialRunner."""

import pytest

from structured_tutorials.models import TutorialModel
from structured_tutorials.runners.local import LocalTutorialRunner


@pytest.fixture
def runner(tutorial: TutorialModel) -> LocalTutorialRunner:
    """Fixture to retrieve a local tutorial runner based on the tutorial fixture."""
    return LocalTutorialRunner(tutorial, interactive=False)


@pytest.fixture
def doc_runner(doc_tutorial: TutorialModel) -> LocalTutorialRunner:
    """Fixture to retrieve a local tutorial runner based on an example from the documentation."""
    return LocalTutorialRunner(doc_tutorial, interactive=False)
