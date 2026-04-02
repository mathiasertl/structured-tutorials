# Copyright (c) 2026 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""conftest for vagrant tests."""

from collections.abc import Iterator
from unittest.mock import patch

import pytest

from structured_tutorials.models import TutorialModel
from structured_tutorials.runners.vagrant import VagrantRunner


@pytest.fixture
def runner(tutorial: TutorialModel) -> VagrantRunner:
    """Fixture to retrieve a local tutorial runner based on the tutorial fixture."""
    return VagrantRunner(tutorial, interactive=False)


@pytest.fixture(autouse=True)
def mock_shutil_which() -> Iterator[None]:
    """Mock shutil.which to make sure that vagrant is always "found"."""
    with patch("structured_tutorials.runners.vagrant.shutil.which", return_value=True):
        yield
