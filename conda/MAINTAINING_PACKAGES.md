# Release Maintenance (VBMicrolensing)

This is a project-specific maintainer guide for the VBM conda package.

It explains:
- what lives in this repo vs conda-forge
- the normal update path after a PyPI release
- what `.github/workflows/test_conda_recipe.yml` is for (and what it is not for)

## What Lives Where

- `conda/meta.yaml` in this repo:
  - a local recipe copy used for smoke testing and documentation
  - convenient place to iterate before editing the real feedstock
- `vbmicrolensing-feedstock` (under `conda-forge/`):
  - the real conda-forge recipe and CI
  - the only place that actually publishes packages to conda-forge

## High-Level Maintenance Flow

1. Release a new VBM version to PyPI (sdist + wheels).
2. Run or let CI run the `test_conda_recipe` workflow in this repo.
3. Wait for `regro-cf-autotick-bot` to open a version bump PR on the feedstock.
4. Review/fix the feedstock PR if needed, then merge it.
5. conda-forge CI builds and publishes the new conda package.

## PyPI release checklist (primary maintainer: `valboz/VBMicrolensing`)

Publishing is implemented in `.github/workflows/publish_pypi_release.yml`. It only uploads
when the workflow runs on the upstream repository (`github.repository == 'valboz/VBMicrolensing'`),
so pushes and tags on forks do not publish to PyPI.

**One-time setup (repo admin on `valboz/VBMicrolensing`)**

You need **admin** (or custom role with “Secrets” access) on the GitHub repository to add secrets.

### 1. Create API tokens on PyPI / TestPyPI

**PyPI (production)**

1. Sign in at [https://pypi.org](https://pypi.org).
2. Open **Account settings** → **API tokens** (or [https://pypi.org/manage/account/](https://pypi.org/manage/account/) → API tokens).
3. Choose **Add API token**.
4. Set **Token name** (for example `VBM-github-actions`).
5. Set **Scope** to the **entire account** or, preferably, **limit to project** and select the `VBMicrolensing` (or `vbmicrolensing`) package so the token cannot upload other projects.
6. Create the token, copy it **once** (PyPI will not show it again). It should look like `pypi-…`.

**TestPyPI (optional, for manual TestPyPI runs)**

1. Repeat the same steps on [https://test.pypi.org](https://test.pypi.org) (separate account state; register the package there first if you use project-scoped tokens).
2. Store that token for the GitHub secret below.

Official reference: [PyPI — API tokens](https://pypi.org/help/#apitoken).

### 2. Add repository secrets in GitHub

1. Open the repository: [https://github.com/valboz/VBMicrolensing](https://github.com/valboz/VBMicrolensing).
2. Go to **Settings** (repo tabs, not your global GitHub settings).
3. In the left sidebar: **Security: Secrets and variables** → **Actions**.
4. Open the **Secrets** tab (not *Variables*; they aren't secret).
5. Click **New repository secret**.
6. Add **`PYPI_API_TOKEN`**:
   - **Name** must be exactly `PYPI_API_TOKEN` (matches `.github/workflows/publish_pypi_release.yml`).
   - **Secret**: paste the PyPI token from step 1.
   - Save.
7. Optional: add **`TEST_PYPI_API_TOKEN`** the same way for TestPyPI workflow runs.

**Notes**

- Secret **names** are case-sensitive and must match the workflow.
- After saving, you cannot view the secret again in GitHub; you can only **update** or **delete** it.
- Forks do not inherit secrets; the publish workflow also checks `github.repository == 'valboz/VBMicrolensing'` so accidental publish from a fork does not occur.

Official reference: [GitHub Docs — Using secrets in GitHub Actions](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository).

**Release steps**

1. Bump `version` in `pyproject.toml` and add an entry in `changelog.md`.
2. Merge the version bump to `valboz/VBMicrolensing` `main`.
3. Create and push an annotated tag `v<version>` matching `pyproject.toml` (for example `v5.4.1`).
4. Confirm the automated *Publish PyPI And Release* workflow completes; wheels and sdist should appear on PyPI.
5. Proceed with the conda-forge bot PR flow below (no manual feedstock edit is needed for a simple version bump).

**TestPyPI without a tag**

- Use *Actions → Publish PyPI And Release → Run workflow*, choose `testpypi`, run on `main`.
- Artifacts still build for every run; only the publish job is gated by tag or manual choice.

## Overlapping conda-forge bot pull requests

When several bot PRs exist at once, treat them in this order:

1. **Infrastructure / migration PRs** (for example *Rebuild for python 3.14*) merge first once CI is green.
2. **Version bumps**: keep only the PR for the **newest** upstream version you intend to ship.
3. If a newer bump PR says it **Closes** an older bump (for example v5.4.1 closes v5.4), merge the newest PR and **close** the obsolete one if GitHub did not auto-close it.
4. If conda-forge-admin reports a **lint** error (for example `package.version` parsed as a float), fix by quoting the version in `recipe/meta.yaml` (for example `version: "5.4"`); newer bot PRs often include that fix.

For [`vbmicrolensing-feedstock`](https://github.com/conda-forge/vbmicrolensing-feedstock.git), typical resolution after PyPI has the latest release: merge the
current version-bump PR whose CI passes and whose `meta.yaml` matches PyPI (version + `sha256`).

## Role of `test_conda_recipe.yml`

`test_conda_recipe.yml` is a smoke-test workflow for this repository.

What it does:
- runs a matrix build on `ubuntu`, `macOS`, and `windows`
- tests Python `3.10` to `3.13`
- fetches source tarball metadata from PyPI for the target version
- patches `conda/meta.yaml` in CI only with the PyPI version and `sha256`
- runs `conda render` and `conda build`
- uploads built packages as CI artifacts

What it does not do:
- it does not update the feedstock
- it does not publish to conda-forge
- it does not replace the conda-forge bot PR/review flow

Why it exists:
- catches packaging breakage right after a PyPI release
- verifies the recipe still builds across OS/Python combinations
- avoids waiting on the conda-forge bot PR to discover obvious build issues

## Workflow Triggers and Guardrails

Current triggers for `.github/workflows/test_conda_recipe.yml`:
- `workflow_dispatch` (manual)
- GitHub `release.published`

Important guardrail:
- the workflow skips automatic `release.published` runs unless the repo variable
  `ENABLE_PYPI_PUBLISH=true` is set
- this avoids noisy failures when GitHub releases and PyPI publishing are not yet
  synchronized

Manual run behavior:
- `workflow_dispatch` always uses the version from `pyproject.toml` and fetches that release’s sdist metadata from PyPI
- `release.published` uses the release tag (`v*`) as the version; it fails if that version does not match `pyproject.toml` (guardrail so the smoke test stays aligned with the repo)

## After the Package Is on Conda-Forge

For normal version bumps, prefer the bot workflow:
- `regro-cf-autotick-bot` usually updates version and source hash
- review the PR and fix recipe changes if dependencies/build logic changed
- merge the PR once feedstock CI passes

If the bot PR does not appear:
- wait a few hours first (bot lag is common)
- check that the PyPI release exists and the sdist is available
- check for too many open bot PRs on the feedstock (the bot pauses after several)

## Feedstock PR Rules (Condensed)

- Use a fork of the feedstock, not a branch in `conda-forge/vbmicrolensing-feedstock`
- New upstream version:
  - set recipe `version` to the new version
  - update source `sha256`
  - reset `build.number` to `0`
- Metadata-only fix (same upstream version):
  - increment `build.number`

## Local Testing (Before Feedstock PR)

Quick local test of this repo recipe:

```bash
conda render conda --override-channels -c conda-forge
conda build conda --override-channels -c conda-forge --no-anaconda-upload
```

For staged-recipes or feedstock-style CI reproduction:
- use conda-forge's `build-locally.py` in the relevant repository
- do not commit local `.ci_support/*.yaml` path tweaks (for example local SDK paths)

## Common Failure Modes We Have Seen

- PyPI URL/SHA mismatch:
  - use the `pypi.io/packages/source/...` recipe URL pattern
- Linux/macOS CMake generator issue:
  - CMake may default to `make` in CI where `make` is unavailable
  - the recipe forces `CMAKE_GENERATOR=Ninja` on Unix
- Windows generator conflict:
  - do not force Ninja on Windows in conda-forge CI (Visual Studio generator is expected)
- `pip check` false failures:
  - avoid `pip check` if upstream metadata incorrectly lists non-runtime deps

## References

- Canonical conda-forge maintainer docs:
  - https://conda-forge.org/docs/maintainer/adding_pkgs/
- This file is intentionally shorter and VBM-specific.
