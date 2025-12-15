# Copyright (c) 2025 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Base classes for runners."""

import abc
from copy import deepcopy
from typing import Any

from jinja2 import Environment

from structured_tutorials.models import AlternativeModel, CleanupCommandModel, TutorialModel


class RunnerBase(abc.ABC):
    """Base class for runners to provide shared functionality."""

    def __init__(self, tutorial: TutorialModel, alternatives: tuple[str, ...] = ()):
        self.tutorial = tutorial
        self.context = deepcopy(tutorial.configuration.run.context)
        self.env = Environment(keep_trailing_newline=True)
        self.cleanup: list[CleanupCommandModel] = []
        self.alternatives = alternatives

    def render(self, value: str, **context: Any) -> str:
        return self.env.from_string(value).render({**self.context, **context})

    def validate_alternatives(self) -> None:
        """Validate that for each alternative part, an alternative was selected."""
        chosen = set(self.alternatives)

        for part_no, part in enumerate(self.tutorial.parts, start=1):
            if isinstance(part, AlternativeModel):
                selected = chosen & set(part.alternatives)
                print(selected, part.required)
                if part.required and len(selected) == 0:
                    raise ValueError(f"Part {part_no}: No alternative selected.")
                elif len(selected) != 1:
                    raise ValueError(f"Part {part_no}: More then one alternative selected: {selected}")

    @abc.abstractmethod
    def run(self) -> None:
        """Run the tutorial."""
