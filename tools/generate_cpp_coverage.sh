#!/usr/bin/env bash

set -euo pipefail
IFS=$'\n\t'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build-coverage"
COVERAGE_DIR="${ROOT_DIR}/coverage"

command -v gcovr >/dev/null 2>&1 || {
  echo "gcovr is required. Install it via 'python -m pip install gcovr'." >&2
  exit 1
}

echo "Cleaning coverage build directory: ${BUILD_DIR}"
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

echo "Configuring coverage build..."
cmake -S "${ROOT_DIR}" -B "${BUILD_DIR}" \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS="--coverage" \
  -DCMAKE_SHARED_LINKER_FLAGS="--coverage" \
  -DCMAKE_EXE_LINKER_FLAGS="--coverage"

echo "Building extension with coverage instrumentation..."
cmake --build "${BUILD_DIR}" --config Debug

echo "Running pytest against coverage build..."
EXTENSION_PATH="$(find "${BUILD_DIR}" -maxdepth 1 \( -name 'VBMicrolensing*.so' -o -name 'VBMicrolensing*.pyd' \) | head -n 1)"
if [[ -z "${EXTENSION_PATH}" ]]; then
  echo "Unable to locate built extension in ${BUILD_DIR}" >&2
  exit 1
fi

(
  cd "${ROOT_DIR}"
  PYTHONPATH="${ROOT_DIR}${PYTHONPATH:+:${PYTHONPATH}}" \
  VBM_EXTENSION_OVERRIDE="${EXTENSION_PATH}" \
  PYTHONWARNINGS=ignore \
  python -m pytest -q
)

echo "Collecting gcov coverage data..."
mkdir -p "${COVERAGE_DIR}"
COMMON_ARGS=(
  --root "${ROOT_DIR}"
  --object-directory "${BUILD_DIR}"
  --filter ".*VBMicrolensing/lib/.*"
  --gcov-ignore-errors=no_working_dir_found
  --gcov-ignore-parse-errors=suspicious_hits.warn
  --exclude-directories ".*/CMakeFiles/[0-9].*"
)

gcovr "${COMMON_ARGS[@]}" \
  --html-details -o "${COVERAGE_DIR}/cpp_coverage.html"

gcovr "${COMMON_ARGS[@]}" \
  --html --html-self-contained -o "${COVERAGE_DIR}/cpp_coverage.summary.html"

gcovr "${COMMON_ARGS[@]}" --txt > "${COVERAGE_DIR}/cpp_coverage.txt"

echo "Coverage reports generated under ${COVERAGE_DIR}"
