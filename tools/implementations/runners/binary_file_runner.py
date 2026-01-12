import os
import time
import subprocess

from gcc.tools.interfaces.runner import Runner


class BinaryFileRunner(Runner):
    def __init__(self, timeout, cmd_args=""):
        self.timeout = timeout
        self.cmd_args = cmd_args

    def run(self, binary_path):
        try:
            cmd = binary_path
            if self.cmd_args:
                cmd += " " + self.cmd_args
            start_time = time.perf_counter()
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True,
                check=True,
                timeout=self.timeout,
                cwd=os.path.dirname(binary_path)
            )
            end_time = time.perf_counter()
            return end_time - start_time
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.raise_run_error(f"{str(e)}")
