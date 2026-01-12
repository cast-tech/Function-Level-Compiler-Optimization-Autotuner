import os
import subprocess

from tools.interfaces.profiler import Profiler


class SPECProfiler(Profiler):
    def __init__(self, perf, threads=1, iterations=1, size='test'):
        self.perf = perf
        self.threads = threads
        self.iterations = iterations
        self.size = size

    def profile(self, build_info):
        try:
            spec_root, build_dir, config_path, benchmark_name, env = build_info
            shrc_path = os.path.join(spec_root, 'shrc')
            run_cmd = f"runcpu --output_root={build_dir} --config={config_path} --tune=peak --size={self.size} --iterations={self.iterations} --threads={self.threads} --noreportable --nobuild {benchmark_name}"
            cmd_prefix = f"cd {spec_root} && . {shrc_path} && cd - && "
            self.perf.record(run_cmd, env, cmd_prefix)
            report = self.perf.report()
            return self.perf.parse_report(report)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
            self.raise_profile_error(f"SPEC run with perf failed: {str(e)}")
