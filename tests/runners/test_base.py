# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test functionality found in the base class."""

from pathlib import Path

import pytest

from structured_tutorials.errors import InvalidAlternativesSelectedError, RequiredExecutableNotFoundError
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


@pytest.mark.tutorial("alternatives-configuration")
def test_alternatives_configuration(tutorial: TutorialModel) -> None:
    """Test alternatives configuration at runtime."""
    runner = Runner(tutorial, alternatives=("foo",))
    assert runner.alternatives == ("foo",)
    assert runner.context["key"] == "foo-var"
    assert runner.environment == {"env-key": "env-foo", "foo-key": "env-foo-key"}


def test_required_executables() -> None:
    """Test required executables."""
    tutorial = TutorialModel(
        configuration={"run": {"required_executables": ["git"]}}, parts=[], path=Path.cwd()
    )
    Runner(tutorial)


def test_required_executables_in_alternatives() -> None:
    """Test required executables in alternatives."""
    tutorial = TutorialModel(
        configuration={"run": {"alternatives": {"foo": {"required_executables": ["git"]}}}},
        parts=[],
        path=Path.cwd(),
    )
    Runner(tutorial, alternatives=("foo",))


def test_required_executables_with_custom_path() -> None:
    """Test required executables with a custom PATH environment variable."""
    tutorial = TutorialModel(
        configuration={"run": {"required_executables": ["git"], "environment": {"PATH": "/does/not/exist"}}},
        parts=[],
        path=Path.cwd(),
    )
    with pytest.raises(RequiredExecutableNotFoundError, match=r"^git: Executable not found.$"):
        Runner(tutorial)


def test_required_executables_in_alternative_with_custom_path() -> None:
    """Test required executables with a custom PATH environment variable."""
    tutorial = TutorialModel(
        configuration={
            "run": {
                "alternatives": {
                    "foo": {"required_executables": ["git"], "environment": {"PATH": "/does/not/exist"}}
                }
            },
        },
        parts=[],
        path=Path.cwd(),
    )
    with pytest.raises(RequiredExecutableNotFoundError, match=r"^git: Executable not found.$"):
        Runner(tutorial, alternatives=("foo",))
