import os
import time
import subprocess

from tools.interfaces.runner import Runner


class BinaryFileRunner(Runner):
    def __init__(self, timeout, cmd_args="", cmd_stdin_file_path="",  cores=None):
        self.timeout = timeout
        self.cmd_args = cmd_args
        self.cmd_stdin_file_path = cmd_stdin_file_path
        self.taskset_cmd = ""
        if cores:
            self.taskset_cmd += f"taskset -c {cores}"

    def run(self, binary_path):
        stdin_file = None
        try:
            cmd = f"{self.taskset_cmd} {binary_path}"
            if self.cmd_args:
                cmd += " " + self.cmd_args
            start_time = time.perf_counter()
            if self.cmd_stdin_file_path:
                stdin_file = open(self.cmd_stdin_file_path, "r")
            subprocess.run(
                cmd,
                stdin=stdin_file,
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
        finally:
            if stdin_file:
                stdin_file.close()
