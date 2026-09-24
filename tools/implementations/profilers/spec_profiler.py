import os
import subprocess

from tools.interfaces.profiler import Profiler


class SPECProfiler(Profiler):
    def __init__(self, perf, threads=1, iterations=1, size='test', cores=None):
        self.perf = perf
        self.threads = threads
        self.iterations = iterations
        self.size = size
        self.taskset_cmd = f"taskset -c {cores} " if cores else ""

    def profile(self, build_info):
        try:
            spec_root, build_dir, config_path, benchmark_name, env, gcc_dir = build_info
            shrc_path = os.path.join(spec_root, 'shrc')
            run_cmd = f"{self.taskset_cmd}runcpu --output_root={build_dir} --config={config_path} --tune=peak --size={self.size} --iterations={self.iterations} --threads={self.threads} --define gcc_dir={gcc_dir} --noreportable --nobuild {benchmark_name}"
            cmd_prefix = f"cd {spec_root} && . {shrc_path} && cd - && "
            self.perf.record(run_cmd, env, cmd_prefix)
            report = self.perf.report()
            return self.perf.parse_report(report, "spec")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
            self.raise_profile_error(f"SPEC run with perf failed: {str(e)}")
