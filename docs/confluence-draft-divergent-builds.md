# Using unit tests to reveal divergent VBMicrolensing behaviours across wheel vs local builds

## Summary
- VBMicrolensing’s Python layer wraps a C++ contour-integration engine. How that binary extension is compiled (PyPI wheel vs. local CMake build) drives distinct scientific results and failure modes.
- A GitHub Actions matrix run (`https://github.com/AmberLee2427/VBMicrolensing/actions/runs/18956497837`) highlighted repeatable divergences: `BinaryLightCurveKepler` falls back to static magnifications, `BinaryLightCurveOrbital` splits into two families of outputs, and several advanced routines (`CombineCentroids`, `BinaryMagMultiDark`, `SetMethod → MultiMag2`) become unusable under specific build artefacts.
- The behaviours are now captured in the repository’s regression tests, providing reproducible evidence for maintainers and guidance for users choosing an install path.

## Impact
- **Science outputs:** Users installing from wheels (e.g. `pip install VBMicrolensing`) can receive different magnifications, centroid shifts, or NaNs compared with collaborators who build the extension with CMake. This undermines cross-team result reproducibility.
- **Stability:** Some code paths still crash the interpreter (`BinaryMagMultiDark`, `SetMethod` with `Multipoly/Nopoly`) regardless of platform, blocking adoption of those features.
- **Operations:** We now have automated visibility into these discrepancies. The xfailed tests act as sentinels; when behaviour changes, CI logs will show it immediately.

## Methodology & Coverage
- **Test harness:** `pytest` suites under `tests/` load the VBMicrolensing extension, exercise parity checks (basic magnifications, orbital motion) and “expectation” checks designed to catch historic bugs.
- **Matrix of environments:** The workflow covers six combinations (Ubuntu editable & wheel; macOS wheels; macOS CMake builds on 13 & 15; Windows wheel). Each job records which shared object (`.so`/`.pyd`) was imported so we can confirm the build path taken.
- **What we measured:**
  - Binary light curves in static vs. orbital regimes (`tests/test_vbmicrolensing.py::test_parallax_and_orbital_light_curves`).
  - Astrometric centroid combination with both wheel-built and locally built extensions (`tests/test_vbmicrolensing_expectations.py::test_combine_centroids_*`).
  - Contour-solver switching via `SetMethod`, limb-darkened magnification routines, and the Keplerian solver regressions (`tests/test_vbmicrolensing_expectations.py` suite).
- **Local verification:** Post-run, the repository was at commit `413a55ef759e14d4605914cd5a32f18e55e19ba1`, ensuring the report aligns with the code snapshot visible to the collaboration.

## Reproduction
1. Clone `https://github.com/valboz/VBMicrolensing` and checkout commit `413a55ef759e14d4605914cd5a32f18e55e19ba1`.
2. Decide on the build style:
   - **Editable/local build:** `pip install -e .`
   - **Wheel-style install:** `python -m build --wheel && pip install dist/*.whl`
   - **macOS CMake workflow:** `cmake -S . -B build -DPython3_EXECUTABLE=$(which python)` then `cmake --build build --config Release`, copy `build/VBMicrolensing*.so` into `VBMicrolensing/` and set `PYTHONPATH=$PWD`.
3. Run `pytest -vv`. The harness will emit `::notice::VBMicrolensing extension loaded from …` so you can confirm which module was exercised.
4. Inspect failing/xfailed tests for reproduction snippets that isolate each bug.

## Links & Artifacts
- Repository snapshot: <https://github.com/valboz/VBMicrolensing/tree/413a55ef759e14d4605914cd5a32f18e55e19ba1>
- GitHub Actions run (ID 18956497837): <https://github.com/AmberLee2427/VBMicrolensing/actions/runs/18956497837>
- Test logs (ZIP artifacts, aligned with the workflow job order):
  1. <https://github.com/AmberLee2427/VBMicrolensing/actions/runs/18956497837/artifacts/4423758033>
  2. <https://github.com/AmberLee2427/VBMicrolensing/actions/runs/18956497837/artifacts/4423753576>
  3. <https://github.com/AmberLee2427/VBMicrolensing/actions/runs/18956497837/artifacts/4423753771>
  4. <https://github.com/AmberLee2427/VBMicrolensing/actions/runs/18956497837/artifacts/4423753820>
  5. <https://github.com/AmberLee2427/VBMicrolensing/actions/runs/18956497837/artifacts/4423753637>
  6. <https://github.com/AmberLee2427/VBMicrolensing/actions/runs/18956497837/artifacts/4423758931>
- In-repo build behaviour snapshot: `docs/build-behaviour-report.md`
