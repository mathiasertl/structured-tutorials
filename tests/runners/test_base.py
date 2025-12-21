# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test functionality found in the base class."""

import pytest

from structured_tutorials.errors import InvalidAlternativesSelectedError
from structured_tutorials.models import TutorialModel
from tests.conftest import Runner


@pytest.mark.tutorial("alternatives")
def test_validate_alternatives(tutorial: TutorialModel) -> None:
    """Test basic validation of alternatives."""
    runner = Runner(tutorial, alternatives=("foo",))
    runner.validate_alternatives()


@pytest.mark.tutorial("alternatives")
def test_validate_alternatives_with_no_selected_alternative(tutorial: TutorialModel) -> None:
    """Test error when no alternative was selected."""
    runner = Runner(tutorial, alternatives=("bla",))
    with pytest.raises(InvalidAlternativesSelectedError, match=r"^Part 1: No alternative selected\.$"):
        runner.validate_alternatives()


@pytest.mark.tutorial("alternatives")
def test_validate_alternatives_with_multiple_selected_alternatives(tutorial: TutorialModel) -> None:
    """Test error when multiple alternatives where selected."""
    runner = Runner(tutorial, alternatives=("foo", "bar"))
    with pytest.raises(
        InvalidAlternativesSelectedError, match=r"^Part 1: More then one alternative selected:"
    ):
        runner.validate_alternatives()
