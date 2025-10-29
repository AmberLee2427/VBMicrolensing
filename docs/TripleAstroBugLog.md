# Testing log

The following code blocks were a continuous stream from my terminal, but I have added subtitles for clarity and easier navigation.

## Ensured `VBMicrolensingLibrary.cpp` matches the `main` branch

```
(base) ➜  VBMicrolensing git:(fix-astro-data-packaging) ✗ git checkout main -- VBMicrolensing/lib/VBMicrolensingLibrary.cpp
```

## Built a wheel

```
(base) ➜  VBMicrolensing git:(fix-astro-data-packaging) pip install .

Processing /Users/malpas.1/Code/VBMicrolensing
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Installing backend dependencies ... done
  Preparing metadata (pyproject.toml) ... done
Requirement already satisfied: numpy in /opt/anaconda3/lib/python3.12/site-packages (from VBMicrolensing==5.3.3) (1.26.4)
Requirement already satisfied: pytest in /opt/anaconda3/lib/python3.12/site-packages (from VBMicrolensing==5.3.3) (8.4.1)
Requirement already satisfied: iniconfig>=1 in /opt/anaconda3/lib/python3.12/site-packages (from pytest->VBMicrolensing==5.3.3) (1.1.1)
Requirement already satisfied: packaging>=20 in /opt/anaconda3/lib/python3.12/site-packages (from pytest->VBMicrolensing==5.3.3) (25.0)
Requirement already satisfied: pluggy<2,>=1.5 in /opt/anaconda3/lib/python3.12/site-packages (from pytest->VBMicrolensing==5.3.3) (1.6.0)
Requirement already satisfied: pygments>=2.7.2 in /opt/anaconda3/lib/python3.12/site-packages (from pytest->VBMicrolensing==5.3.3) (2.19.2)
Building wheels for collected packages: VBMicrolensing
  Building wheel for VBMicrolensing (pyproject.toml) ... done
  Created wheel for VBMicrolensing: filename=vbmicrolensing-5.3.3-cp312-cp312-macosx_15_0_arm64.whl size=1354351 sha256=7fef9fc87447812d9b4d6b64d57030b285cce3f2dd06148843618274c5ff530b
  Stored in directory: /private/var/folders/yk/2lp5vmnd6s778_4bh__0mvyc0000gp/T/pip-ephem-wheel-cache-4tlnnexo/wheels/05/68/e2/a51c932b135346f26b9aa96be56db6fab8557460a296fd5d78
Successfully built VBMicrolensing
Installing collected packages: VBMicrolensing
  Attempting uninstall: VBMicrolensing
    Found existing installation: VBMicrolensing 5.3.3
    Uninstalling VBMicrolensing-5.3.3:
      Successfully uninstalled VBMicrolensing-5.3.3
Successfully installed VBMicrolensing-5.3.3

[notice] A new release of pip is available: 25.2 -> 25.3
[notice] To update, run: pip install --upgrade pip
```

## Ran the test, expecting 2 failures

```
(base) ➜  VBMicrolensing git:(fix-astro-data-packaging) PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_triple_astro_lightcurve_envs.py

====================================== test session starts =======================================
platform darwin -- Python 3.12.2, pytest-8.4.1, pluggy-1.6.0
rootdir: /Users/malpas.1/Code/VBMicrolensing
configfile: pyproject.toml
collected 4 items                                                                                

tests/test_triple_astro_lightcurve_envs.py .F.F                                            [100%]

============================================ FAILURES ============================================
______________________ test_triple_lightcurve_contexts[wheel-triple-astro] _______________________

scenario = Scenario(name='wheel-triple-astro', script='import math\nimport VBMicrolensing\n\nVBM = VBMicrolensing.VBMicrolensing(...n _installed_package_env at 0x1045fc4a0>, cwd=PosixPath('/Users/malpas.1/Code'), prep=<class 'contextlib.nullcontext'>)

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
    
>       assert result.returncode == 0, (
            f"{scenario.name} returned exit code {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
E       AssertionError: wheel-triple-astro returned exit code -11
E         stdout:
E         
E         stderr:
E         
E       assert -11 == 0
E        +  where -11 = CompletedProcess(args=['/opt/anaconda3/bin/python', '-c', 'import math\nimport VBMicrolensing\n\nVBM = VBMicrolensing....ve(params, times)\nprint("RESULT_ARRAY_LENGTHS", [len(arr) for arr in result])'], returncode=-11, stdout='', stderr='').returncode

tests/test_triple_astro_lightcurve_envs.py:238: AssertionError
_______________________ test_triple_lightcurve_contexts[repo-triple-astro] _______________________

scenario = Scenario(name='repo-triple-astro', script='import math\nimport VBMicrolensing\n\nVBM = VBMicrolensing.VBMicrolensing()...a0>, cwd=PosixPath('/Users/malpas.1/Code/VBMicrolensing'), prep=<function _extension_available_in_repo at 0x1045fc900>)

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
    
>       assert result.returncode == 0, (
            f"{scenario.name} returned exit code {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
E       AssertionError: repo-triple-astro returned exit code -11
E         stdout:
E         
E         stderr:
E         
E       assert -11 == 0
E        +  where -11 = CompletedProcess(args=['/opt/anaconda3/bin/python', '-c', 'import math\nimport VBMicrolensing\n\nVBM = VBMicrolensing....ve(params, times)\nprint("RESULT_ARRAY_LENGTHS", [len(arr) for arr in result])'], returncode=-11, stdout='', stderr='').returncode

tests/test_triple_astro_lightcurve_envs.py:238: AssertionError
==================================== short test summary info =====================================
FAILED tests/test_triple_astro_lightcurve_envs.py::test_triple_lightcurve_contexts[wheel-triple-astro] - AssertionError: wheel-triple-astro returned exit code -11
FAILED tests/test_triple_astro_lightcurve_envs.py::test_triple_lightcurve_contexts[repo-triple-astro] - AssertionError: repo-triple-astro returned exit code -11
================================== 2 failed, 2 passed in 0.96s ===================================
```

## Removed the offending line

```
(base) ➜  VBMicrolensing git:(fix-astro-data-packaging) sed -i '' '5450d' VBMicrolensing/lib/VBMicrolensingLibrary.cpp
```

## Rebuilt the wheel

```
(base) ➜  VBMicrolensing git:(fix-astro-data-packaging) ✗ pip install .

Processing /Users/malpas.1/Code/VBMicrolensing
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Installing backend dependencies ... done
  Preparing metadata (pyproject.toml) ... done
Requirement already satisfied: numpy in /opt/anaconda3/lib/python3.12/site-packages (from VBMicrolensing==5.3.3) (1.26.4)
Requirement already satisfied: pytest in /opt/anaconda3/lib/python3.12/site-packages (from VBMicrolensing==5.3.3) (8.4.1)
Requirement already satisfied: iniconfig>=1 in /opt/anaconda3/lib/python3.12/site-packages (from pytest->VBMicrolensing==5.3.3) (1.1.1)
Requirement already satisfied: packaging>=20 in /opt/anaconda3/lib/python3.12/site-packages (from pytest->VBMicrolensing==5.3.3) (25.0)
Requirement already satisfied: pluggy<2,>=1.5 in /opt/anaconda3/lib/python3.12/site-packages (from pytest->VBMicrolensing==5.3.3) (1.6.0)
Requirement already satisfied: pygments>=2.7.2 in /opt/anaconda3/lib/python3.12/site-packages (from pytest->VBMicrolensing==5.3.3) (2.19.2)
Building wheels for collected packages: VBMicrolensing
  Building wheel for VBMicrolensing (pyproject.toml) ... done
  Created wheel for VBMicrolensing: filename=vbmicrolensing-5.3.3-cp312-cp312-macosx_15_0_arm64.whl size=1354411 sha256=883bb27ff465110ceda1c13bb8d0af11db05e49c173b9ad119f683408d39dcb7
  Stored in directory: /private/var/folders/yk/2lp5vmnd6s778_4bh__0mvyc0000gp/T/pip-ephem-wheel-cache-y62uixuh/wheels/05/68/e2/a51c932b135346f26b9aa96be56db6fab8557460a296fd5d78
Successfully built VBMicrolensing
Installing collected packages: VBMicrolensing
  Attempting uninstall: VBMicrolensing
    Found existing installation: VBMicrolensing 5.3.3
    Uninstalling VBMicrolensing-5.3.3:
      Successfully uninstalled VBMicrolensing-5.3.3
Successfully installed VBMicrolensing-5.3.3

[notice] A new release of pip is available: 25.2 -> 25.3
[notice] To update, run: pip install --upgrade pip
```

## Reran the tests expecting success

```
(base) ➜  VBMicrolensing git:(fix-astro-data-packaging) ✗ PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_triple_astro_lightcurve_envs.py

====================================== test session starts =======================================
platform darwin -- Python 3.12.2, pytest-8.4.1, pluggy-1.6.0
rootdir: /Users/malpas.1/Code/VBMicrolensing
configfile: pyproject.toml
collected 4 items                                                                                

tests/test_triple_astro_lightcurve_envs.py ....                                            [100%]

======================================= 4 passed in 0.70s ========================================
(base) ➜  VBMicrolensing git:(fix-astro-data-packaging) ✗ 
```