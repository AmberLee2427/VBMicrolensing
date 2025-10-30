# Build Behaviour Snapshot

This note records what we see when the GitHub Actions workflow
`.github/workflows/test-matrix.yml` runs. VBMicrolensing (VBM) is a C++ engine
for microlensing calculations that we drive from Python through a compiled
extension module. Depending on how that extension is built we surface different
bugs, so the workflow exercises the major installation styles:

- **Editable install** (`pip install -e .`): Python loads the module that CMake
  or scikit-build put under `build/`.
- **Wheel install** (`python -m build && pip install dist/*.whl`): Python loads
  the pre-built module that would ship on PyPI.
- **CMake local build** (`cmake … && PYTHONPATH=repo pytest`): we mimic the
  manual build that many collaborators use on macOS to pick up the more stable
  solver configuration; this can select different compilers or optimisations
  compared with the wheel.

## Current matrix (run id `7a73372`)

| Label | OS / runner | Python | Install style | Extension loaded |
| --- | --- | --- | --- | --- |
| `ubuntu-editable` | `ubuntu-latest` | 3.10 | editable | `/home/runner/work/.../build/VBMicrolensing.so` |
| `ubuntu-wheel` | `ubuntu-latest` | 3.12 | wheel | `/opt/hostedtoolcache/.../site-packages/VBMicrolensing/VBMicrolensing.so` |
| `macos-wheel` | `macos-14` | 3.12 | wheel | `/Library/Frameworks/.../site-packages/VBMicrolensing/VBMicrolensing.so` |
| `macos-cmake-13` | `macos-13` | 3.11 | cmake-local | `/Users/runner/work/.../build/VBMicrolensing.so` |
| `macos-cmake-15` | `macos-15` | 3.12 | cmake-local | `/Users/runner/work/.../build/VBMicrolensing.so` |
| `windows-wheel` | `windows-latest` | 3.11 | wheel | `C:\hostedtoolcache\...\site-packages\VBMicrolensing\VBMicrolensing.pyd` |

All logs for the run live under `tests/CI logs/7a73372-test_matrix/`.

## Highlights in plain language

- **BinaryLightCurveKepler (Keplerian binary light curve)**  
  Every build still falls back to the flat, static solution with NaN offsets.
  On the macOS CMake builds the solver now also stalls long enough for our
  guard to xfail (`tests/test_vbmicrolensing.py:126`).

- **BinaryLightCurveOrbital**  
  The same inputs produce two families of answers: wheels (site-packages) use
  the full orbital solver, while editable / CMake builds stick to the static
  branch noted in `TODO.md:8`. The regression test accepts either set so that
  both behaviours are documented but the suite still finishes.

- **CombineCentroids (astrometric centroid combiner)**  
  Wheels on Linux, macOS, and Windows return NaNs; locally compiled modules
  collapse to zeros. Both outcomes remain marked xfail so we keep collecting the
  failure codes.

- **BinaryMagMultiDark (limb-darkened magnifications)**  
  Calling this through the Python wrapper still causes Python itself to exit
  abruptly (process abort). The expectation test stays xfailed so we can keep
  spotting that regression.

- **SetMethod → MultiMag2 (switching contour solvers)**  
  Flipping `SetMethod` to `Multipoly` or `Nopoly` still crashes before we get a
  magnification back. Every environment hits the same fault.

## Scenario-by-scenario table

Legend: “OK” means the parity test currently passes, “Fail” gives the symptom
we observe, and “n/a” means the environment cannot exercise that path (for
example because no local build artefact exists).

| Scenario | ubuntu-editable (3.10 editable) | ubuntu-wheel (3.12 wheel) | macos-wheel (3.12 wheel) | macos-cmake-13 (3.11 CMake) | macos-cmake-15 (3.12 CMake) | windows-wheel (3.11 wheel) |
| --- | --- | --- | --- | --- | --- | --- |
| `BinaryLightCurveKepler` orbital signal (`tests/test_vbmicrolensing_expectations.py::test_binary_light_curve_kepler_has_orbital_signal`) | Fail – stays at static mags, NaNs | Fail – stays at static mags, NaNs | Fail – stays at static mags, NaNs | Fail – stays at static mags, NaNs | Fail – stays at static mags, NaNs | Fail – stays at static mags, NaNs |
| `BinaryLightCurveKepler` parity suite (`tests/test_vbmicrolensing.py::test_parallax_and_orbital_light_curves`) | OK – static branch | OK – static branch | OK – orbital branch | Fail – solver stalls (xfail) | Fail – solver stalls (xfail) | OK – orbital branch |
| `BinaryLightCurveOrbital` outputs (`tests/test_vbmicrolensing.py::test_parallax_and_orbital_light_curves`) | Static branch | Static branch | Orbital branch¹ | Static branch | Static branch | Orbital branch¹ |
| `CombineCentroids` with wheel module (`tests/test_vbmicrolensing_expectations.py::test_combine_centroids_returns_finite_series`) | Fail – NaNs (xfail) | Fail – NaNs (xfail) | Fail – NaNs (xfail) | n/a | n/a | Fail – NaNs (xfail) |
| `CombineCentroids` with local module (`tests/test_vbmicrolensing_expectations.py::test_combine_centroids_returns_finite_series_local`) | Fail – zeros (xfail) | n/a | Fail – zeros (xfail) | Fail – zeros (xfail) | Fail – zeros (xfail) | n/a |
| `BinaryMagMultiDark` subprocess guard (`tests/test_vbmicrolensing_expectations.py::test_binary_mag_multi_dark_populates_outputs`) | Fail – Python exits (xfail) | Fail – Python exits (xfail) | Fail – Python exits (xfail) | Fail – Python exits (xfail) | Fail – Python exits (xfail) | Fail – Python exits (xfail) |
| `SetMethod` then `MultiMag2` (`tests/test_vbmicrolensing_expectations.py::test_set_method_multi_mag2_stability`) | Fail – crash before return (xfail) | Fail – crash before return (xfail) | Fail – crash before return (xfail) | Fail – crash before return (xfail) | Fail – crash before return (xfail) | Fail – crash before return (xfail) |

¹ Matches the discrepancy described in `TODO.md:8`; we allow both answers in the
regression test so that runs on either build style continue to report useful
results.

## Using this information

- When filing a bug or responding to user reports, note which build method they
  used. Pip wheels (PyPI installs) and local CMake builds have different failure
  modes.
- The artefacts uploaded by the workflow (`pytest-log-<os>-py<version>-<mode>`)
  contain the full test output for each environment if deeper triage is needed.
- If you reproduce one of these issues locally, copy the relevant snippet from
  the tests listed in the table—they are the shortest scripts we have that hit
  each bug.
