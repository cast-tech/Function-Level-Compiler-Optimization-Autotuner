import argparse
import logging
import opentuner
import os

from tools.implementations.builders.source_file_builder import SourceFileBuilder
from tools.implementations.runners.binary_file_runner import BinaryFileRunner
from tools.implementations.runners.averaging_runner import AveragingRunner
from tools.services.gcc_wrapper_support import WrapperConfigGenerator, WrapperEnhancedBuilder
from tools.services.reduce_flags import Reduce

argparser = argparse.ArgumentParser(parents=opentuner.argparsers())
argparser.add_argument('--source-file-path', help='Path to the source file', required=True)
argparser.add_argument('--compiler-bin', help='Path to the compiler bin directory', required=True)
argparser.add_argument('--gcc-wrapper-bin', help='Path to the gcc wrapper bin directory', required=True)
argparser.add_argument('--optimization-config', help='Path to the optimization entries file', required=True)
argparser.add_argument('--output-dir', help='Path to the output directory', required=True)
argparser.add_argument('--flag-set', choices=WrapperConfigGenerator.FLAG_SET_CHOICES,
                       default='reduced', help='Flag set used by the input configuration')
argparser.add_argument('--timeout', help='Program running timeout in seconds', type=int, default=10)
argparser.add_argument('--cmd-args', help='Arguments passed to binary', type=str, default="")
argparser.add_argument('--stdin-file-path', help='Path to the stdin file', type=str, default='')
argparser.add_argument('--ranked-flags-csv', help='Path to ranked flags CSV for priority-aware grouping', default=None)
argparser.add_argument('--runner-cores', help='cores to set to taskset during runner run', type=str, default='')
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

    wrapper_name = 'gcc' if os.path.splitext(args.source_file_path)[1].lower() == '.c' else 'g++'
    wrapper_path = os.path.join(args.gcc_wrapper_bin, wrapper_name)
    base_builder = SourceFileBuilder(wrapper_path, args.source_file_path, args.output_dir)
    builder = WrapperEnhancedBuilder(base_builder, args.gcc_wrapper_bin, args.compiler_bin,
                                     args.output_dir, args.flag_set)
    runner = AveragingRunner(BinaryFileRunner(args.timeout, args.cmd_args, args.stdin_file_path, cores=args.runner_cores))

    reduce = Reduce(
        args.optimization_config, runner, builder, args.output_dir,
        initial_group_size=args.initial_group_size,
        impact_threshold=args.impact_threshold,
        min_flags_to_keep=args.min_flags_to_keep,
        ranked_flags_csv=args.ranked_flags_csv,
        entry_index=args.entry_index,
        retries=args.retries,
    )
    reduce.reduce()


if __name__ == "__main__":
    main()
