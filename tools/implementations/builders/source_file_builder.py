import os
import subprocess

from tools.interfaces.builder import Builder


class SourceFileBuilder(Builder):
    def __init__(self, compiler_path, source_file_path, output_dir):
        self.binary_path = os.path.join(output_dir, "builder.out")
        self.build_cmd = [compiler_path, source_file_path, "-o", self.binary_path]

    def build(self, flags):
        try:
            os.makedirs(os.path.dirname(self.binary_path), exist_ok=True)
            if os.path.exists(self.binary_path):
                os.remove(self.binary_path)
            subprocess.run(self.build_cmd + flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return self.binary_path
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            self.raise_build_error(f"{str(e)}")
