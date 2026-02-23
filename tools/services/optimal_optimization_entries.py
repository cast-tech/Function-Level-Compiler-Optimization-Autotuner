import os
import json
from collections import defaultdict

from tools.services.get_function_to_files_mapping import get_function_file_mapping
from tools.services.enhanced_builder import EnhancedBuilder


def combine_functions_with_same_name(function_runtimes):
    combined = defaultdict(float)
    for function, runtime in function_runtimes:
        combined[function] += runtime
    return list(combined.items())


def top_functions_by_runtime(function_runtimes, max_size):
    sorted_functions = sorted(function_runtimes, key=lambda x: x[1], reverse=True)
    return [name for name, _ in sorted_functions[:max_size]]

def get_function_files(function_runtimes, build_directory):
    function_file_mapping = {}
    for root, _, files in os.walk(build_directory):
        for file in files:
            full_path = os.path.join(root, file)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                try:
                    function_to_file_mapping_for_file = get_function_file_mapping(full_path)
                except Exception as e:
                    print(f"Error getting function to file mapping for {full_path}: {e}")
                    continue
                for func_name, file_path in function_to_file_mapping_for_file.items():
                    if func_name not in function_file_mapping:
                        function_file_mapping[func_name] = []
                    if file_path not in function_file_mapping[func_name]:
                        function_file_mapping[func_name].append(file_path)

    results = {}
    for func in function_runtimes:
        function_name = func[0]
        if function_name in function_file_mapping:
            matching_files = [f for f in function_file_mapping[function_name] if f.endswith((".cpp", ".cxx", ".cc", ".c"))]
            if matching_files:
                results[function_name] = matching_files
    return results

def get_file_runtimes(function_runtimes, build_directory): 
    function_in_files = get_function_files(function_runtimes, build_directory)
    file_runtimes = {}
    for function_runtime in function_runtimes:
        function_name = function_runtime[0]
        if function_name not in function_in_files:
            continue
        for file in function_in_files[function_name]:
            if file not in file_runtimes:
                file_runtimes[file] = 0
            file_runtimes[file] += function_runtime[1]
    return list(file_runtimes.items())
    
def top_files_by_runtime(function_runtimes, build_directory, max_size):
    file_runtimes = get_file_runtimes(function_runtimes, build_directory)
    sorted_files = sorted(file_runtimes, key=lambda x: x[1], reverse=True)
    return [name for name, _ in sorted_files[:max_size]] 

def top_entries_by_runtime(function_runtimes, max_size, build_directory="", is_function=True):
    if is_function:
        return top_functions_by_runtime(function_runtimes, max_size)
    return top_files_by_runtime(function_runtimes, build_directory, max_size)

def get_optimization_entry(entry, is_function):
    entry_type = "function_"
    if not is_function:
        entry_type = "file"

    optimization_entry = {
        "type": entry_type.replace("_", ""),
        f"{entry_type}name": entry
    }
    return optimization_entry

def create_optimal_optimization_entries(enhanced_builder: EnhancedBuilder, runner, profiler, is_function, output_dir, report_limit):
    os.makedirs(output_dir, exist_ok=True)
    build_info = enhanced_builder.build_with_optimizations([], ["-O3", "-fno-omit-frame-pointer"])
    function_runtimes = profiler.profile(build_info)
    combined_function_runtimes = combine_functions_with_same_name(function_runtimes)
    if not is_function:
        debug_build_info = enhanced_builder.build_with_optimizations([], ["-O3", "-g", "-fno-omit-frame-pointer"])
    top_entries = top_entries_by_runtime(combined_function_runtimes, report_limit, enhanced_builder.builder.build_dir, is_function)

    entry_runtimes_optimization_disabled = []
    for entry in top_entries:
        optimization_config = [get_optimization_entry(entry, is_function)]
        optimization_config[0]["optimizations"] = {"level": 0}
        build_info = enhanced_builder.build_with_optimizations(optimization_config, ["-O3"])
        runtime = runner.run(build_info)
        entry_runtimes_optimization_disabled.append((entry, runtime))
        print("{}: {:.3f} s".format(entry, runtime))

    result_optimization_entries = []
    for entry, runtime in sorted(entry_runtimes_optimization_disabled, key=lambda x: x[1], reverse=True):
        result_optimization_entries.append(get_optimization_entry(entry, is_function))

    result_optimization_entries_filepath = os.path.join(output_dir, "optimization_entries.json")
    with open(result_optimization_entries_filepath, "w") as f:
        json.dump(result_optimization_entries, f, indent=2)
    print(f"Optimal optimization entries written to {result_optimization_entries_filepath}")
