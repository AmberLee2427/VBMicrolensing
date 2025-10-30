from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import site
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "VBMicrolensing" / "data"
EXTENSION_NAME = "VBMicrolensing.VBMicrolensing"


def _site_package_dirs() -> list[Path]:
    dirs: list[Path] = []
    getters = []
    getsitepackages = getattr(site, "getsitepackages", None)
    if getsitepackages is not None:
        getters.append(getsitepackages)
    getters.append(lambda: [site.getusersitepackages()])
    for getter in getters:
        try:
            entries = getter()
        except Exception:
            continue
        if isinstance(entries, (str, Path)):
            entries = [entries]
        dirs.extend(Path(entry) for entry in entries)
    return dirs


def _find_extension_candidates() -> list[Path]:
    candidates: list[Path] = []
    for base in _site_package_dirs():
        pkg_dir = base / "VBMicrolensing"
        if pkg_dir.is_dir():
            candidates.extend(pkg_dir.glob("VBMicrolensing*.so"))
    build_dir = ROOT / "build"
    if build_dir.exists():
        candidates.extend(build_dir.glob("**/VBMicrolensing*.so"))
    seen: set[Path] = set()
    unique: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return sorted(unique)


def _load_extension(path: Path):
    loader = importlib.machinery.ExtensionFileLoader(EXTENSION_NAME, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError(f"Unable to create spec for {path}")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def ensure_extension() -> None:
    if EXTENSION_NAME in sys.modules:
        return
    candidates = _find_extension_candidates()
    if not candidates:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "."], cwd=ROOT)
        candidates = _find_extension_candidates()
    if not candidates:
        raise RuntimeError("VBMicrolensing extension library not found")
    module = _load_extension(candidates[0])
    sys.modules[EXTENSION_NAME] = module


ensure_extension()


@pytest.fixture(scope="session", autouse=True)
def configure_tables():
    import VBMicrolensing

    data_files = [
        DATA_DIR / "ESPL.tbl",
        DATA_DIR / "SunEphemeris.txt",
        DATA_DIR / "satellite1.txt",
        DATA_DIR / "satellite2.txt",
    ]
    missing = [str(path) for path in data_files if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Required VBMicrolensing data files missing: {missing}")
    VBMicrolensing.VBMicrolensing.SetESPLtablefile(str(data_files[0]).encode())
    VBMicrolensing.VBMicrolensing.SetSuntablefile(str(data_files[1]).encode())


@contextlib.contextmanager
def _timeout(seconds: float):
    if seconds <= 0:
        yield
        return
    if hasattr(signal_module := __import__("signal"), "SIGALRM"):
        signal = signal_module

        def handler(signum, frame):
            raise TimeoutError(f"Test exceeded {seconds}s timeout")

        previous = signal.signal(signal.SIGALRM, handler)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
    else:
        start = time.monotonic()
        try:
            yield
        finally:
            elapsed = time.monotonic() - start
            if elapsed > seconds * 1.5:
                raise TimeoutError(f"Test exceeded {seconds}s timeout (fallback)")


@pytest.fixture(autouse=True)
def enforce_timeout():
    with _timeout(20):
        yield
