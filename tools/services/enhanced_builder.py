from abc import ABC, abstractmethod


class EnhancedBuilderError(Exception):
    pass


class EnhancedBuilder(ABC):
    @abstractmethod
    def build_with_optimizations(self, optimization_config, flags):
        pass
