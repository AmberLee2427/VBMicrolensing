from __future__ import annotations

import math
import site
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import VBMicrolensing

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "VBMicrolensing" / "data"
EXTENSION_SUFFIXES = (".so", ".pyd", ".dylib", ".dll")


def _discover_extension_candidates() -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()
    for base in site.getsitepackages():
        pkg_dir = Path(base) / "VBMicrolensing"
        if pkg_dir.is_dir():
            for candidate in pkg_dir.glob("VBMicrolensing*"):
                if candidate.is_file() and candidate.suffix in EXTENSION_SUFFIXES:
                    real = candidate.resolve()
                    if real not in seen:
                        seen.add(real)
                        candidates.append(real)
    build_dir = ROOT / "build"
    if build_dir.exists():
        for candidate in build_dir.glob("**/VBMicrolensing*"):
            if candidate.is_file() and candidate.suffix in EXTENSION_SUFFIXES:
                real = candidate.resolve()
                if real not in seen:
                    seen.add(real)
                    candidates.append(real)
    return sorted(candidates)


EXTENSION_CANDIDATES = _discover_extension_candidates()
SITE_EXTENSION = next(
    (path for path in EXTENSION_CANDIDATES if "site-packages" in str(path)), None
)
LOCAL_EXTENSION = next(
    (
        path
        for path in EXTENSION_CANDIDATES
        if (ROOT / "build") in path.parents
    ),
    None,
)


@pytest.fixture
def vbm():
    return VBMicrolensing.VBMicrolensing()


def _run_subprocess_expectations(snippet: str) -> subprocess.CompletedProcess[str]:
    code = textwrap.dedent(
        f"""
        import math
        from pathlib import Path

        import VBMicrolensing

        DATA_DIR = Path({DATA_DIR!r})

        vbm = VBMicrolensing.VBMicrolensing()
        vbm.LoadESPLTable(str(DATA_DIR / "ESPL.tbl"))
        vbm.LoadSunTable(str(DATA_DIR / "SunEphemeris.txt"))
        vbm.SetObjectCoordinates(b"17:59:04 +14:00:03")

        {snippet}
        """
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
    )


@pytest.mark.xfail(strict=True, reason="BinaryLightCurveKepler currently returns static magnifications and NaNs.")
def test_binary_light_curve_kepler_has_orbital_signal(vbm):
    vbm.LoadESPLTable(str(DATA_DIR / "ESPL.tbl"))
    vbm.LoadSunTable(str(DATA_DIR / "SunEphemeris.txt"))
    vbm.SetObjectCoordinates(b"17:59:04 +14:00:03")

    params = [
        math.log10(0.9),
        math.log10(0.1),
        0.1,
        math.pi / 4,
        math.log10(0.03),
        math.log10(30.0),
        0.2,
    ]
    times = [0.0, 0.5, 1.0]
    result = vbm.BinaryLightCurveKepler(params + [0.01, -0.02, 0.0], times)

    mags, y1, y2, seps = result
    assert not all(abs(mag - 1.0) < 1e-6 for mag in mags)
    for series in (mags, y1, y2, seps):
        assert all(math.isfinite(value) for value in series)


@pytest.mark.xfail(strict=True, reason="CombineCentroids currently produces NaNs for BinaryAstroLightCurve results when using the wheel build.")
def test_combine_centroids_returns_finite_series(vbm):
    if SITE_EXTENSION is None:
        pytest.skip("No site-packages extension available to exercise CombineCentroids bug.")

    snippet = f"""
import importlib.machinery
import importlib.util
import sys
import math
from pathlib import Path

path = Path({SITE_EXTENSION!r})
loader = importlib.machinery.ExtensionFileLoader('VBMicrolensing.VBMicrolensing', str(path))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)
sys.modules['VBMicrolensing.VBMicrolensing'] = module
import VBMicrolensing

DATA_DIR = Path({DATA_DIR!r})
vbm = VBMicrolensing.VBMicrolensing()
vbm.LoadESPLTable(str(DATA_DIR / "ESPL.tbl"))
vbm.LoadSunTable(str(DATA_DIR / "SunEphemeris.txt"))
vbm.SetObjectCoordinates(b"17:59:04 +14:00:03")

params = [
    math.log10(0.9),
    math.log10(0.1),
    0.1,
    math.pi / 4,
    math.log10(0.03),
    math.log10(30.0),
    0.2,
]
times = [0.0, 0.5, 1.0]
astro = vbm.BinaryAstroLightCurve(params, times)
centroids = vbm.CombineCentroids(astro, 0.4)
for series in centroids:
    if not all(math.isfinite(value) for value in series):
        raise SystemExit(3)
    if not any(abs(value) > 1e-8 for value in series):
        raise SystemExit(4)
"""
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(snippet)],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.xfail(strict=True, reason="CombineCentroids collapses to zero offsets when using the locally built extension.")
def test_combine_centroids_returns_finite_series_local(vbm):
    if LOCAL_EXTENSION is None:
        pytest.skip("No local build artefact available to exercise CombineCentroids behaviour.")

    snippet = f"""
import importlib.machinery
import importlib.util
import sys
import math
from pathlib import Path

path = Path({LOCAL_EXTENSION!r})
loader = importlib.machinery.ExtensionFileLoader('VBMicrolensing.VBMicrolensing', str(path))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)
sys.modules['VBMicrolensing.VBMicrolensing'] = module
import VBMicrolensing

DATA_DIR = Path({DATA_DIR!r})
vbm = VBMicrolensing.VBMicrolensing()
vbm.LoadESPLTable(str(DATA_DIR / "ESPL.tbl"))
vbm.LoadSunTable(str(DATA_DIR / "SunEphemeris.txt"))
vbm.SetObjectCoordinates(b"17:59:04 +14:00:03")

params = [
    math.log10(0.9),
    math.log10(0.1),
    0.1,
    math.pi / 4,
    math.log10(0.03),
    math.log10(30.0),
    0.2,
]
times = [0.0, 0.5, 1.0]
astro = vbm.BinaryAstroLightCurve(params, times)
centroids = vbm.CombineCentroids(astro, 0.4)
for series in centroids:
    if not all(math.isfinite(value) for value in series):
        raise SystemExit(5)
    if not any(abs(value) > 1e-8 for value in series):
        raise SystemExit(6)
"""
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(snippet)],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.xfail(strict=True, reason="BinaryMagMultiDark currently aborts the interpreter.")
def test_binary_mag_multi_dark_populates_outputs():
    snippet = """
mag_list = [0.0, 0.0, 0.0]
vbm.BinaryMagMultiDark(0.9, 0.1, 0.1, -0.2, 0.03, [0.1, 0.2, 0.3], 3, mag_list, 1e-4)
if not all(isinstance(value, float) and math.isfinite(value) for value in mag_list):
    raise SystemExit(2)
"""
    result = _run_subprocess_expectations(snippet)
    assert result.returncode == 0, result.stderr


@pytest.mark.xfail(strict=True, reason="Switching method to Multipoly or Nopoly still segfaults before returning from MultiMag2.")
def test_set_method_multi_mag2_stability():
    snippet = """
vbm.SetLensGeometry([0.0, 0.0, 1.0, 0.5, 0.1, 0.7, -0.3, 0.2, 0.2])
method = VBMicrolensing.VBMicrolensing.Method
vbm.SetMethod(method.Multipoly)
value = vbm.MultiMag2(-0.1, 0.2, 0.05)
vbm.SetMethod(method.Singlepoly)
if not math.isfinite(value):
    raise SystemExit(3)
"""
    result = _run_subprocess_expectations(snippet)
    assert result.returncode == 0, result.stderr
