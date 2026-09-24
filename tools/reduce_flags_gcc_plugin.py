import argparse
import opentuner
import logging

from tools.implementations.builders.cmake_project_builder import CMakeProjectBuilder
from tools.implementations.runners.binary_file_runner import BinaryFileRunner
from tools.implementations.runners.averaging_runner import AveragingRunner
from tools.services.gcc_plugin_support import PluginConfigGenerator, PluginEnhancedBuilder
from tools.services.reduce_flags import Reduce

argparser = argparse.ArgumentParser(parents=opentuner.argparsers())
argparser.add_argument('--project-dir', help='Path to the project directory', required=True)
argparser.add_argument('--compiler-bin', help='Path to the compiler bin directory', required=True)
argparser.add_argument('--project-binary', help='Name of the project binary', required=True)
argparser.add_argument('--gcc-plugin', help='Path to the gcc plugin .so file', required=True)
argparser.add_argument('--optimization-config', help='Path to the optimization entries file', required=True)
argparser.add_argument('--output-dir', help='Path to the output directory', required=True)
argparser.add_argument('--flag-set', choices=PluginConfigGenerator.FLAG_SET_CHOICES,
                       default='reduced', help='Flag set used by the input configuration')
argparser.add_argument('--build-cores', help='Number of parallel CMake build jobs', type=int, default=1)
argparser.add_argument('--timeout', help='Program running timeout in seconds', type=int, default=10)
argparser.add_argument('--cmd-args', help='Arguments passed to binary', type=str, default="")
argparser.add_argument('--entry-index', help='Configuration entry to reduce', type=int, default=0)
argparser.add_argument('--initial-group-size', help='Initial number of flags tested as a group',
                       type=int, default=50)
argparser.add_argument('--impact-threshold', help='Maximum allowed runtime degradation, in percent',
                       type=float, default=0.1)
argparser.add_argument('--min-flags-to-keep', help='Minimum non-level flags to retain',
                       type=int, default=0)
argparser.add_argument('--retries', help='Build/run attempts per configuration', type=int, default=1)


def main():
    args = argparser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Can be replaced with any Builder or Runner
    base_builder = CMakeProjectBuilder(args.compiler_bin, args.project_dir, args.output_dir,
                                       args.project_binary, args.build_cores)
    builder = PluginEnhancedBuilder(base_builder, args.gcc_plugin, args.output_dir,
                                    args.flag_set)
    runner = AveragingRunner(BinaryFileRunner(args.timeout, args.cmd_args))

    reduce = Reduce(
        args.optimization_config, runner, builder, args.output_dir,
        initial_group_size=args.initial_group_size,
        impact_threshold=args.impact_threshold,
        min_flags_to_keep=args.min_flags_to_keep,
        entry_index=args.entry_index,
        retries=args.retries,
    )
    reduce.reduce()


if __name__ == "__main__":
    main()
