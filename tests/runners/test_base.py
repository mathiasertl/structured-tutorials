# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test functionality found in the base class."""

import pytest

from structured_tutorials.models import TutorialModel
from structured_tutorials.runners.base import RunnerBase


class Runner(RunnerBase):
    """Dummy runner in this module."""

    def run(self) -> None:
        pass


@pytest.fixture
def model() -> TutorialModel:
    """Fixture to return a standard model."""
    return TutorialModel.model_validate(
        {
            "path": "/dummy.yaml",
            "parts": [
                {
                    "alternatives": {
                        "foo": {"commands": [{"command": "ls foo"}]},
                        "bar": {"commands": [{"command": "ls bar"}]},
                    }
                }
            ],
        }
    )


def test_validate_alternatives(model: TutorialModel) -> None:
    """Test basic validation of alternatives."""
    runner = Runner(model, alternatives=("foo",))
    runner.validate_alternatives()


def test_validate_alternatives_with_no_selected_alternative(model: TutorialModel) -> None:
    """Test error when no alternative was selected."""
    runner = Runner(model, alternatives=("bla",))
    with pytest.raises(ValueError, match=r"^Part 1: No alternative selected\.$"):
        runner.validate_alternatives()


def test_validate_alternatives_with_multiple_selected_alternatives(model: TutorialModel) -> None:
    """Test error when multiple alternatives where selected."""
    runner = Runner(model, alternatives=("foo", "bar"))
    with pytest.raises(ValueError, match=r"^Part 1: More then one alternative selected:"):
        runner.validate_alternatives()
