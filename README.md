# Multi-Level Compiler Optimization Autotuner

This project profiles C/C++ programs and uses OpenTuner to search GCC optimization
settings at global, source-file, or function scope. Function settings are applied by
a GCC plugin; file settings are applied by compiler wrapper scripts.

The tools support ordinary CMake projects and SPEC CPU2017 benchmarks. They can:

- discover hot functions and source files with `perf`;
- tune functions with the GCC plugin or files with the GCC wrappers;
- tune one global GCC flag set for a SPEC benchmark;
- run a three-phase global, file, and function search;
- pin benchmark runs to selected CPUs and control parallel build jobs;
- reduce a tuned flag set while recording every evaluated configuration.

## Setup

### Requirements

- Python 3
- CMake
- GCC 15.2.0
- `perf`
- `lscpu`
- `taskset` when CPU pinning is requested
- a licensed SPEC CPU2017 installation for the `*_spec.py` commands

Initialize OpenTuner and create the Python environment from the repository root:

```shell
git submodule update --init
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install -e ./opentuner/
```

Installing this project also installs `pyelftools`, which the entry-generation
commands use to map profiled functions to source files.

### GCC 15.2.0 and the plugin

Build the supported GCC release:

```shell
./scripts/create_gcc_release.sh
```

It is created under `gcc-15.2.0-bin/`. Build the plugin with that compiler:

```shell
./plugin/build.sh ./gcc-15.2.0-bin/bin/g++
```

The resulting plugin is `plugin/build/cxx_optimizer.so`. The compiler wrappers are
in `wrappers/bin/`; pass that directory to `--gcc-wrapper-bin`.

## Optimization entries

Tuning is performed in the order entries appear in a JSON array. A function entry
requires `function_name`; `filename` and `line_number` may be added to distinguish
functions with the same name:

```json
[
  {
    "type": "function",
    "function_name": "matrix_multiply",
    "filename": "main.c",
    "line_number": 8
  }
]
```

A file entry identifies the source file name seen by the compiler wrapper:

```json
[
  {
    "type": "file",
    "filename": "source.cpp"
  }
]
```

The `create_project_*` commands generate these arrays automatically. Use
`--entries-limit` to control how many hot entries are retained.

## Generate optimization entries

Run commands from the repository root. These examples show the required arguments;
all scripts provide `--help` for workload, timeout, core-affinity, and profiling
options.

### CMake projects

Generate function entries with the plugin:

```shell
python tools/create_project_optimization_entries_function.py \
  --project-dir /path/to/project \
  --project-binary relative/path/to/binary \
  --compiler-bin ./gcc-15.2.0-bin/bin \
  --gcc-plugin ./plugin/build/cxx_optimizer.so \
  --output-dir /tmp/autotune-entries \
  --build-cores 8 \
  --cmd-args "benchmark arguments"
```

`create_project_optimization_entries.py` is the compatible function-entry command
kept for existing workflows.

Generate file entries with the compiler wrappers:

```shell
python tools/create_project_optimization_entries_file.py \
  --project-dir /path/to/project \
  --project-binary relative/path/to/binary \
  --compiler-bin ./gcc-15.2.0-bin/bin \
  --gcc-wrapper-bin ./wrappers/bin \
  --output-dir /tmp/autotune-entries \
  --build-cores 8
```

Both commands write `optimization_entries.json`.

### SPEC CPU2017

The SPEC variants are:

- `create_project_optimization_entries_function_spec.py` for function entries;
- `create_project_optimization_entries_file_spec.py` for file entries;
- `create_project_optimization_entries_file_func_spec.py` for both lists from one
  profile.

The combined command writes `file_optimization_entries.json` and
`function_optimization_entries.json`. If either file already exists in the output
directory, that list is reused and re-ranked instead of rediscovered.

```shell
python tools/create_project_optimization_entries_file_func_spec.py \
  --spec-root /path/to/cpu2017 \
  --spec-benchmark 605.mcf_s \
  --spec-config /path/to/config.cfg \
  --compiler-bin ./gcc-15.2.0-bin/bin \
  --gcc-wrapper-bin ./wrappers/bin \
  --gcc-plugin ./plugin/build/cxx_optimizer.so \
  --output-dir /tmp/spec-entries \
  --spec-core-count 8 \
  --runner-cores 2-3
```

`--runner-cores` applies the same `taskset` selection to profiling and benchmark
runs; omit it to let the operating system schedule the workload.

## Tune projects

OpenTuner options are accepted by every `tune_project_*` command. For example,
`--stop-after 100` limits a tuning stage to 100 seconds.

Every tuner also accepts `--flag-set reduced` (the default 30-flag search space)
or `--flag-set all` (the full 234-flag search space). The three-phase tuner applies
the selection consistently to its global, file, and function phases. Both shared
flag sets are maintained in `tools/services/gcc_optimization_flags.py`.

### CMake plugin and wrapper tuning

Use plugin tuning for function entries:

```shell
python tools/tune_project_gcc_plugin.py \
  --project-dir /path/to/project \
  --project-binary relative/path/to/binary \
  --compiler-bin ./gcc-15.2.0-bin/bin \
  --gcc-plugin ./plugin/build/cxx_optimizer.so \
  --optimization-entries /tmp/autotune-entries/optimization_entries.json \
  --output-dir /tmp/function-tuning \
  --build-cores 8 \
  --stop-after 100
```

`tune_project.py` is kept as a compatible name for this plugin-based CMake
workflow.

Use wrapper tuning for file entries:

```shell
python tools/tune_project_gcc_wrapper.py \
  --project-dir /path/to/project \
  --project-binary relative/path/to/binary \
  --compiler-bin ./gcc-15.2.0-bin/bin \
  --gcc-wrapper-bin ./wrappers/bin \
  --optimization-entries /tmp/autotune-entries/optimization_entries.json \
  --output-dir /tmp/file-tuning \
  --build-cores 8 \
  --stop-after 100
```

Each command writes the cumulative best entries to `optimization_config.json` and
keeps a JSON report for every tuned entry.

### SPEC tuning

The single-scope SPEC commands are:

- `tune_project_gcc_plugin_spec.py` for function-level plugin tuning;
- `tune_project_gcc_wrapper_spec.py` for file-level wrapper tuning;
- `tune_project_spec_simple.py` for one global compiler configuration.

Global tuning uses the built-in candidate list by default. Pass `--flags-file` to
provide one flag name per line; both `tree-vectorize` and `-ftree-vectorize` forms
are accepted, and blank or `#` comment lines are ignored. A custom flags file
overrides `--flag-set`.

For a complete search, `tune_project_gcc_plugin_spec_three_phase.py` runs:

1. global whole-benchmark flag tuning;
2. file tuning on top of the fixed global flags;
3. function tuning on top of the fixed global and file configurations.

```shell
python tools/tune_project_gcc_plugin_spec_three_phase.py \
  --spec-root /path/to/cpu2017 \
  --spec-benchmark 605.mcf_s \
  --spec-config /path/to/config.cfg \
  --compiler-bin ./gcc-15.2.0-bin/bin \
  --gcc-wrapper-bin ./wrappers/bin \
  --gcc-plugin ./plugin/build/cxx_optimizer.so \
  --file-entries /tmp/spec-entries/file_optimization_entries.json \
  --function-entries /tmp/spec-entries/function_optimization_entries.json \
  --output-dir /tmp/spec-tuning \
  --spec-core-count 8 \
  --runner-cores 2-3 \
  --stop-after 100
```

The three-phase tuner writes the global flags to `global_base_flags.json` and the
file/function entries to `optimization_config.json`. Use `--phase3-only` to rerun
only function tuning from those existing files.

## Reduce a tuned configuration

Reduction removes groups whose measured impact is below `--impact-threshold`, then
repeats with progressively smaller groups. It supports multi-entry configuration
files through `--entry-index` and can preserve a floor with
`--min-flags-to-keep`. Pass the same `--flag-set` used during tuning when reducing
an `all` configuration.

Reduce one plugin entry in a CMake project:

```shell
python tools/reduce_flags_gcc_plugin.py \
  --project-dir /path/to/project \
  --project-binary relative/path/to/binary \
  --compiler-bin ./gcc-15.2.0-bin/bin \
  --gcc-plugin ./plugin/build/cxx_optimizer.so \
  --optimization-config /tmp/function-tuning/optimization_config.json \
  --entry-index 0 \
  --output-dir /tmp/reduced \
  --initial-group-size 16 \
  --impact-threshold 0.1
```

Reduce flags for a standalone source file with the wrapper:

```shell
python tools/reduce_source_file_gcc_wrapper.py \
  --source-file-path /path/to/program.cpp \
  --compiler-bin ./gcc-15.2.0-bin/bin \
  --gcc-wrapper-bin ./wrappers/bin \
  --optimization-config /path/to/optimization_config.json \
  --output-dir /tmp/reduced \
  --cmd-args "benchmark arguments" \
  --stdin-file-path /path/to/input.txt \
  --runner-cores 2
```

`--stdin-file-path` is optional. `--ranked-flags-csv` accepts a CSV with `flag` and
`rank` columns and tests higher-priority flags first. Use `--retries` to repeat a
failed or noisy configuration evaluation.

Reduction produces:

- `reduced_configuration.json` and `reduced_flags.txt`;
- `reduction_summary.json`;
- `reduction_log.jsonl` and `runtime_log.csv` with every measurement.

## Other build systems

Builders, runners, and profilers implement the abstract interfaces in
`tools/interfaces`. Add an implementation in `tools/implementations` to reuse the
tuning and reduction services with another build or benchmark system.
