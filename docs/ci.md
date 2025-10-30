# Continuous Integration Matrix

The `Test Matrix` GitHub Actions workflow (`.github/workflows/test-matrix.yml`) runs
the Python test suite across a small grid of operating systems, Python versions,
and installation modes so we can monitor the behavioural drift between
distribution paths.

Current job matrix:

- `editable` install on `ubuntu-latest` (Python 3.10) exercising the in-tree build.
- `pip-wheel` install on `ubuntu-latest` (Python 3.12) forcing the wheel path after
  removing `build/` so the site-packages module is imported.
- `pip-wheel` install on `macos-14` (Python 3.12) covering the wheel behaviour on Apple silicon.
- `pip-wheel` install on `windows-latest` (Python 3.11) covering the `.pyd` wheel.
- `cmake-local` installs on `macos-13` (Python 3.11) and `macos-15` (Python 3.12),
  both compiling the extension with CMake and exposing the repository root on
  `PYTHONPATH`, mirroring the most stable local workflow discovered so far.

Each pytest session now emits a `::notice::VBMicrolensing extension loaded from …`
log line that captures which `.so` file Python imported, making it easy to verify
the build artefact under test from the workflow logs.

Every job also uploads its full pytest output and exit code as an artifact named
`pytest-log-<os>-py<version>-<install-mode>`, so we can diff behaviours between
runs or download logs from failing builds.

`tests/test_vbmicrolensing_expectations.py` now considers `.pyd`, `.dylib`, and
`.dll` extensions as part of its discovery routine so the Windows wheel job
exercises the CombineCentroids failure mode.

The workflow exports `VBM_BUILD_STYLE=<install-mode>` before running pytest.
`tests/test_vbmicrolensing.py::test_parallax_and_orbital_light_curves` relies on
this value to mark the macOS `cmake-local` build as an expected failure while
`BinaryLightCurveKepler` remains stuck in the CMake artefact.

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
