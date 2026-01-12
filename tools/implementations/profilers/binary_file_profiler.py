import subprocess

from tools.interfaces.profiler import Profiler


class BinaryFileProfiler(Profiler):
    def __init__(self, perf, cmd_args=""):
        self.perf = perf
        self.cmd_args = cmd_args

    def profile(self, binary_path):
        try:
            cmd = binary_path
            if self.cmd_args:
                cmd += " " + self.cmd_args
            self.perf.record(cmd)
            report = self.perf.report()
            return self.perf.parse_report(report)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
            self.raise_profile_error(f"Perf run failed: {str(e)}")
