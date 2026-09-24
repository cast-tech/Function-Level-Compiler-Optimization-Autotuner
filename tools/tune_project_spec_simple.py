import argparse
import opentuner

from tools.implementations.builders.spec_builder import SPECBuilder
from tools.implementations.runners.spec_runner import SPECRunner
from tools.services.simple_tuner import SimpleConfigGenerator, simple_tune, load_flags

argparser = argparse.ArgumentParser(parents=opentuner.argparsers())
argparser.add_argument('--spec-root', help='Path to the spec root directory', required=True)
argparser.add_argument('--spec-benchmark', help='Name of the spec benchmark', required=True)
argparser.add_argument('--spec-config', help='Path to the spec config file', required=True)
argparser.add_argument('--spec-threads-count', help='Number of threads for the spec run', type=int, default=1)
argparser.add_argument('--spec-iterations-count', help='Number of iterations for the spec run', type=int, default=1)
argparser.add_argument('--spec-size', help='Size of the spec run', choices=['test', 'train', 'refspeed'], default='test')
argparser.add_argument('--spec-core-count', help='Number of cores for the spec build', type=int, default=1)
argparser.add_argument('--compiler-bin', help='Path to the compiler bin directory', required=True)
argparser.add_argument('--flags-file', help='Path to a file listing candidate flag names or -f flags, one per line '
                                             '(overrides --flag-set)', default=None)
argparser.add_argument('--flag-set', choices=SimpleConfigGenerator.FLAG_SET_CHOICES,
                       default='reduced', help='Built-in GCC optimization flag set to tune')
argparser.add_argument('--output-dir', help='Path to the output directory', required=True)
argparser.add_argument('--timeout', help='Program running timeout in seconds', type=int, default=10)
argparser.add_argument("--runner-cores", help="cores to set to taskset during runner run", type=str, default='')


def main():
    args = argparser.parse_args()

    builder = SPECBuilder(args.spec_root, args.spec_benchmark, args.spec_config, args.output_dir,
                           args.spec_core_count, args.compiler_bin)
    runner = SPECRunner(args.spec_threads_count, args.spec_iterations_count, args.spec_size, args.timeout,
                         args.runner_cores)

    flags = load_flags(args.flags_file) if args.flags_file else None
    simple_tune(args, runner, builder, args.output_dir, flags=flags,
                flag_set=args.flag_set)


if __name__ == "__main__":
    main()
