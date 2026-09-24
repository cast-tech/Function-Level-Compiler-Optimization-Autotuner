import argparse

from tools.implementations.builders.spec_builder import SPECBuilder
from tools.implementations.runners.spec_runner import SPECRunner
from tools.implementations.profilers.spec_profiler import SPECProfiler
from tools.implementations.utils.perf import Perf
from tools.services.optimal_optimization_entries import create_optimal_optimization_entries_file_and_function
from tools.services.gcc_plugin_support import PluginEnhancedBuilder
from tools.services.gcc_wrapper_support import WrapperEnhancedBuilder

argparser = argparse.ArgumentParser()
argparser.add_argument('--spec-root', help='Path to the spec root directory', required=True)
argparser.add_argument('--spec-benchmark', help='Name of the spec benchmark', required=True)
argparser.add_argument('--spec-config', help='Path to the spec config file', required=True)
argparser.add_argument('--spec-threads-count', help='Number of threads for the spec run', type=int, default=1)
argparser.add_argument('--spec-iterations-count', help='Number of iterations for the spec run', type=int, default=1)
argparser.add_argument('--spec-size', help='Size of the spec run', choices=['test', 'train', 'refspeed'], default='test')
argparser.add_argument('--spec-core-count', help='Number of cores for the spec build', type=int, default=1)
argparser.add_argument('--compiler-bin', help='Path to the compiler bin directory', required=True)
argparser.add_argument('--gcc-wrapper-bin', help='Path to the gcc wrapper bin directory', required=True)
argparser.add_argument('--gcc-plugin', help='Path to the gcc plugin .so file', required=True)
argparser.add_argument('--output-dir', help='Path to the output directory', required=True)
argparser.add_argument('--timeout', help='Program running timeout in seconds', type=int, default=10)
argparser.add_argument('--perf', help='Path to perf', type=str, default='perf')
argparser.add_argument('--frequency', help='Frequency of sampling', type=int, default=1000)
argparser.add_argument('--entries-limit', help='Max number of optimization entries allowed', type=int, default=10)
argparser.add_argument('--runner-cores', help='Cores to set to taskset during runner run', type=str, default='')


def main():
    args = argparser.parse_args()

    # Can be replaced with any Builder, Runner or Profiler
    function_builder = SPECBuilder(args.spec_root, args.spec_benchmark, args.spec_config, args.output_dir, args.spec_core_count, args.compiler_bin)
    function_enhanced_builder = PluginEnhancedBuilder(function_builder, args.gcc_plugin, args.output_dir)

    file_builder = SPECBuilder(args.spec_root, args.spec_benchmark, args.spec_config, args.output_dir, args.spec_core_count, args.gcc_wrapper_bin)
    file_enhanced_builder = WrapperEnhancedBuilder(file_builder, args.gcc_wrapper_bin, args.compiler_bin, args.output_dir)

    runner = SPECRunner(args.spec_threads_count, args.spec_iterations_count, args.spec_size, args.timeout, args.runner_cores)
    profiler = SPECProfiler(Perf(args.perf, args.timeout, args.frequency, args.output_dir),
                            args.spec_threads_count, args.spec_iterations_count,
                            args.spec_size, args.runner_cores)

    create_optimal_optimization_entries_file_and_function(function_enhanced_builder, file_enhanced_builder, runner, profiler, args.output_dir, args.entries_limit)


if __name__ == "__main__":
    main()
