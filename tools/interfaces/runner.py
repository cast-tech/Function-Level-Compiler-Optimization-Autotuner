from abc import ABC, abstractmethod


class RunError(Exception):
    pass


class Runner(ABC):
    @abstractmethod
    def run(self, build_info) -> float:
        """
        Runs the project using the build info provided by the builder.
        Returns measured time taken to run the project.
        """
        pass

    def raise_run_error(self, msg: str):
        raise RunError(msg)
