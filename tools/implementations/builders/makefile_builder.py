import os
import shutil
import subprocess

from tools.interfaces.builder import Builder


class MakefileBuilder(Builder):
    def __init__(self, compiler_bin_dir, project_dir, output_dir, binary_name, core_count=1, makefile_name="Makefile"):
        self.compiler_bin_dir = compiler_bin_dir
        self.build_dir = os.path.join(output_dir, "builder.dir")
        self.project_dir = project_dir
        self.binary_name = binary_name
        self.binary_path = os.path.join(self.build_dir, binary_name)
        self.core_count = core_count
        self.makefile_name = makefile_name

    def build(self, flags):
        shutil.rmtree(self.build_dir, ignore_errors=True)
        os.makedirs(self.build_dir, exist_ok=True)

        try:
            env = os.environ.copy()
            env['CC'] = os.path.join(self.compiler_bin_dir, 'gcc')
            env['CXX'] = os.path.join(self.compiler_bin_dir, 'g++')
            env['CFLAGS'] = " ".join(flags)
            env['CXXFLAGS'] = " ".join(flags)

            shutil.copytree(self.project_dir, self.build_dir, dirs_exist_ok=True)

            make_cmd = ["make", "-f", self.makefile_name, "-j", str(self.core_count)]
            subprocess.run(
                make_cmd,
                cwd=self.build_dir,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.raise_build_error(f"{str(e)}")

        return self.binary_path
