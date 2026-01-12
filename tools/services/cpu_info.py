import subprocess


def get_cpu_info():
    try:
        lscpu_output = subprocess.run(['lscpu'], capture_output=True, text=True, check=True).stdout
        cpu_info = {}

        for line in lscpu_output.splitlines():
            if ':' in line:
                key, value = map(str.strip, line.split(":", 1))
                cpu_info[key] = value

        return cpu_info

    except FileNotFoundError:
        return "lscpu command not found. Please install lscpu"

    except subprocess.CalledProcessError as e:
        return f"An error occurred while running lscpu: {e}"
