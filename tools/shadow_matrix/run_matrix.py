#!/usr/bin/env python3
"""
Run a build+test matrix to detect behavioral differences (useful for demonstrating
issues caused by shadowed variables across compilers/flags).

Usage (example):
  python tools/shadow_matrix/run_matrix.py \
    --config tools/shadow_matrix/config.yml \
    --run-cmd "python -m pytest tests/test_shadow_case.py -q" \
    --baseline results/baseline.txt

This script will, for each matrix entry:
 - configure a separate CMake build directory (build/matrix/<name>)
 - attempt to build the project
 - run the provided run-cmd (must be a shell command string) and capture stdout/stderr
 - write results to results/<name>.txt and record exit code
 - if a baseline is provided, produce a unified diff

The script is intentionally conservative: it does not attempt to install wheels.
Instead the run-cmd should perform whatever runtime validation you need (e.g.
importing the package from the build tree, running the branch's test, or running
a standalone binary produced by CMake).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:
    yaml = None


@dataclass
class MatrixEntry:
    name: str
    cc: str
    cxx: str
    cflags: str | None = None
    cxxflags: str | None = None


def load_config(path: Path) -> list[MatrixEntry]:
    text = path.read_text()
    if yaml:
        data = yaml.safe_load(text)
        rows = []
        for entry in data.get("matrix", []):
            rows.append(MatrixEntry(
                name=entry["name"],
                cc=entry["cc"],
                cxx=entry["cxx"],
                cflags=entry.get("cflags"),
                cxxflags=entry.get("cxxflags"),
            ))
        return rows

    # Minimal fallback parser for the simple YAML structure we write in config.yml.
    rows: list[MatrixEntry] = []
    cur: dict[str, Any] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('- '):
            # start new map entry
            if cur:
                # finalize previous
                rows.append(MatrixEntry(
                    name=cur['name'], cc=cur['cc'], cxx=cur['cxx'],
                    cflags=cur.get('cflags'), cxxflags=cur.get('cxxflags')
                ))
            cur = {}
            # parse after '- '
            if ':' in line:
                k, v = line[2:].split(':', 1)
                cur[k.strip()] = v.strip()
            continue
        if ':' in line and cur is not None:
            k, v = line.split(':', 1)
            cur[k.strip()] = v.strip()
    if cur:
        rows.append(MatrixEntry(
            name=cur['name'], cc=cur['cc'], cxx=cur['cxx'],
            cflags=cur.get('cflags'), cxxflags=cur.get('cxxflags')
        ))
    return rows


def run(cmd: str, cwd: Path | None = None, env: dict | None = None) -> tuple[int, str]:
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd, env=env)
    return proc.returncode, proc.stdout


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Run matrix builds and tests")
    p.add_argument("--config", default="tools/shadow_matrix/config.yml")
    p.add_argument("--run-cmd", required=True, help="Command to run after successful build (shell string).")
    p.add_argument("--baseline", help="Optional baseline file to diff against results/<name>.txt")
    p.add_argument("--build-root", default="build/matrix")
    p.add_argument("--jobs", type=int, default=4)
    args = p.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    config = Path(args.config)
    if not config.exists():
        print(f"Config not found: {config}")
        return 2

    entries = load_config(config)
    results_dir = repo_root / "results"
    ensure_dir(results_dir)

    overall = []
    for e in entries:
        print(f"\n=== Matrix entry: {e.name} ===")
        build_dir = repo_root / args.build_root / e.name
        # Fresh build dir to avoid accidental caching between entries
        if build_dir.exists():
            print(f"Removing existing build dir: {build_dir}")
            shutil.rmtree(build_dir)
        ensure_dir(build_dir)

        cmake_cmd = (
            f"cmake -S {repo_root} -B {build_dir} "
            f"-DCMAKE_CXX_COMPILER={e.cxx} "
            f"-DCMAKE_BUILD_TYPE=Release"
        )
        if e.cxxflags:
            cmake_cmd += f" -DCMAKE_CXX_FLAGS='{e.cxxflags}'"

        print("Configuring with CMake...")
        rc, out = run(cmake_cmd)
        (results_dir / f"{e.name}_configure.txt").write_text(out)
        print(out)
        if rc != 0:
            print(f"Configure failed for {e.name}; see results/{e.name}_configure.txt")
            overall.append((e.name, "configure-failed", rc))
            continue

        build_cmd = f"cmake --build {build_dir} -- -j{args.jobs}"
        print("Building...")
        rc, out = run(build_cmd)
        (results_dir / f"{e.name}_build.txt").write_text(out)
        print(out[:1000])
        if rc != 0:
            print(f"Build failed for {e.name}; see results/{e.name}_build.txt")
            overall.append((e.name, "build-failed", rc))
            continue

        # Stage the freshly built extension next to the Python package so imports pick it up.
        so_candidates = list(build_dir.glob("**/VBMicrolensing*.so"))
        if so_candidates:
            target_dir = repo_root / "VBMicrolensing"
            target_dir.mkdir(exist_ok=True)
            destination = target_dir / "VBMicrolensing.so"
            shutil.copy2(so_candidates[0], destination)

        # Run the user-provided command. Provide environment where build dir is visible.
        env = os.environ.copy()
        # Add repo root to PYTHONPATH so Python can import the package source
        env_py = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(repo_root) + (":" + env_py if env_py else "")

        print("Running test command...")
        rc, out = run(args.run_cmd, env=env, cwd=repo_root)
        res_file = results_dir / f"{e.name}.txt"
        res_file.write_text(out)
        print(out[:1000])

        # Optionally diff to baseline
        if args.baseline:
            import difflib

            baseline_path = repo_root / args.baseline
            if baseline_path.exists():
                baseline = baseline_path.read_text().splitlines(keepends=True)
                actual = out.splitlines(keepends=True)
                diff = ''.join(difflib.unified_diff(baseline, actual, fromfile=str(baseline_path), tofile=str(res_file)))
                (results_dir / f"{e.name}_diff.txt").write_text(diff)
                if diff:
                    print(f"Differences found for {e.name}; see results/{e.name}_diff.txt")
                    overall.append((e.name, "diff", 1))
                else:
                    overall.append((e.name, "ok", 0))
            else:
                print(f"Baseline not found at {baseline_path}; skipping diff")
                overall.append((e.name, "ran", rc))
        else:
            overall.append((e.name, "ran", rc))

    print("\n=== Matrix summary ===")
    for name, status, code in overall:
        print(f"{name}: {status} (code {code})")

    # Exit non-zero if any entry recorded diff or failure
    for _, status, code in overall:
        if status in ("configure-failed", "build-failed", "diff") or code != 0:
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
