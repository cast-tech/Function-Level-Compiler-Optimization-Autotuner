from tools.interfaces.runner import Runner


class AveragingRunner(Runner):
    def __init__(self, runner, run_count=5, trim_count=1):
        self.runner = runner
        self.run_count = run_count
        self.trim_count = trim_count
        if 2 * self.trim_count >= self.run_count:
            self.raise_run_error("Runner Error: trying to trim more runs than you actually perform!")

    def run(self, build_info) -> float:
        runtime_measurements = list()
        for i in range(self.run_count):
            runtime = self.runner.run(build_info)
            if not isinstance(runtime, float):
                self.raise_run_error("Runner Error: runtime was not a float!")
            runtime_measurements.append(runtime)
        if self.trim_count > 0:
            trimmed_runtime_measurements = sorted(runtime_measurements)[self.trim_count:-self.trim_count]
        else:
            trimmed_runtime_measurements = runtime_measurements
        return sum(trimmed_runtime_measurements) / len(trimmed_runtime_measurements)
