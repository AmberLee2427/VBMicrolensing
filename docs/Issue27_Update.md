# TripleAstroLightCurve Test Matrix (Issue #27)

I created `tests/test_triple_astro_lightcurve_envs.py` as a reproducible record of how `TripleAstroLightCurve` behaves in the different environments. Running the suite documents both the success cases and the crash scenarios.

## Set-up

1. Add the folowwing 3 lies to the end of the `pyroject.toml`.

    ```toml
    [tool.pytest.ini_options]
    addopts = "-ra"
    testpaths = ["tests"]
    ```

2. Ensure that `pytest` is installed in your python environment.

3. Create a `test` directory in the repo root and add the attached test script to it.

## Running the test

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_triple_astro_lightcurve_envs.py
```

> `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` tells pytest not to auto-load any globally installed plugins. We hit segfaults from third-party plugins in this codebase, so disabling auto-discovery keeps the run deterministic.

## Scenarios covered by the test

| Scenario ID | Description | Expected Result |
|-------------|-------------|-----------------|
| `wheel-triple-lightcurve` | Imports the already installed wheel and exercises the non-astrometric `TripleLightCurve` path. Baseline sanity check that the wheel itself loads and the simple call completes. | ✅ Passes |
| `repo-triple-astro-localbuild` | Mirrors Valerio’s presumed workflow: repo checkout on `PYTHONPATH`, CMake-built `VBMicrolensing.so` copied into `VBMicrolensing/`. Confirms Greg’s script succeeds when run from that environment. | ✅ Passes |
| `wheel-triple-astro` | Imports the installed wheel but runs the full astrometric call. This is exactly the setup Greg reported (conda install, no local build). | ❌ `xfail` — still segfaults |
| `repo-triple-astro` | Repo checkout on `PYTHONPATH` but relies on the wheel’s compiled module instead of the local CMake build (i.e., what Greg tried after Valerio’s comment). | ❌ `xfail` — still segfaults |

With the CMake build present (`VBMicrolensing/VBMicrolensing.so`), the run currently reports:

```
======================================= test session starts =======================================
platform darwin -- Python 3.12.2, pytest-8.4.1, pluggy-1.6.0
rootdir: /Users/malpas.1/Code/VBMicrolensing
configfile: pyproject.toml
collected 4 items                                                                                 

tests/test_triple_astro_lightcurve_envs.py .x.x                                             [100%]

===================================== short test summary info =====================================
XFAIL tests/test_triple_astro_lightcurve_envs.py::test_triple_lightcurve_contexts[wheel-triple-astro] - TripleAstroLightCurve still crashes when using the installed wheel
XFAIL tests/test_triple_astro_lightcurve_envs.py::test_triple_lightcurve_contexts[repo-triple-astro] - TripleAstroLightCurve still crashes when run from the repo checkout
================================== 2 passed, 2 xfailed in 0.40s ===================================
```

So:

- Valerio’s “build from checkout” setup (local CMake build + repo path) is green (`repo-triple-astro-localbuild`).
- The packaged wheel remains the problem (`wheel-triple-astro`, `repo-triple-astro`), which matches Greg’s report.

I have attached `tests/test_triple_astro_lightcurve_envs.py` so the above matrix is easy to reproduce.  From there, I guess fixing the remaining crashes comes down to tightening the wheel packaging / runtime guards so the installed artefact behaves like the local build.

## Summary

Both Greg and Valerio’s behaviours are reproducible from the same sources: the `CMake` build + repo checkout succeeds, whereas the wheel built by `scikit-build-core`/`cibuildwheel` still segfaults. The remaining bug sits in how the packaged artefact is produced or initialised at runtime, not in the core C++ logic.
