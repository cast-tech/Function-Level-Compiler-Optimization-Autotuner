import os
import json
from collections import defaultdict

from gcc.tools.services.gcc_plugin_support import PluginEnhancedBuilder


def combine_functions_with_same_name(function_runtimes):
    combined = defaultdict(float)
    for function, runtime in function_runtimes:
        combined[function] += runtime
    return list(combined.items())


def top_functions_by_runtime(function_runtimes, max_size):
    sorted_functions = sorted(function_runtimes, key=lambda x: x[1], reverse=True)
    return [name for name, _ in sorted_functions[:max_size]]


def create_optimal_optimization_entries(builder, runner, profiler, gcc_plugin, output_dir, report_limit):
    os.makedirs(output_dir, exist_ok=True)
    build_info = builder.build(["-O3", "-fno-omit-frame-pointer"])
    function_runtimes = profiler.profile(build_info)
    combined_function_runtimes = combine_functions_with_same_name(function_runtimes)
    top_functions = top_functions_by_runtime(combined_function_runtimes, report_limit)
    function_runtimes_optimization_disabled = []
    for function in top_functions:
        enhanced_builder = PluginEnhancedBuilder(builder, gcc_plugin, output_dir)
        optimization_config = [
            {
                "type": "function",
                "function_name": function,
                "optimizations": {
                    "level": 0
                }
            }
        ]
        build_info = enhanced_builder.build_with_optimizations(optimization_config, ["-O3"])
        runtime = runner.run(build_info)
        function_runtimes_optimization_disabled.append((function, runtime))
        print("{}: {:.3f} s".format(function, runtime))

    result_optimization_entries = []
    for function, runtime in sorted(function_runtimes_optimization_disabled, key=lambda x: x[1], reverse=True):
        result_optimization_entries.append({"type": "function", "function_name": function})

    result_optimization_entries_filepath = os.path.join(output_dir, "optimization_entries.json")
    with open(result_optimization_entries_filepath, "w") as f:
        json.dump(result_optimization_entries, f, indent=2)
    print(f"Optimal optimization entries written to {result_optimization_entries_filepath}")
