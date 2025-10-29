# Why `TripleAstroLightCurve` Segfaulted (and How To Fixed It)

Greg’s crash report looked scary, but the root cause turned out to be a one-line C++ scoping bug. This note explains what went wrong, why Valerio’s local build seemed fine, and how removing a stray declaration makes the wheel behave correctly.

---

## The bug: a shadowed member array

Inside `VBMicrolensing::TripleAstroLightCurve` VBM declared a local `double Et[2];`:

```cpp
double rho = exp(pr[4]), tn, tE_inv = exp(-pr[5]), di, mindi, u, u0 = pr[2], t0 = pr[6], pai1 = pr[10], pai2 = pr[11];
double q[3] = { 1, exp(pr[1]), exp(pr[8]) };
double FR[3];
double FRtot;
complex s[3];
double salpha = sin(pr[3]), calpha = cos(pr[3]), sbeta = sin(pr[9]), cbeta = cos(pr[9]);
double Et[2];  // ← problematic line
```

But the class already has a member `double Et[2];` defined in `VBMicrolensing`, and the parallax routine `ComputeParallax` writes directly into that member before each loop iteration. By introducing a second `Et` on the stack, we *hid* the true member (a phenomenon known as *shadowing*). Every read in the loop saw the uninitialised local array instead of the member that had just been populated.

Because the local array was full of garbage, we effectively fed NaNs into the first call to `MultiMag2`. That explains Greg’s crash from the wheel build: the astrometry code was operating on the wrong `Et`.

---

## Why Valerio’s local build “worked”

I assume, Valerio built the extension via CMake and copied the resulting `VBMicrolensing.so` into the checkout before running python code. That build path happened to resolve `Et` to the class member at runtime, so his script never saw the NaNs.

The wheel built by scikit-build-core/cibuildwheel, on the other hand, resolved `Et` to the local stack array, so `TripleAstroLightCurve` blew up immediately. Same sources, different import path, wildly different results. No data files were missing; it was strictly the shadowed variable.

---

## The fix

If you remove the local declaration so the function always uses `this->Et` (the member updated by `ComputeParallax`), regardless of how the module is loaded:

```diff
 double FR[3];
 double FRtot;
 complex s[3];
 double salpha = sin(pr[3]), calpha = cos(pr[3]), sbeta = sin(pr[9]), cbeta = cos(pr[9]);
-double Et[2];
```

That’s it—one line deleted.

After reinstalling the package (`pip install .`), `TripleAstroLightCurve` returns sane values in every scenario:

```
$ PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_triple_astro_lightcurve_envs.py
======================================= test session starts =======================================
platform darwin -- Python 3.12.2, pytest-8.4.1, pluggy-1.6.0
rootdir: /Users/malpas.1/Code/VBMicrolensing
configfile: pyproject.toml
collected 4 items                                                                                 

tests/test_triple_astro_lightcurve_envs.py ....                                             [100%]

======================================== 4 passed in 0.55s ========================================
```

| Scenario | Description | Result |
|----------|-------------|--------|
| `wheel-triple-lightcurve` | wheel import, non-astrometric | ✅ |
| `repo-triple-astro-localbuild` | CMake build + repo import | ✅ |
| `wheel-triple-astro` | wheel import, full astrometry | ✅ |
| `repo-triple-astro` | repo import, wheel module | ✅ |

No extra guards, no special packaging rules—just pointing to the correct `Et`.

---

## Takeaway

The segfault was never about missing aux data or precision flags. It was an accidentally shadowed array in the parallax corrections inside `TripleAstroLightCurve`. Removing that local array lets the function read the member `Et` that `ComputeParallax` already maintains, so the wheel and the CMake build now produce identical, correct results.

## TL;DR

Delete line 5450 in `VBMicrolensing.cpp` and local wheel builds should work like Valerio's set up; `pip install .` from inside a VBM clone.
