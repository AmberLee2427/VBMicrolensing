# Continuous Integration Matrix

The `Test Matrix` GitHub Actions workflow (`.github/workflows/test-matrix.yml`) runs
the Python test suite across a small grid of operating systems, Python versions,
and installation modes so we can monitor the behavioural drift between
distribution paths.

Current job matrix:

- `editable` install on `ubuntu-latest` (Python 3.10) exercising the in-tree build.
- `pip-wheel` installs on `ubuntu-latest`, `windows-latest`, and `macos-14`
  (Python 3.11–3.12) exercising wheels built via `python -m build`.
- `cmake-local` install on `macos-13` (Python 3.11) compiling the extension with
  CMake and exposing the repository root on `PYTHONPATH`, mirroring the most
  stable local workflow discovered so far.

Each pytest session now emits a `::notice::VBMicrolensing extension loaded from …`
log line that captures which `.so` file Python imported, making it easy to verify
the build artefact under test from the workflow logs.

Every job also uploads its full pytest output and exit code as an artifact named
`pytest-log-<os>-py<version>-<install-mode>`, so we can diff behaviours between
runs or download logs from failing builds.

## Reproducing the CMake-local job locally

```bash
python -m pip install --upgrade pip numpy "pybind11[global]" pytest
PYTHON_EXECUTABLE="$(python -c 'import sys; print(sys.executable)')"
PYBIND11_CMAKE_DIR="$(python -m pybind11 --cmakedir)"
cmake -S . -B build -DPython3_EXECUTABLE="${PYTHON_EXECUTABLE}" -Dpybind11_DIR="${PYBIND11_CMAKE_DIR}"
cmake --build build --config Release
rm -f VBMicrolensing/VBMicrolensing*.so
cp build/VBMicrolensing*.so VBMicrolensing/
PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}" python -m pytest -vv
```

The test harness (`tests/conftest.py`) will reuse any pre-existing wheel
installation by default; copying the freshly built module into
`VBMicrolensing/` and setting `PYTHONPATH` ensures the local artefact is the one
loaded during the run.
