import json
import logging
import opentuner
import os

from opentuner.resultsdb.models import Result
from opentuner.search import manipulator
from tools.services.cpu_info import get_cpu_info
from tools.services.gcc_plugin_support import PluginEnhancedBuilder
from tools.services.gcc_plugin_support import PluginConfigGenerationError
from tools.interfaces.runner import RunError
from tools.interfaces.builder import BuildError


class CompilerOptimizationsTuner(opentuner.measurement.MeasurementInterface):
    def __init__(self, args, runner, builder, gcc_plugin_path, init_opt_config, current_opt_entry, name, do_warmup,
                 output_dir, *pargs, **kwargs):
        super(CompilerOptimizationsTuner, self).__init__(args, *pargs, **kwargs)
        opentuner.init_logging()
        self.log = logging.getLogger(name)
        self.log.info(f"Tuner init...")
        self.runner = runner
        self.enhanced_builder = PluginEnhancedBuilder(builder, gcc_plugin_path, output_dir)
        self.init_opt_config = init_opt_config
        self.current_opt_entry = current_opt_entry
        self.history = []
        self.parallel_compile = False
        self.report_filename = os.path.join(output_dir, name + "_report.json")
        if do_warmup:
            self.warmup()

    def warmup(self, warmup_steps=2):
        self.log.info(f"Warmup...")
        for i in range(warmup_steps):
            self.compile_and_run_inner(self.init_opt_config)

    def manipulator(self):
        m = manipulator.ConfigurationManipulator()
        m.add_parameter(manipulator.BooleanParameter(self.enhanced_builder.config_generator.OPTIMIZATION_LEVEL_KEY))
        for opt in self.enhanced_builder.config_generator.BINARY_OPTIMIZATION_KEYS:
            m.add_parameter(manipulator.BooleanParameter(opt))
        return m

    def save_final_config(self, configuration):
        self.log.info(f"Tuning report written to {self.report_filename}")
        with open(self.report_filename, 'w') as fd:
            json.dump(self.create_report(), fd, indent=2)

    def create_report(self):
        return {
            "cpu_info": get_cpu_info(),
            "tunable_optimizations": self.enhanced_builder.config_generator.BINARY_OPTIMIZATION_KEYS,
            "init_opt_config": self.init_opt_config,
            "current_opt_entry": self.current_opt_entry,
            "history": self.history
        }

    def compile_and_run(self, desired_result, input, limit):
        optimizations_config = self.get_optimizations_config(desired_result.configuration.data)
        runtime = self.compile_and_run_inner(optimizations_config)
        if runtime == float('inf'):
            return Result(state='ERROR', time=float('inf'))
        info = {'runtime': runtime, 'optimizations': optimizations_config[-1]["optimizations"]}
        self.history.append(info)
        return Result(time=runtime)

    def compile_and_run_inner(self, optimizations_config):
        try:
            build_status = self.enhanced_builder.build_with_optimizations(optimizations_config, ["-O3"])
            runtime = self.runner.run(build_status)
        except RunError as e:
            self.log.warning(f"Runner failed: {e}")
            return float('inf')
        except BuildError as e:
            self.log.warning(f"Builder failed: {e}")
            return float('inf')
        except PluginConfigGenerationError as e:
            self.log.warning(f"Plugin Config Generator failed: {e}")
            return float('inf')
        if runtime == float('inf'):
            self.log.warning(f"Runtime evaluation failed")
            return float('inf')
        return runtime

    def get_optimizations_config(self, cfg):
        current_entry = self.current_opt_entry.copy()
        current_entry["optimizations"] = {}
        if cfg[self.enhanced_builder.config_generator.OPTIMIZATION_LEVEL_KEY]:
            current_entry["optimizations"][self.enhanced_builder.config_generator.OPTIMIZATION_LEVEL_KEY] = 3
        else:
            current_entry["optimizations"][self.enhanced_builder.config_generator.OPTIMIZATION_LEVEL_KEY] = 2

        for opt in self.enhanced_builder.config_generator.BINARY_OPTIMIZATION_KEYS:
            current_entry["optimizations"][opt] = cfg[opt]

        return self.init_opt_config + [current_entry]
