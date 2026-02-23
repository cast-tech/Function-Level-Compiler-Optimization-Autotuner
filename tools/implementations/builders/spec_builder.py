import os
import shutil
import subprocess

from tools.interfaces.builder import Builder


class SPECBuilder(Builder):
    """Builder for SPEC CPU2017 intspeed benchmarks"""

    def __init__(self, spec_root, benchmark_name, config_path, output_dir, core_count, gcc_bin):
        """
        Args:
            spec_root: Root directory of SPEC CPU2017 installation
            benchmark_name: Name of the benchmark (e.g., '600.perlbench_s', '605.mcf_s')
            config_path: Path of the SPEC config file, which uses $(PLUGIN_FLAGS) variable
            output_dir: Directory for build artifacts
            core_count: Number of parallel jobs for building (default: 1)
            gcc_bin: Path to the gcc bin directory
        """
        self.spec_root = spec_root
        self.benchmark_name = benchmark_name
        self.config_path = config_path
        self.output_dir = output_dir
        self.build_dir = os.path.join(output_dir, "spec_build.dir")
        self.core_count = core_count
        self.gcc_dir = os.path.dirname(os.path.normpath(gcc_bin))


    def build(self, flags):
        shutil.rmtree(self.build_dir, ignore_errors=True)
        os.makedirs(self.build_dir, exist_ok=True)

        try:
            shrc_path = os.path.join(self.spec_root, 'shrc')
            env = os.environ.copy()
            env['PLUGIN_FLAGS'] = " ".join(flags)

            build_cmd = f". {shrc_path} && runcpu --output_root={self.build_dir} --config={self.config_path} --tune=peak --define build_ncpus={self.core_count} --define gcc_dir={self.gcc_dir} --action=build {self.benchmark_name}"
            subprocess.run(
                build_cmd,
                shell=True,
                cwd=self.spec_root,
                env=env,
                executable='/bin/bash',
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )

            return self.spec_root, self.build_dir, self.config_path, self.benchmark_name, env, self.gcc_dir

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.raise_build_error(f"{str(e)}")

        return self.build_dir
