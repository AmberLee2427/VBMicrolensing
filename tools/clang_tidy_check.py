#!/usr/bin/env python3
"""
Run clang-tidy (clang-diagnostic-shadow) across the compile_commands.json
and return a non-zero exit code if any shadow diagnostics are found.

Usage:
  python tools/clang_tidy_check.py [--clang-tidy /path/to/clang-tidy] [--compile-commands build/compile_commands.json]

This script is intended to be used in CI or as a local check. It prints a summary
and exits with code 1 if any shadowing diagnostics are detected.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def find_clang_tidy() -> str:
    # Allow override via env var first
    path = os.environ.get("CLANG_TIDY")
    if path:
        return path
    # Common Homebrew location
    brew_path = "/opt/homebrew/opt/llvm/bin/clang-tidy"
    if Path(brew_path).exists():
        return brew_path
    # Fallback to PATH
    return "clang-tidy"


def read_compile_commands(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    for entry in data:
        # Only consider C/C++ source files
        fname = entry.get("file") or entry.get("command")
        if not fname:
            continue
        if fname.endswith(('.c', '.cpp', '.cc', '.cxx', '.m', '.mm', '.h', '.hpp')):
            yield entry["file"]


def macos_sdk_path() -> str | None:
    try:
        out = subprocess.check_output(["xcrun", "--sdk", "macosx", "--show-sdk-path"], text=True)
        return out.strip()
    except Exception:
        return None


def run_clang_tidy_on_file(clang_tidy: str, file: str, build_path: str | None,
                           extra_args: list[str], extra_args_before: list[str]) -> str:
    cmd = [clang_tidy, file, "-checks=-*,clang-diagnostic-shadow", "-quiet"]
    for arg in extra_args_before:
        cmd.extend(["--extra-arg-before", arg])
    for arg in extra_args:
        cmd.extend(["--extra-arg", arg])
    if build_path:
        cmd.extend(["-p", build_path])
    env = os.environ.copy()
    if sys.platform == "darwin" and "SDKROOT" not in env:
        sdk = macos_sdk_path()
        if sdk:
            env["SDKROOT"] = sdk
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False, env=env)
        return proc.stdout
    except FileNotFoundError:
        print(f"ERROR: clang-tidy binary not found at '{clang_tidy}'.", file=sys.stderr)
        sys.exit(2)


def count_shadow_diagnostics(output: str) -> int:
    # Match lines that mention "shadow" in a diagnostic message.
    # clang-tidy messages often look like: file:line:col: warning: 'x' shadows previous declaration [clang-diagnostic-shadow]
    pattern = re.compile(r"\bshadow\b", re.IGNORECASE)
    return sum(1 for _ in (ln for ln in output.splitlines() if pattern.search(ln)))


def main(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Check for clang-diagnostic-shadow across project")
    parser.add_argument("--clang-tidy", dest="clang_tidy", help="Path to clang-tidy binary")
    parser.add_argument("--compile-commands", dest="compile_commands", default="build/compile_commands.json")
    parser.add_argument("--extra-arg", action="append", default=[],
                        help="Additional compiler arguments appended to the compiler command")
    parser.add_argument("--extra-arg-before", action="append", default=[],
                        help="Additional compiler arguments prepended to the compiler command")
    parser.add_argument("--detail", action="store_true", help="Print full clang-tidy output for each file")
    args = parser.parse_args(argv)

    clang_tidy = args.clang_tidy or find_clang_tidy()
    cc_path = Path(args.compile_commands)
    if not cc_path.exists():
        print(f"ERROR: compile_commands.json not found at {cc_path}. Run CMake with -DCMAKE_EXPORT_COMPILE_COMMANDS=ON", file=sys.stderr)
        return 2

    # Attempt to derive build directory from compile_commands path
    build_dir = str(cc_path.parent)

    files = list(read_compile_commands(cc_path))
    if not files:
        print("No source files found in compile_commands.json", file=sys.stderr)
        return 0

    total = 0
    details = []
    extra_args: list[str] = args.extra_arg
    extra_args_before: list[str] = args.extra_arg_before
    for f in files:
        out = run_clang_tidy_on_file(clang_tidy, f, build_dir, extra_args, extra_args_before)
        n = count_shadow_diagnostics(out)
        if n:
            details.append((f, n, out.strip()))
            total += n

    if total == 0:
        print("No shadow diagnostics found.")
        return 0

    print(f"Found {total} shadow diagnostics in {len(details)} files:\n")
    for f, n, out in details:
        print(f"--- {f}: {n} occurrences ---")
        if args.detail:
            print(out)
        else:
            for ln in out.splitlines():
                if 'shadow' in ln.lower():
                    print(ln)
        print()

    return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
