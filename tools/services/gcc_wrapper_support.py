import os
from tools.services.enhanced_builder import EnhancedBuilder
from tools.services.enhanced_builder import EnhancedBuilderError


class WrapperConfigGenerator:
    OPTIMIZATION_LEVEL_KEY = "level"

    BINARY_OPTIMIZATION_KEYS = [
        "selective-scheduling",
        "selective-scheduling2",
        "schedule-insns",
        "schedule-insns2",
        "sched-interblock",
        "unroll-loops",
        "peel-loops",
        "unswitch-loops",
        "tree-loop-vectorize",
        "tree-slp-vectorize",
        "tree-tail-merge",
        "tree-loop-distribute-patterns",
        "branch-probabilities",
        "code-hoisting"
    ]

    def __init__(self, output_dir):
        self.wrapper_config_filepath = os.path.abspath(os.path.join(output_dir, 'wrapper_optimizations.cfg'))

    @staticmethod
    def check_if_entry_keys_are_valid(optimization_entry, valid_keys):
        if any(k not in valid_keys for k in optimization_entry):
            raise EnhancedBuilderError("Invalid key in optimization config entry")

    def check_if_optimizations_are_supported(self, optimization_entry):
        if any((k not in self.BINARY_OPTIMIZATION_KEYS and k != self.OPTIMIZATION_LEVEL_KEY)
               for k in optimization_entry["optimizations"]):
            raise EnhancedBuilderError("Optimization not supported in config entry")

    def get_optimization_entry_content(self, optimization_entry):
        if 'type' not in optimization_entry:
            raise EnhancedBuilderError("No optimization entry type specified")
        elif optimization_entry['type'] == 'file':
            valid_keys = ["type", "filename", "optimizations"]
        else:
            raise EnhancedBuilderError("Unknown optimization entry type")
        self.check_if_entry_keys_are_valid(optimization_entry, valid_keys)
        self.check_if_optimizations_are_supported(optimization_entry)
        content = f"{optimization_entry['filename']}:"
        optimization_flags = []
        level = ""
        for key in optimization_entry["optimizations"]:
            if key == self.OPTIMIZATION_LEVEL_KEY:
                level = optimization_entry['optimizations'][key]
                continue
            if optimization_entry['optimizations'][key] == False:
                optimization_flags.append(f"-fno-{key}")
            else:
                optimization_flags.append(f"-f{key}")
        return content + f"-O{level} " + " ".join(optimization_flags)

    def get_optimization_config_content(self, optimization_config):
        config_contents = []
        for optimization_entry in optimization_config:
            config_contents.append(self.get_optimization_entry_content(optimization_entry))
        return "\n".join(config_contents)

    def generate_optimization_config_file(self, optimization_config):
        with open(self.wrapper_config_filepath, "w") as f:
            f.write(self.get_optimization_config_content(optimization_config))


class WrapperEnhancedBuilder(EnhancedBuilder):
    def __init__(self, builder, gcc_wrapper_path, gcc_bin_path, output_dir):
        self.builder = builder
        self.gcc_wrapper_path = gcc_wrapper_path
        self.gcc_bin_path = gcc_bin_path
        self.config_generator = WrapperConfigGenerator(output_dir)

    def build_with_optimizations(self, optimization_config, flags):
        self.config_generator.generate_optimization_config_file(optimization_config)
        os.environ["GCC_BIN"] = self.gcc_bin_path
        os.environ["OPTIMIZATION_CONFIG_PATH"] = self.config_generator.wrapper_config_filepath
        return self.builder.build(flags)
