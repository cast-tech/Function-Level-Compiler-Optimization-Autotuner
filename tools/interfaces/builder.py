from abc import ABC, abstractmethod


class BuildError(Exception):
    pass


class Builder(ABC):
    @abstractmethod
    def build(self, flags: list[str]):
        """
        Builds the project using the provided list of flags.
        Returns the build info, which is then passed to the runner.
        """
        pass

    def raise_build_error(self, msg: str):
        raise BuildError(msg)
