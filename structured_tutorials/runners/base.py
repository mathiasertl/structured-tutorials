import abc
import copy

from structured_tutorials.models import Step, StepBase, Tutorial


class RunnerBase(abc.ABC):
    def __init__(self, tutorial: Tutorial) -> None:
        self._performed_steps: list[StepBase] = []
        self.tutorial = tutorial

    def run(self) -> None:
        context = copy.deepcopy(self.tutorial.context.execution)
        try:
            for part in self.tutorial.parts:
                for step in part.commands:
                    self.run_step(step)
                    self._performed_steps.append(step)
        finally:
            print("### cleaning up:")
            for step in reversed(self._performed_steps):
                for cleanup_step in step.cleanup:
                    print(cleanup_step)
                    self.run_step(cleanup_step)

    @abc.abstractmethod
    def run_step(self, step: StepBase) -> None: ...
