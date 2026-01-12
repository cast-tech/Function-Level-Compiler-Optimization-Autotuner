import subprocess
import re
import os


class Perf:
    def __init__(self, perf_path, timeout, perf_frequency, output_dir):
        self.perf = perf_path
        self.timeout = timeout
        self.perf_frequency = perf_frequency
        self.output_dir = output_dir

    def record(self, cmd, env=None, cmd_prefix=None):
        if env is None:
            env = os.environ.copy()
        if cmd_prefix is None:
            perf_record_cmd = ""
        else:
            perf_record_cmd = cmd_prefix
        perf_record_cmd += f"{self.perf} record -F{self.perf_frequency} -g " + cmd
        subprocess.run(
            perf_record_cmd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
            check=True,
            timeout=self.timeout,
            cwd=self.output_dir
        )

    def report(self):
        perf_report_cmd = [self.perf, "report", "--header", "-i", "perf.data", "-g", "none"]
        result = subprocess.run(perf_report_cmd, capture_output=True, text=True, cwd=self.output_dir, check=True)
        return result.stdout

    @staticmethod
    def parse_report(perf_report):
        duration = Perf.__get_sample_duration(perf_report)
        filtered_lines = [line for line in perf_report.strip().split('\n') if not line.strip().startswith('#')]

        parsed_data = []
        for line in filtered_lines:
            parts = line.split()
            if len(parts) >= 5:
                self_percent = parts[1]
                symbol_type = parts[4]
                self_duration = duration * float(self_percent.rstrip('%'))
                function = ' '.join(parts[5:]).strip()
                function_name = function.split('(')[0].split('.')[0].split(':')[-1]
                if len(function_name) > 0 and function_name[0] != '0' and self_duration > 0 and symbol_type == '[.]':
                    parsed_data.append((function_name, self_duration))
        return sorted(parsed_data, key=lambda item: item[1], reverse=True)

    @staticmethod
    def __get_sample_duration(perf_report):
        pattern = re.compile(r'sample duration\s*:\s*([\d.]+)\s*ms')
        match = pattern.search(perf_report)
        if not match:
            raise ValueError("Sample duration not found!")
        return float(match.group(1))
