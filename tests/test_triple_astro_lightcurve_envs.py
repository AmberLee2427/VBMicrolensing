import contextlib
import importlib
import os
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_PARENT = REPO_ROOT.parent

# Greg's test scripts for triple lens light curves
TRIPLE_ASTRO_SCRIPT = textwrap.dedent(
    """
    import math
    import VBMicrolensing

    VBM = VBMicrolensing.VBMicrolensing()
    VBM.RelTol = 1e-3
    VBM.Tol = 1e-3
    VBM.astrometry = True
    VBM.SetObjectCoordinates("17:51:40.2082 -29:53:26.502")

    params = [
        math.log(0.9),
        math.log(0.028997),
        0.1,
        0.261799,
        math.log(0.01),
        math.log(20),
        0.0,
        math.log(1.5),
        math.log(0.003270),
        0.785398,
        0.1,
        0.1,
        -3.0,
        -2.0,
        0.12,
        5.15,
    ]

    times = [-5.0, 0.0, 5.0]

    result = VBM.TripleAstroLightCurve(params, times)
    print("RESULT_ARRAY_LENGTHS", [len(arr) for arr in result])
    """
).strip()


TRIPLE_LIGHT_SCRIPT = textwrap.dedent(
    """
    import math
    import VBMicrolensing

    VBM = VBMicrolensing.VBMicrolensing()
    params = [
        math.log(0.9),
        math.log(0.028997),
        0.1,
        0.261799,
        math.log(0.01),
        math.log(20),
        0.0,
        math.log(1.5),
        math.log(0.003270),
        0.785398,
    ]

    result = VBM.TripleLightCurve(params, [0.0])
    print("RESULT_LIGHT", result[0])
    """
).strip()


def _run_script(script: str, env: dict, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd),
    )


def _installed_package_env() -> dict:
    """Return environment pointing only to the installed wheel."""
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    if existing:
        filtered = [
            p for p in existing.split(os.pathsep) if not p or Path(p).resolve() != REPO_ROOT
        ]
        env["PYTHONPATH"] = os.pathsep.join(filtered)
    else:
        env.pop("PYTHONPATH", None)
    return env


@contextlib.contextmanager
def _extension_available_in_repo():
    """Temporarily ensure the compiled extension exists inside the repository tree."""
    candidate_paths = []
    import site

    for base in site.getsitepackages():
        candidate = Path(base) / "VBMicrolensing" / "VBMicrolensing.so"
        candidate_paths.append(candidate)
    user_candidate = Path(site.getusersitepackages()) / "VBMicrolensing" / "VBMicrolensing.so"
    candidate_paths.append(user_candidate)

    so_path = None
    for candidate in candidate_paths:
        if candidate.exists():
            so_path = candidate
            break

    if so_path is None:
        # Fallback: import whatever is available (likely the repo build)
        core_module = importlib.import_module("VBMicrolensing.VBMicrolensing")
        so_path = Path(core_module.__file__)

    target_dir = REPO_ROOT / "VBMicrolensing"
    target_dir.mkdir(exist_ok=True)
    target_path = target_dir / so_path.name
    exists_before = target_path.exists()
    backup_bytes = target_path.read_bytes() if exists_before else None

    if target_path.resolve() != so_path.resolve():
        shutil.copy2(so_path, target_path)
    try:
        yield
    finally:
        if exists_before and backup_bytes is not None:
            target_path.write_bytes(backup_bytes)
        elif not exists_before and target_path.exists():
            with contextlib.suppress(FileNotFoundError):
                target_path.unlink()


def _repo_checkout_env() -> dict:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(REPO_ROOT) if not existing else os.pathsep.join([str(REPO_ROOT), existing])
    return env


@dataclass
class Scenario:
    name: str
    script: str
    env_builder: callable
    cwd: Path
    prep: callable = field(default=contextlib.nullcontext)


LOCAL_BUILD_SO = REPO_ROOT / "VBMicrolensing" / "VBMicrolensing.so"


SCENARIOS = [
    pytest.param(
        Scenario(
            name="wheel-triple-lightcurve",
            script=TRIPLE_LIGHT_SCRIPT,
            env_builder=_installed_package_env,
            cwd=PROJECT_PARENT,
        ),
        id="wheel-triple-lightcurve",
    ),
    pytest.param(
        Scenario(
            name="wheel-triple-astro",
            script=TRIPLE_ASTRO_SCRIPT,
            env_builder=_installed_package_env,
            cwd=PROJECT_PARENT,
        ),
        id="wheel-triple-astro",
    ),
    pytest.param(
        Scenario(
            name="repo-triple-astro-localbuild",
            script=TRIPLE_ASTRO_SCRIPT,
            env_builder=_repo_checkout_env,
            cwd=REPO_ROOT,
            prep=contextlib.nullcontext,
        ),
        id="repo-triple-astro-localbuild",
        marks=pytest.mark.skipif(
            not LOCAL_BUILD_SO.exists(),
            reason="Local CMake build (VBMicrolensing/VBMicrolensing.so) not present.",
        ),
    ),
    pytest.param(
        Scenario(
            name="repo-triple-astro",
            script=TRIPLE_ASTRO_SCRIPT,
            env_builder=_repo_checkout_env,
            cwd=REPO_ROOT,
            prep=_extension_available_in_repo,
        ),
        id="repo-triple-astro",
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_triple_lightcurve_contexts(scenario: Scenario):
    """Exercise triple lens scripts under different import contexts."""
    env = scenario.env_builder()
    with scenario.prep():
        result = _run_script(scenario.script, env=env, cwd=scenario.cwd)

    # Basic diagnostics: ensure every context sees the same VBMicrolensing version
    version_check = subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib.metadata as m; print(m.version('VBMicrolensing'))",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(scenario.cwd),
    )
    assert version_check.returncode == 0, (
        f"{scenario.name} failed to import VBMicrolensing for version check:\n"
        f"stdout:\n{version_check.stdout}\n"
        f"stderr:\n{version_check.stderr}"
    )
    version = version_check.stdout.strip()
    assert version == "5.3.3", f"{scenario.name} imported VBMicrolensing {version}, expected 5.3.3"

    assert result.returncode == 0, (
        f"{scenario.name} returned exit code {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
