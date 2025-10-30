# CI Build Behaviour Report

## Overview

The GitHub Actions matrix in `.github/workflows/test-matrix.yml` now exercises
six environments:

| Label | OS / Runner | Python | Install Mode | Extension path observed in logs |
| --- | --- | --- | --- | --- |
| `ubuntu-editable` | `ubuntu-latest` | 3.10 | `pip install -e .` | `/home/runner/work/.../build/VBMicrolensing.so` |
| `ubuntu-wheel` | `ubuntu-latest` | 3.12 | `pip-wheel` (local wheel install) | `/opt/hostedtoolcache/.../site-packages/VBMicrolensing/VBMicrolensing.so` |
| `macos-wheel` | `macos-14` | 3.12 | `pip-wheel` | `/Library/Frameworks/.../site-packages/VBMicrolensing/VBMicrolensing.so` |
| `macos-cmake-13` | `macos-13` | 3.11 | `cmake-local` | `/Users/runner/work/.../build/VBMicrolensing.so` |
| `macos-cmake-15` | `macos-15` | 3.12 | `cmake-local` | `/Users/runner/work/.../build/VBMicrolensing.so` |
| `windows-wheel` | `windows-latest` | 3.11 | `pip-wheel` | `C:\hostedtoolcache\...\site-packages\VBMicrolensing\VBMicrolensing.pyd` |

Key regressions surfaced repeatedly across the suite (references point to the
tests documenting the behaviour):

- `BinaryLightCurveKepler` still returns static magnifications and NaN offsets,
  failing the orbital-signal expectation (`tests/test_vbmicrolensing_expectations.py:32`).
  The `cmake-local` job additionally times out in the parity test before we xfail
  it (`tests/test_vbmicrolensing.py:126`).
- `CombineCentroids` disagrees between build artefacts: wheels produce NaNs,
  while locally built extensions collapse to zero offsets
  (`tests/test_vbmicrolensing_expectations.py:61`, `tests/test_vbmicrolensing_expectations.py:107`).
- Switching the contour solver with `SetMethod` continues to segfault before
  `MultiMag2` returns (`tests/test_vbmicrolensing_expectations.py:143`).
- `BinaryMagMultiDark` still aborts the interpreter when exercised through the
  bindings (`tests/test_vbmicrolensing_expectations.py:125`).
- `BinaryLightCurveOrbital` returns two distinct result sets depending on which
  shared object is imported (`TODO.md:8`); the suite currently accepts either
  outcome (`tests/test_vbmicrolensing.py:159`).

## Environment-by-Scenario Matrix

`✓` indicates an expected pass, `✗` names the failure mode observed in CI,
`~` marks skips due to the harness not being able to exercise the scenario. Xfail
rows are considered signal: we deliberately keep those tests so the logs record
the regression.

| Scenario | ubuntu-editable (3.10) | ubuntu-wheel (3.12) | macos-wheel (3.12) | macos-cmake-13 (3.11) | macos-cmake-15 (3.12) | windows-wheel (3.11) |
| --- | --- | --- | --- | --- | --- | --- |
| `BinaryLightCurveKepler` orbital signal (`tests/test_vbmicrolensing_expectations.py::test_binary_light_curve_kepler_has_orbital_signal`) | ✗ static mags + NaNs | ✗ static mags + NaNs | ✗ static mags + NaNs | ✗ static mags + NaNs | ✗ static mags + NaNs | ✗ static mags + NaNs |
| `BinaryLightCurveKepler` parity suite (`tests/test_vbmicrolensing.py::test_parallax_and_orbital_light_curves`) | ✓ returns static branch | ✓ returns static branch | ✓ returns orbital branch | ✗ times out (xfail) | ✗ times out (xfail) | ✓ returns orbital branch |
| `BinaryLightCurveOrbital` outputs (`tests/test_vbmicrolensing.py::test_parallax_and_orbital_light_curves`) | Static magnification path | Static magnification path | Orbital solver path¹ | Static magnification path | Static magnification path | Orbital solver path¹ |
| `CombineCentroids` with wheel extension (`tests/test_vbmicrolensing_expectations.py::test_combine_centroids_returns_finite_series`) | ✗ NaNs (xfail) | ✗ NaNs (xfail) | ✗ NaNs (xfail) | ~ skipped (no wheel artefact on path) | ~ skipped (no wheel artefact on path) | ✗ NaNs (xfail) |
| `CombineCentroids` with local build (`tests/test_vbmicrolensing_expectations.py::test_combine_centroids_returns_finite_series_local`) | ✗ zero offsets (xfail) | ~ skipped (no local artefact) | ✗ zero offsets (xfail) | ✗ zero offsets (xfail) | ✗ zero offsets (xfail) | ~ skipped (no local artefact) |
| `BinaryMagMultiDark` subprocess guard (`tests/test_vbmicrolensing_expectations.py::test_binary_mag_multi_dark_populates_outputs`) | ✗ interpreter abort (xfail) | ✗ interpreter abort (xfail) | ✗ interpreter abort (xfail) | ✗ interpreter abort (xfail) | ✗ interpreter abort (xfail) | ✗ interpreter abort (xfail) |
| `SetMethod` → `MultiMag2` (`tests/test_vbmicrolensing_expectations.py::test_set_method_multi_mag2_stability`) | ✗ segfault before return (xfail) | ✗ segfault before return (xfail) | ✗ segfault before return (xfail) | ✗ segfault before return (xfail) | ✗ segfault before return (xfail) | ✗ segfault before return (xfail) |

Notes:

- Wheel jobs delete the `build/` tree before running pytest so the discovery
  logic exercises the site-packages wheel rather than the in-tree artefact.
- Windows now participates in the CombineCentroids wheel check because
  `_discover_extension_candidates` accepts `.pyd` modules; the local-only test
  still skips on wheel jobs where no build artefact exists.
- macOS-13 runners are flagged for deprecation, so the matrix also runs the
  CMake scenario on `macos-15`; both exhibit the same Kepler timeout and orbital
  static-path behaviour for now.

¹ Behaviour taken from the reproducible discrepancy noted in `TODO.md:8`; the
  tests accept either branch to keep both builds green.

## Suggested Bug Report Outline

1. **Title:** “Divergent VBMicrolensing behaviours across wheel vs local builds”
2. **Summary:** Briefly list the major discrepancies (Kepler orbital solver,
   CombineCentroids, SetMethod, BinaryMagMultiDark) with links to the tests and
   CI logs under `tests/CI logs/03b338d-test_matrix/`.
3. **Impact:** Mention that users installing from PyPI see different scientific
   outputs (NaNs, orbital curves) than collaborators running CMake builds,
   leading to inconsistent modelling results and sporadic crashes.
4. **Reproduction:** Provide the relevant pytest invocation snippets per build
   style (`pip install -e .`, wheel install, CMake + `PYTHONPATH`).
5. **Attachments:** Include or link to the captured logs and the matrix table
   above so non-pytest users can scan the outcomes quickly.

Once Valerio (or other collaborators) are ready to dig into a specific failure,
the xfail markers in the code point directly at the minimal reproductions used
by the test suite. Feel free to reference the table in future issues when
triaging platform-specific bug reports.
