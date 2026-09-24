import os
import json
import shutil

from tools.services.compiler_optimizations_tuner import CompilerOptimizationsTuner
from tools.implementations.runners.averaging_runner import UnstableRuntimeError


def get_best_optimization_config(tuner_name, output_dir):
    report_file = os.path.join(output_dir, tuner_name + "_report.json")

    if not os.path.isfile(report_file):
        print("Report file not found!")
        return None

    with open(report_file) as file:
        report = json.load(file)

    if not report["history"]:
        print("No successful runs recorded!")
        return None

    optimization_config = report["current_opt_entry"]
    best_optimization_config = min(report["history"], key=lambda x: x["runtime"])
    if report["baseline_runtime"] != float('inf') and best_optimization_config["runtime"] > report["baseline_runtime"]:
        print("Best optimization config is worse than baseline!")
        return None
    optimization_config["optimizations"] = best_optimization_config["optimizations"]
    return optimization_config


def iterative_tune(args, runner, builder, optimization_entries, output_dir, initial_config=None,
                   tuner_name_prefix="", base_flags=None, do_warmup_first=True, db_dir=None):
    # Each stage gets its own opentuner.db so a later stage's fresh-start wipe does
    # not clobber earlier stages' databases. Defaults to <output_dir>/opentuner.db.
    db_dir = db_dir or os.path.join(output_dir, 'opentuner.db')
    shutil.rmtree(db_dir, ignore_errors=True)
    os.makedirs(db_dir, exist_ok=True)
    init_optimization_config = list(initial_config) if initial_config else []
    optimization_config_filepath = os.path.join(output_dir, 'optimization_config.json')
    tuned_configs = []
    # Always materialize the effective configuration, even when every tested
    # candidate loses to the baseline and no entry is selected.
    with open(optimization_config_filepath, 'w') as file:
        json.dump(init_optimization_config, file, indent=2)
    for index, entry in enumerate(optimization_entries):
        tuner_name = tuner_name_prefix + "tuning_entry_" + str(index)
        args.database = os.path.join(db_dir, tuner_name)
        do_warmup = (index == 0 and do_warmup_first and not initial_config)
        try:
            CompilerOptimizationsTuner.main(args, runner, builder, init_optimization_config, entry,
                                            tuner_name, do_warmup, output_dir, base_flags=base_flags)
        except UnstableRuntimeError as e:
            print(f"Terminating tuning: project is unstable under -O3: {e}")
            break
        best_optimization_config = get_best_optimization_config(tuner_name, output_dir)
        if best_optimization_config is None:
            continue
        init_optimization_config.append(best_optimization_config)
        tuned_configs.append(best_optimization_config)
        with open(optimization_config_filepath, 'w') as file:
            json.dump(init_optimization_config, file, indent=2)
    print(f"Best optimization config written to {optimization_config_filepath}")
    return tuned_configs


def two_phase_iterative_tune(args, file_runner, combined_runner, file_builder, combined_builder, file_entries, function_entries, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    optimization_config_filepath = os.path.join(output_dir, "optimization_config.json")

    db_root = os.path.join(output_dir, "opentuner.db")

    print("=== Phase 1: File-level tuning (gcc wrapper) ===")
    iterative_tune(args, file_runner, file_builder, file_entries, output_dir, tuner_name_prefix="phase1_",
                   db_dir=os.path.join(db_root, "phase1_file"))

    if os.path.isfile(optimization_config_filepath):
        with open(optimization_config_filepath) as f:
            best_file_configs = json.load(f)
    else:
        best_file_configs = []

    print("\n=== Phase 2: Function-level tuning (combined wrapper + plugin, file entries fixed) ===")
    best_function_configs = iterative_tune(
        args, combined_runner, combined_builder, function_entries, output_dir,
        initial_config=best_file_configs, tuner_name_prefix="phase2_",
        db_dir=os.path.join(db_root, "phase2_function")
    )

    final_config = best_file_configs + best_function_configs
    with open(optimization_config_filepath, "w") as f:
        json.dump(final_config, f, indent=2)
    print(f"\nFinal combined config written to {optimization_config_filepath}")


def global_flags_from_config(global_config, config_generator):
    """Turn a tuned {'type': 'global', 'optimizations': {...}} entry into a flat
    gcc flag list (e.g. ['-O2', '-fno-inline', '-ftree-vectorize', ...]) suitable
    for use as the whole-build base flags of the later stages."""
    if not global_config or "optimizations" not in global_config:
        return ["-O3"]
    optimizations = global_config["optimizations"]
    level = optimizations[config_generator.OPTIMIZATION_LEVEL_KEY]
    flags = [f"-O{level}"]
    for key in config_generator.BINARY_OPTIMIZATION_KEYS:
        flags.append(f"-f{key}" if optimizations[key] else f"-fno-{key}")
    return flags


def global_tune(args, runner, builder, output_dir, base_flags=None, tuner_name="global_tuning", db_dir=None):
    """Stage that tunes a single flag set applied to the whole project. `builder`
    is expected to be a SimpleEnhancedBuilder (plain Builder.build(flags) adapter).
    Returns the best {'type': 'global', 'optimizations': {...}} entry, or None."""
    db_dir = db_dir or os.path.join(output_dir, 'opentuner.db')
    shutil.rmtree(db_dir, ignore_errors=True)
    os.makedirs(db_dir, exist_ok=True)
    args.database = os.path.join(db_dir, tuner_name)
    entry = {"type": "global"}
    try:
        CompilerOptimizationsTuner.main(args, runner, builder, [], entry, tuner_name, True,
                                        output_dir, base_flags=base_flags)
    except UnstableRuntimeError as e:
        print(f"Terminating tuning: project is unstable under -O3: {e}")
        return None
    return get_best_optimization_config(tuner_name, output_dir)


def three_phase_iterative_tune(args, global_runner, file_runner, combined_runner,
                               global_builder, file_builder, combined_builder,
                               file_entries, function_entries, output_dir):
    """3-stage tuning: (1) global whole-project flags, (2) file-level entries on
    top of the global flags, (3) function-level entries on top of global + file.

    Writes:
      <output_dir>/global_base_flags.json  - the tuned whole-build flag list
      <output_dir>/optimization_config.json - [file entries..., function entries...]
    Replay both together, e.g. run_spec_with_config.py --base-flags @global_base_flags.json.
    """
    os.makedirs(output_dir, exist_ok=True)
    optimization_config_filepath = os.path.join(output_dir, "optimization_config.json")
    global_flags_filepath = os.path.join(output_dir, "global_base_flags.json")
    db_root = os.path.join(output_dir, "opentuner.db")

    print("=== Phase 1: Global tuning (whole-project flags) ===")
    global_config = global_tune(args, global_runner, global_builder, output_dir,
                                tuner_name="phase1_global",
                                db_dir=os.path.join(db_root, "phase1_global"))
    base_flags = global_flags_from_config(global_config, global_builder.config_generator)
    with open(global_flags_filepath, "w") as f:
        json.dump(base_flags, f, indent=2)
    print(f"Global base flags ({len(base_flags)}) written to {global_flags_filepath}")

    print("\n=== Phase 2: File-level tuning (gcc wrapper, global flags fixed) ===")
    best_file_configs = iterative_tune(
        args, file_runner, file_builder, file_entries, output_dir,
        tuner_name_prefix="phase2_", base_flags=base_flags, do_warmup_first=False,
        db_dir=os.path.join(db_root, "phase2_file")
    )

    print("\n=== Phase 3: Function-level tuning (combined wrapper + plugin, global + file fixed) ===")
    best_function_configs = iterative_tune(
        args, combined_runner, combined_builder, function_entries, output_dir,
        initial_config=best_file_configs, tuner_name_prefix="phase3_", base_flags=base_flags,
        db_dir=os.path.join(db_root, "phase3_function")
    )

    final_config = best_file_configs + best_function_configs
    with open(optimization_config_filepath, "w") as f:
        json.dump(final_config, f, indent=2)
    print(f"\nFinal combined config written to {optimization_config_filepath}")
    print(f"Apply it together with the base flags from {global_flags_filepath}")
