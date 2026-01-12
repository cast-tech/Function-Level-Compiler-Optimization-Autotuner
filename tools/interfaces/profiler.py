from abc import ABC, abstractmethod


class ProfileError(Exception):
    pass


class Profiler(ABC):
    @abstractmethod
    def profile(self, build_info) -> list[tuple[str, float]]:
        """
        Runs the project using the build info provided by the builder.
        Returns measured time taken to execute each function.
        """
        pass

    def raise_profile_error(self, msg: str):
        raise ProfileError(msg)
