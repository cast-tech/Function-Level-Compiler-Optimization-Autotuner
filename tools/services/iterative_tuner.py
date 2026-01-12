import os
import json
import shutil

from tools.services.compiler_optimizations_tuner import CompilerOptimizationsTuner


def get_best_optimization_config(tuner_name, output_dir):
    report_file = os.path.join(output_dir, tuner_name + "_report.json")

    if not os.path.isfile(report_file):
        print("Report file not found!")
        return None

    with open(report_file) as file:
        report = json.load(file)

    optimization_config = report["current_opt_entry"]
    optimization_config["optimizations"] = min(report["history"], key=lambda x: x["runtime"])["optimizations"]
    return optimization_config


def iterative_tune(args, runner, builder, optimization_entries, output_dir, gcc_plugin):
    db_dir = os.path.join(output_dir, 'opentuner.db')
    shutil.rmtree(db_dir, ignore_errors=True)
    os.makedirs(db_dir, exist_ok=True)
    init_optimization_config = []
    optimization_config_filepath = os.path.join(output_dir, 'optimization_config.json')
    for index, entry in enumerate(optimization_entries):
        tuner_name = "tuning_entry_" + str(index)
        args.database = os.path.join(db_dir, tuner_name)
        do_warmup = (index == 0)
        CompilerOptimizationsTuner.main(args, runner, builder, gcc_plugin, init_optimization_config, entry,
                                        tuner_name, do_warmup, output_dir)
        best_optimization_config = get_best_optimization_config(tuner_name, output_dir)
        if best_optimization_config is None:
            continue
        init_optimization_config.append(best_optimization_config)
        with open(optimization_config_filepath, 'w') as file:
            json.dump(init_optimization_config, file, indent=2)
    print(f"Best optimization config written to {optimization_config_filepath}")
