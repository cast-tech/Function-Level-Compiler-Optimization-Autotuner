import argparse

from gcc.tools.implementations.runners.averaging_runner import AveragingRunner
from gcc.tools.implementations.builders.cmake_project_builder import CMakeProjectBuilder
from gcc.tools.implementations.profilers.binary_file_profiler import BinaryFileProfiler
from gcc.tools.implementations.utils.perf import Perf
from gcc.tools.implementations.runners.binary_file_runner import BinaryFileRunner
from gcc.tools.services.optimal_optimization_entries import create_optimal_optimization_entries

argparser = argparse.ArgumentParser()
argparser.add_argument('--project-dir', help='Path to the project directory', required=True)
argparser.add_argument('--compiler-bin', help='Path to the compiler bin directory', required=True)
argparser.add_argument('--project-binary', help='Name of the project binary', required=True)
argparser.add_argument('--gcc-plugin', help='Path to the gcc plugin .so file', required=True)
argparser.add_argument('--output-dir', help='Path to the output directory', required=True)
argparser.add_argument('--timeout', help='Program running timeout in seconds', type=int, default=10)
argparser.add_argument('--perf', help='Path to perf', type=str, default='perf')
argparser.add_argument('--frequency', help='Frequency of sampling', type=int, default=1000)
argparser.add_argument('--entries-limit', help='Max number of optimization entries allowed', type=int, default=10)


def main():
    args = argparser.parse_args()

    # Can be replaced with any Builder, Runner or Profiler
    builder = CMakeProjectBuilder(args.compiler_bin, args.project_dir, args.output_dir, args.project_binary)
    runner = AveragingRunner(BinaryFileRunner(timeout=args.timeout))
    profiler = BinaryFileProfiler(Perf(args.perf, args.timeout, args.frequency, args.output_dir))

    create_optimal_optimization_entries(builder, runner, profiler, args.gcc_plugin, args.output_dir, args.entries_limit)


if __name__ == "__main__":
    main()
