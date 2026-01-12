#!/bin/bash

GCC_VERSION="15.2.0"
GCC_NAME="gcc-${GCC_VERSION}"
GCC_TAR="${GCC_NAME}.tar.gz"
GCC_URL="https://ftp.gnu.org/gnu/gcc/${GCC_NAME}/${GCC_TAR}"

GCC_TUNER_DIR=$(dirname "$(dirname "$(readlink -f "$0")")")
GCC_INSTALL_DIR="${GCC_TUNER_DIR}/${GCC_NAME}-bin"

cores=$(nproc)
half_cores=$((cores / 2))

if [ "$half_cores" -eq 0 ]; then
    half_cores=1
fi

if [ -d "$GCC_INSTALL_DIR" ]; then
    echo "GCC release already exists..."
    exit 0
fi

echo "Installing dependencies..."
if command -v apt-get &>/dev/null; then
    apt-get update
    apt-get install -y build-essential libgmp-dev libmpfr-dev libmpc-dev flex bison texinfo wget
elif command -v dnf &>/dev/null; then
    dnf install -y gcc gcc-c++ gmp-devel mpfr-devel libmpc-devel flex bison texinfo wget
elif command -v yum &>/dev/null; then
    yum update -y
    yum install -y gcc gcc-c++ gmp-devel mpfr-devel libmpc-devel flex bison texinfo wget
else
    echo "Error: No supported package manager found (apt, dnf, or yum)."
    exit 1
fi

if [ ! -f "${GCC_TUNER_DIR}/${GCC_TAR}" ]; then
    echo "Downloading GCC ${GCC_VERSION}..."
    wget -P "$GCC_TUNER_DIR" "$GCC_URL"
else
    echo "GCC ${GCC_VERSION} source already downloaded."
fi

echo "Extracting GCC ${GCC_VERSION}..."
tar -xzf "${GCC_TUNER_DIR}/${GCC_TAR}" -C "$GCC_TUNER_DIR"
cd "${GCC_TUNER_DIR}/${GCC_NAME}" || exit 1

echo "Downloading prerequisite libraries..."
./contrib/download_prerequisites

echo "Creating build directory..."
mkdir build
cd build || exit 1

echo "Configuring the build..."
mkdir "$GCC_INSTALL_DIR" || exit 1
../configure --prefix="$GCC_INSTALL_DIR" --enable-languages=c,c++,fortran --disable-multilib --disable-libsanitizer

echo "Building GCC ${GCC_VERSION}..."
make -j"$half_cores" || exit 1

echo "Installing GCC ${GCC_VERSION}..."
make install || exit 1
