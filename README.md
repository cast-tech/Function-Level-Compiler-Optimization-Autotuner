# Function Level Compiler Optimization Autotuner

A collection of tools for function/file level GCC optimization tuning.
The tool uses the OpenTuner API for iterative optimization selection and a GCC Plugin to apply those optimizations
during compilation.

## Setup

### Requirements

Install the following dependencies:

- python3
- cmake
- perf
- lscpu

### GCC Release

The auto-tuner is designed to run with **GCC 15.2.0**.
To build the specified GCC version, run the following script from the project root directory:

```shell
./scripts/create_gcc_release.sh
```

GCC release will be created in `gcc-15.2.0-bin/` directory.

### GCC Plugin

The GCC plugin enables easy application of function-level and file-level optimizations during compilation.

To build the plugin, run:
```shell
./plugin/build.sh /path/to/gcc-15.2.0-bin/bin/g++
```

The compiled plugin will be located at `plugin/build/cxx_optimizer.so`.
### Virtual Environment

To set up a virtual environment, run the following commands from the project root directory:

```shell
python3 -m venv venv
source ./venv/bin/activate
pip3 install -e .
pip3 install -e ./opentuner/
```

## Autotuning Scripts

Run the scripts from the `tools` directory.

### tune_project.py

This Python script uses the OpenTuner API to iteratively tune GCC optimizations at the function or file level in C/C++
cmake project.
The optimizations are applied using a GCC Plugin.
After tuning, a JSON report files will be generated containing the results of the tuner's execution.

```shell
python3 tune_project.py --project-dir /path/to/project --project-binary binary_name --compiler-bin /path/to/gcc-15.2.0-bin/bin/ --gcc-plugin /path/to/plugin/build/cxx_optimizer.so --optimization-entries /path/to/optimization_entries.json --output-dir /path/to/output/ --stop-after 100
```

The optimization entries file is a JSON file specifying which functions or files need to be auto-tuned and the order in
which the auto-tuning is performed.

**Optimization entries file example for function-level tuning:**

```json
[
  {
    "type": "function",
    "filename": "main.c",
    "function_name": "matrix_multiply",
    "line_number": 8
  },
  {
    "type": "function",
    "filename": "main.c",
    "function_name": "compute_series",
    "line_number": 21
  }
]
```

During function-level auto-tuning, the `filename` key specifies the file containing the function definition, and
`line_number` specifies the line where the function name appears within that file.

**Optimization entries file example for file-level tuning:**

```json
[
  {
    "type": "file",
    "filename": "source.cpp"
  },
  {
    "type": "file",
    "filename": "util.cpp"
  }
]
```

During file-level auto-tuning, `filename` refers to the main input file being compiled.

### create_project_optimization_entries.py

This Python script uses profiler to collect function-level program runtimes and create optimal function-level
optimization entries for a specified cmake project.

```shell
python3 create_project_optimization_entries.py --project-dir /path/to/project --project-binary binary_name --compiler-bin /path/to/gcc-15.2.0-bin/bin/ --gcc-plugin /path/to/plugin/build/cxx_optimizer.so --output-dir /path/to/output/
```

### Support for other build systems

The scripts described above use abstract interfaces (`builder`, `runner`, and `profiler`) defined in
`tools/interfaces`. This design allows the scripts to work with different build systems through specific
implementations.

The `tools/implementations` directory contains implementations for build systems beyond CMake. To adapt the scripts
for a new build system, simply provide a concrete implementation of these interfaces for that system.
