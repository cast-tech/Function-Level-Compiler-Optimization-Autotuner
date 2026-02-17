import argparse
import opentuner
import json

from tools.implementations.builders.spec_builder import SPECBuilder
from tools.implementations.runners.spec_runner import SPECRunner
from tools.implementations.runners.averaging_runner import AveragingRunner
from tools.services.iterative_tuner import iterative_tune
from tools.services.gcc_wrapper_support import WrapperEnhancedBuilder

argparser = argparse.ArgumentParser(parents=opentuner.argparsers())
argparser.add_argument('--spec-root', help='Path to the spec root directory', required=True)
argparser.add_argument('--spec-benchmark', help='Name of the spec benchmark', required=True)
argparser.add_argument('--spec-config', help='Path to the spec config file', required=True)
argparser.add_argument('--spec-threads-count', help='Number of threads for the spec run', type=int, default=1)
argparser.add_argument('--spec-iterations-count', help='Number of iterations for the spec run', type=int, default=1)
argparser.add_argument('--spec-size', help='Size of the spec run', choices=['test', 'train', 'refspeed'], default='test')
argparser.add_argument('--spec-core-count', help='Number of cores for the spec build', type=int, default=1)
argparser.add_argument('--compiler-bin', help='Path to the compiler bin directory', required=True)
argparser.add_argument('--gcc-wrapper-bin', help='Path to the gcc wrapper bin directory', required=True)
argparser.add_argument('--optimization-entries', help='Path to the optimization entries file', required=True)
argparser.add_argument('--output-dir', help='Path to the output directory', required=True)
argparser.add_argument('--timeout', help='Program running timeout in seconds', type=int, default=10)


def load_json(json_path):
    with open(json_path, 'r') as f:
        json_content = json.load(f)
    return json_content


def main():
    args = argparser.parse_args()

    # Can be replaced with any Builder or Runner
    base_builder = SPECBuilder(args.spec_root, args.spec_benchmark, args.spec_config, args.output_dir, args.spec_core_count, args.gcc_wrapper_bin)
    builder = WrapperEnhancedBuilder(base_builder, args.gcc_wrapper_bin, args.compiler_bin, args.output_dir)
    runner = AveragingRunner(SPECRunner(args.spec_threads_count, args.spec_iterations_count, args.spec_size, args.timeout))

    optimization_entries = load_json(args.optimization_entries)
    iterative_tune(args, runner, builder, optimization_entries, args.output_dir)


if __name__ == "__main__":
    main()
