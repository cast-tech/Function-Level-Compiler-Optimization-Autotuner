import os
import subprocess
import csv

from gcc.tools.interfaces.runner import Runner


class SPECRunner(Runner):
    """Runner for SPEC CPU2017 intspeed benchmarks"""

    def __init__(self, threads=1, iterations=1, size='test', timeout=None):
        """
        Args:
            iterations: Number of iterations to run (default: 1)
            size: Workload size - 'test', 'train', 'refspeed' (default: 'test')
        """
        self.threads = threads
        self.iterations = iterations
        self.size = size
        self.timeout = timeout

    def run(self, build_info):
        try:
            spec_root, build_dir, config_path, benchmark_name, env = build_info
            shrc_path = os.path.join(spec_root, 'shrc')
            run_cmd = f"cd {spec_root} && . {shrc_path} && runcpu --output_root={build_dir} --config={config_path} --tune=peak --size={self.size} --iterations={self.iterations} --threads={self.threads} --noreportable --nobuild {benchmark_name}"

            subprocess.run(
                run_cmd,
                shell=True,
                env=env,
                executable='/bin/bash',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                check=True,
                text=True
            )

            return self.get_benchmark_runtime(benchmark_name, build_dir)

        except subprocess.CalledProcessError as e:
            self.raise_run_error(f"SPEC run failed: {str(e)}\nStderr: {e.stderr}")
        except subprocess.TimeoutExpired as e:
            self.raise_run_error(f"SPEC run failed (timed out): {str(e)}")
        except FileNotFoundError as e:
            self.raise_run_error(f"SPEC run failed (file not found): {str(e)}")

    def get_benchmark_runtime(self, benchmark_name, build_dir):
        result_dir = os.path.join(build_dir, 'result')
        csv_file = next((f for f in os.listdir(result_dir) if f.endswith('.csv')), None)
        if not csv_file:
            return self.raise_run_error("Could not find benchmark runtime file")
        csv_path = os.path.join(result_dir, csv_file)
        with open(csv_path, 'r') as file:
            return self.process_benchmark_runtime_from_csv_result(benchmark_name, csv.reader(file))

    def process_benchmark_runtime_from_csv_result(self, benchmark_name, reader):
        try:
            iteration_runtimes = []
            for row in reader:
                if row and len(row) >= 11 and row[0] == benchmark_name:
                    if row[10] == 'S':
                        iteration_runtimes.append(float(row[7]))
                    else:
                        self.raise_run_error("Benchmark run failed with an error status")
                if len(iteration_runtimes) == self.iterations:
                    return sorted(iteration_runtimes)[self.iterations // 2]
        except ValueError:
            pass
        self.raise_run_error("Failed to parse runtime from SPEC output")
