Shadow-variable matrix runner
=============================

Purpose
-------
This small harness builds the project multiple times (different compilers/flags), runs a user-provided test command that exercises the behavior you want to validate (for example, the test in your `fix-astr-data-packaging` branch that reproduces the shadowed-variable problem), and records the outputs.

How it works
------------
- Edit `tools/shadow_matrix/config.yml` to list the compilers/flags you want to test.
- Provide a run command that executes the test (the command is run from the repository root).
- The script will create `build/matrix/<entry>` build directories, build the project with CMake, run the provided command, and write results into `results/`.

Example
-------
From the repository root:

```bash
python tools/shadow_matrix/run_matrix.py \
  --config tools/shadow_matrix/config.yml \
  --run-cmd "python -m pytest tests/test_shadow_case.py -q" \
  --baseline results/baseline.txt
```

Notes and tips
--------------
- The runner does not try to install Python wheels; the run-cmd should import your package from the source tree or run any binaries produced by CMake. Commonly, your run-cmd can be a pytest that imports the extension built in the build tree (set `PYTHONPATH` appropriately inside the test) or a small executable produced by CMake.
- If you need to use a compiler not on the default PATH, put the absolute compiler path in `config.yml`.
- The script prefers `cmake` and assumes a typical CMake project layout. If your project has custom steps, make the run-cmd perform them.
- On macOS, if Python extension loading fails due to library path issues, you may need to adjust `DYLD_LIBRARY_PATH` or explicitly copy built .so into a test-friendly location.

If you want, I can:
- Add a small CMake target that builds a standalone test executable which the runner can call directly (makes runtime invocation simpler). (Say: "Add test executable target")
- Wire the specific test from your `fix-astr-data-packaging` branch into the harness so it's runnable with the matrix (Say: "Wire branch test")
