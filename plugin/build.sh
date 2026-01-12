#!/bin/bash -e

if [ -z "$1" ]; then
    echo "Error: Path to g++ compiler must be provided as the first argument." >&2
    exit 1
fi

GCC_PATH="$1"
if [ ! -x "$GCC_PATH" ]; then
    echo "Error: '$GCC_PATH' does not exist or is not an executable file." >&2
    exit 1
fi

SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
BUILD_DIR="$SCRIPT_DIR/build"

rm -rf "$BUILD_DIR"
mkdir "$BUILD_DIR"

cmake -DCMAKE_CXX_COMPILER="$GCC_PATH" -S "$SCRIPT_DIR" -B "$BUILD_DIR"
if [ $? -ne 0 ]; then
    echo "Error: CMake configuration failed." >&2
    exit 1
fi

cmake --build "$BUILD_DIR"
if [ $? -ne 0 ]; then
    echo "Error: Plugin build failed." >&2
    exit 1
fi
