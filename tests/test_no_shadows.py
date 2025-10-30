"""Pytest that fails if any clang-diagnostic-shadow warnings are found.

This test calls the helper script tools/clang_tidy_check.py. It requires a working
clang-tidy binary and a valid build/compile_commands.json file (CMake with
-DCMAKE_EXPORT_COMPILE_COMMANDS=ON).
"""
import subprocess
import sys
from pathlib import Path


def test_no_shadow_diagnostics():
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "tools" / "clang_tidy_check.py"
    assert script.exists(), "clang_tidy_check.py not found in tools/"

    cmd = [sys.executable, str(script), "--compile-commands", str(repo_root / "build" / "compile_commands.json")]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out = proc.stdout
    # Exit code 1 means shadow diagnostics were found; 0 means none; 2 means tool/setup error
    if proc.returncode == 2:
        pytest_msg = (
            "clang-tidy or compile_commands.json not found — ensure clang-tidy is installed and CMake was run with -DCMAKE_EXPORT_COMPILE_COMMANDS=ON"
        )
        raise RuntimeError(pytest_msg)
    assert proc.returncode == 0, f"Shadow diagnostics detected:\n{out}"
