import argparse
import opentuner
import json

from tools.implementations.builders.cmake_project_builder import CMakeProjectBuilder
from tools.implementations.runners.binary_file_runner import BinaryFileRunner
from tools.implementations.runners.averaging_runner import AveragingRunner
from tools.services.iterative_tuner import iterative_tune

argparser = argparse.ArgumentParser(parents=opentuner.argparsers())
argparser.add_argument('--project-dir', help='Path to the project directory', required=True)
argparser.add_argument('--compiler-bin', help='Path to the compiler bin directory', required=True)
argparser.add_argument('--project-binary', help='Name of the project binary', required=True)
argparser.add_argument('--gcc-plugin', help='Path to the gcc plugin .so file', required=True)
argparser.add_argument('--optimization-entries', help='Path to the optimization entries file', required=True)
argparser.add_argument('--output-dir', help='Path to the output directory', required=True)
argparser.add_argument('--timeout', help='Program running timeout in seconds', type=int, default=10)
argparser.add_argument('--cmd-args', help='Arguments passed to binary', type=str, default="")


def load_json(json_path):
    with open(json_path, 'r') as f:
        json_content = json.load(f)
    return json_content


def main():
    args = argparser.parse_args()

    # Can be replaced with any Builder or Runner
    builder = CMakeProjectBuilder(args.compiler_bin, args.project_dir, args.output_dir, args.project_binary)
    runner = AveragingRunner(BinaryFileRunner(args.timeout, args.cmd_args))

    optimization_entries = load_json(args.optimization_entries)
    iterative_tune(args, runner, builder, optimization_entries, args.output_dir, args.gcc_plugin)


if __name__ == "__main__":
    main()
