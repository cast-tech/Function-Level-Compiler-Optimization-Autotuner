import os
import shutil

from tools.services.compiler_optimizations_tuner import CompilerOptimizationsTuner
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
from tools.services.iterative_tuner import get_best_optimization_config
from tools.implementations.runners.averaging_runner import UnstableRuntimeError

import json


def load_flags(flags_file):
    flags = []
    with open(flags_file) as f:
        for line in f:
            flag = line.strip().split()[0] if line.strip() else ""
            if not flag or flag.startswith("#"):
                continue
            if flag.startswith("-fno-"):
                flag = flag[5:]
            elif flag.startswith("-f"):
                flag = flag[2:]
            if flag and flag not in flags:
                flags.append(flag)
    if not flags:
        raise ValueError(f"No optimization flags found in {flags_file}")
    return flags


class SimpleConfigGenerator:
    OPTIMIZATION_LEVEL_KEY = WrapperConfigGenerator.OPTIMIZATION_LEVEL_KEY

    BINARY_OPTIMIZATION_KEYS_ALL = SHARED_BINARY_OPTIMIZATION_KEYS_ALL
    BINARY_OPTIMIZATION_KEYS_REDUCED = SHARED_BINARY_OPTIMIZATION_KEYS_REDUCED
    BINARY_OPTIMIZATION_KEYS = BINARY_OPTIMIZATION_KEYS_REDUCED
    FLAG_SET_CHOICES = SHARED_FLAG_SET_CHOICES

    @staticmethod
    def get_optimization_keys(flag_set):
        return get_shared_optimization_keys(flag_set)

    def __init__(self, flags=None, flag_set="reduced"):
        if flags is not None:
            self.flag_set = "custom"
            self.BINARY_OPTIMIZATION_KEYS = list(flags)
        else:
            self.flag_set = flag_set
            self.BINARY_OPTIMIZATION_KEYS = self.get_optimization_keys(flag_set)


class SimpleEnhancedBuilder(EnhancedBuilder):
    """
    Adapts a plain Builder (Builder.build(flags)) to the EnhancedBuilder
    interface expected by CompilerOptimizationsTuner, so the same tuner can
    be reused directly against a builder that just takes a flat list of gcc
    flags (e.g. SPECBuilder), with no per-file/function wrapper or plugin.
    """

    def __init__(self, builder, flags=None, flag_set="reduced"):
        self.builder = builder
        self.config_generator = SimpleConfigGenerator(flags, flag_set)

    def build_with_optimizations(self, optimization_config, flags):
        # Warmup/baseline call this with an empty optimization_config (no
        # entry decided yet) and rely on the plain `flags` fallback, same as
        # the Wrapper/Plugin enhanced builders.
        if not optimization_config:
            return self.builder.build(flags)
        optimizations = optimization_config[-1]["optimizations"]
        level = optimizations[self.config_generator.OPTIMIZATION_LEVEL_KEY]
        gcc_flags = [f"-O{level}"]
        for flag in self.config_generator.BINARY_OPTIMIZATION_KEYS:
            gcc_flags.append(f"-f{flag}" if optimizations[flag] else f"-fno-{flag}")
        return self.builder.build(gcc_flags)


def simple_tune(args, runner, builder, output_dir, flags=None, flag_set="reduced",
                name="simple_tuner"):
    db_dir = os.path.join(output_dir, 'opentuner.db')
    shutil.rmtree(db_dir, ignore_errors=True)
    os.makedirs(db_dir, exist_ok=True)
    args.database = os.path.join(db_dir, name)

    enhanced_builder = SimpleEnhancedBuilder(builder, flags, flag_set)
    entry = {"type": "global"}
    try:
        CompilerOptimizationsTuner.main(args, runner, enhanced_builder, [], entry, name, True, output_dir)
    except UnstableRuntimeError as e:
        print(f"Terminating tuning: project is unstable under -O3: {e}")
        return None

    best_optimization_config = get_best_optimization_config(name, output_dir)
    result_filepath = os.path.join(output_dir, 'optimization_config.json')
    with open(result_filepath, 'w') as file:
        json.dump(best_optimization_config, file, indent=2)
    print(f"Best optimization config written to {result_filepath}")
    return best_optimization_config
