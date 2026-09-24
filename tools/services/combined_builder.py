import os

from tools.services.enhanced_builder import EnhancedBuilder
from tools.services.gcc_optimization_flags import (
    BINARY_OPTIMIZATION_KEYS_ALL as SHARED_BINARY_OPTIMIZATION_KEYS_ALL,
)
from tools.services.gcc_optimization_flags import (
    BINARY_OPTIMIZATION_KEYS_REDUCED as SHARED_BINARY_OPTIMIZATION_KEYS_REDUCED,
)
from tools.services.gcc_optimization_flags import FLAG_SET_CHOICES as SHARED_FLAG_SET_CHOICES
from tools.services.gcc_optimization_flags import get_optimization_keys as get_shared_optimization_keys
from tools.services.gcc_wrapper_support import WrapperConfigGenerator
from tools.services.gcc_plugin_support import PluginConfigGenerator


class CombinedConfigGenerator:
    OPTIMIZATION_LEVEL_KEY = PluginConfigGenerator.OPTIMIZATION_LEVEL_KEY
    BINARY_OPTIMIZATION_KEYS_ALL = SHARED_BINARY_OPTIMIZATION_KEYS_ALL
    BINARY_OPTIMIZATION_KEYS_REDUCED = SHARED_BINARY_OPTIMIZATION_KEYS_REDUCED
    BINARY_OPTIMIZATION_KEYS = BINARY_OPTIMIZATION_KEYS_REDUCED
    FLAG_SET_CHOICES = SHARED_FLAG_SET_CHOICES

    def __init__(self, flag_set="reduced"):
        self.flag_set = flag_set
        self.BINARY_OPTIMIZATION_KEYS = get_shared_optimization_keys(flag_set)


class CombinedEnhancedBuilder(EnhancedBuilder):
    """
    Applies file-level optimizations via the gcc wrapper and function-level
    optimizations via the gcc plugin in a single build.
    """

    def __init__(self, builder, gcc_wrapper_path, gcc_bin_path, gcc_plugin_path,
                 output_dir, flag_set="reduced"):
        self.builder = builder
        self.gcc_wrapper_path = gcc_wrapper_path
        self.gcc_bin_path = gcc_bin_path
        self.gcc_plugin_path = gcc_plugin_path
        self.wrapper_config_generator = WrapperConfigGenerator(output_dir, flag_set)
        self.plugin_config_generator = PluginConfigGenerator(output_dir, flag_set)
        self.config_generator = CombinedConfigGenerator(flag_set)

    def build_with_optimizations(self, optimization_config, flags):
        file_entries = [e for e in optimization_config if e.get('type') == 'file']
        function_entries = [e for e in optimization_config if e.get('type') == 'function']

        self.wrapper_config_generator.generate_optimization_config_file(file_entries)
        os.environ["GCC_BIN"] = self.gcc_bin_path
        os.environ["OPTIMIZATION_CONFIG_PATH"] = self.wrapper_config_generator.wrapper_config_filepath
        # Base/global optimization flags a matched per-file entry should fully replace
        # (plugin flags are excluded -- they are not per-file overrides).
        os.environ["BASE_OPTIMIZATION_FLAGS"] = " ".join(flags)

        self.plugin_config_generator.generate_optimization_config_file(function_entries)
        plugin_flags = [
            f"-fplugin={self.gcc_plugin_path}",
            f"-fplugin-arg-cxx_optimizer-config={self.plugin_config_generator.plugin_config_filepath}",
        ]

        return self.builder.build(flags + plugin_flags)
