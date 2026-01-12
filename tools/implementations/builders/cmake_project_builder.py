import os
import shutil
import subprocess

from gcc.tools.interfaces.builder import Builder


class CMakeProjectBuilder(Builder):
    @staticmethod
    def get_flags_to_set_compiler_in_cmake(compiler_bin_dir):
        gcc_cpp_path = os.path.join(compiler_bin_dir, 'g++')
        gcc_c_path = os.path.join(compiler_bin_dir, 'gcc')
        return [f"-DCMAKE_CXX_COMPILER={gcc_cpp_path}", f"-DCMAKE_C_COMPILER={gcc_c_path}"]

    def __init__(self, compiler_bin_dir, project_dir, output_dir, binary_name, core_count=1):
        self.flags_to_set_compiler = CMakeProjectBuilder.get_flags_to_set_compiler_in_cmake(compiler_bin_dir)
        self.build_dir = os.path.join(output_dir, "builder.dir")
        self.project_dir = project_dir
        self.binary_path = os.path.join(self.build_dir, binary_name)
        self.core_count = core_count

    def build(self, flags):
        shutil.rmtree(self.build_dir, ignore_errors=True)
        os.makedirs(self.build_dir, exist_ok=True)
        try:
            flags_str = " ".join(flags)
            cmake_cmd = ["cmake", "-DCMAKE_BUILD_TYPE=Release",
                         f"-DCMAKE_C_FLAGS={flags_str}", f"-DCMAKE_CXX_FLAGS={flags_str}",
                         "-DCMAKE_CXX_FLAGS_RELEASE=", "-DCMAKE_C_FLAGS_RELEASE=",
                         "-S", self.project_dir, "-B", self.build_dir] + self.flags_to_set_compiler
            subprocess.run(cmake_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            build_cmd = ["cmake", "--build", self.build_dir, "--", f"-j{self.core_count}"]
            subprocess.run(build_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.raise_build_error(f"{str(e)}")
        return self.binary_path
