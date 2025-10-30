from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import pytest

import VBMicrolensing

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "VBMicrolensing" / "data"


@pytest.fixture
def vbm():
    return VBMicrolensing.VBMicrolensing()


def test_load_tables_and_basic_magnifications(vbm):
    vbm.LoadESPLTable(str(DATA_DIR / "ESPL.tbl"))
    vbm.LoadSunTable(str(DATA_DIR / "SunEphemeris.txt"))

    assert vbm.PSPLMag(0.1) == pytest.approx(10.037461005722339)
    assert vbm.ESPLMag(0.2, 0.05) == pytest.approx(5.115264209713242)
    assert vbm.ESPLMag2(0.2, 0.05) == pytest.approx(5.115264209713242)
    assert vbm.ESPLMagDark(0.2, 0.05) == pytest.approx(5.115264209713242)

    assert vbm.BinaryMag0(0.9, 0.1, 0.1, -0.2) == pytest.approx(3.637365075053435)
    assert vbm.BinaryMag(0.9, 0.1, 0.1, -0.2, 0.03, 1e-4) == pytest.approx(3.644289742581571)
    assert vbm.BinaryMag2(0.9, 0.1, 0.1, -0.2, 0.03) == pytest.approx(3.644294615355848)
    assert vbm.BinaryMagDark(0.9, 0.1, 0.1, -0.2, 0.03, 1e-4) == pytest.approx(3.644289742581571)


def test_binary_magnifications_and_contours(vbm):
    magnifications = (
        vbm.BinaryMag0(0.9, 0.1, 0.1, -0.2),
        vbm.BinaryMag(0.9, 0.1, 0.1, -0.2, 0.03, 1e-4),
        vbm.BinaryMag2(0.9, 0.1, 0.1, -0.2, 0.03),
    )
    assert magnifications[0] < magnifications[1] < magnifications[2]

    contours = vbm.ImageContours(0.9, 0.1, 0.1, -0.2, 0.03)
    assert len(contours) == 3
    for segment in contours:
        assert len(segment[0]) == len(segment[1])
    first_points = sorted(segment[0][0] for segment in contours)
    assert first_points == pytest.approx(
        [-0.6445137206816927, 0.5381842807995851, 0.6844713811420684]
    )


def test_set_lens_geometry_and_caustics(vbm):
    parameters = [0.0, 0.0, 1.0, 0.5, 0.1, 0.7, -0.3, 0.2, 0.2]
    vbm.SetLensGeometry(parameters)

    assert vbm.MultiMag0(-0.1, 0.2) == pytest.approx(3.335165808307957)
    assert vbm.MultiMag(-0.1, 0.2, 0.05) == pytest.approx(3.3634445751120223)
    assert vbm.MultiMagDark(-0.1, 0.2, 0.05, 0.2) == pytest.approx(3.349617659810512)
    baseline = vbm.MultiMag2(-0.1, 0.2, 0.05)
    assert baseline == pytest.approx(3.349617659810512)

    assert len(vbm.MultiImageContours(-0.1, 0.2, 0.05)) == 4
    assert len(vbm.Multicaustics()) == 5
    assert len(vbm.Multicriticalcurves()) == 5
    assert len(vbm.Caustics(0.9, 0.1)) == 1
    assert len(vbm.Criticalcurves(0.9, 0.1)) == 1

    assert vbm.MultiMag2(-0.1, 0.2, 0.05) == pytest.approx(baseline)


def test_object_coordinate_variants(vbm):
    vbm.SetObjectCoordinates(b"17:59:04 +14:00:03")

    coordinate_file = DATA_DIR / "OB151212coords.txt"
    vbm.SetObjectCoordinates(str(coordinate_file).encode(), str(DATA_DIR).encode())

    params_pspl_par = [0.1, math.log10(30.0), 0.2, 0.05, -0.02]
    times = [0.0, 0.5, 1.0]
    result = vbm.PSPLLightCurveParallax(params_pspl_par, times)
    assert len(result[0]) == len(times)


def test_light_curve_basics(vbm):
    params_pspl = [math.log10(0.3), math.log10(30.0), 0.1]
    params_espl = [math.log10(0.1), math.log10(30.0), 0.1, math.log10(0.01)]
    params_bin = [
        math.log10(0.9),
        math.log10(0.1),
        0.1,
        math.pi / 4,
        math.log10(0.03),
        math.log10(30.0),
        0.2,
    ]
    params_binsource = [math.log10(30.0), math.log10(0.5), 0.1, -0.1, 0.2, 0.25]
    times = [0.0, 0.5, 1.0]

    pspl = vbm.PSPLLightCurve(params_pspl, times)
    assert pspl[0] == pytest.approx([1.90040972312803, 1.8842044864657774, 1.820105176168462])
    assert pspl[1] == pytest.approx([0.02282939434472496, -0.09131757737889984, -0.20546454910252465])
    assert pspl[2] == pytest.approx([-0.5928115358342116] * 3)

    espl = vbm.ESPLLightCurve(params_espl, times)
    assert espl[0] == pytest.approx([2.8996514261896196, 2.824476368105552, 2.561989214893916])
    assert espl[1] == pytest.approx(pspl[1])
    assert espl[2] == pytest.approx([-0.36787944117144233] * 3)

    binary = vbm.BinaryLightCurve(params_bin, times)
    assert binary[0] == pytest.approx([6.116464407892789, 6.365845619361319, 5.573717957899462])
    assert binary[1] == pytest.approx([0.10299631722172843, 0.022282219464044233, -0.058431878293639966])
    assert binary[2] == pytest.approx([-0.038425039015581086, -0.11913913677326526, -0.19985323453094944])

    binary_w = vbm.BinaryLightCurveW(params_bin + [0.01], times)
    assert binary_w[0] == pytest.approx(binary[0])

    bin_source = vbm.BinSourceLightCurve(params_binsource, times)
    assert bin_source[0] == pytest.approx([8.963585196726799, 8.479720279749072, 4.981135857202303])
    assert bin_source[2] == pytest.approx([-0.1, -0.1, -0.1])

    bin_source_ext = vbm.BinSourceExtLightCurve(params_binsource + [math.log10(0.03)], times)
    assert bin_source_ext[0] == pytest.approx([8.798834144813227, 8.718537857936001, 6.586882872965887])


def test_parallax_and_orbital_light_curves(vbm):
    build_style = os.environ.get("VBM_BUILD_STYLE")
    if sys.platform == "darwin" and build_style == "cmake-local":
        pytest.xfail("BinaryLightCurveKepler stalls under macOS CMake builds.")
    vbm.LoadESPLTable(str(DATA_DIR / "ESPL.tbl"))
    vbm.LoadSunTable(str(DATA_DIR / "SunEphemeris.txt"))
    vbm.SetObjectCoordinates(b"17:59:04 +14:00:03")

    params_pspl_par = [0.1, math.log10(30.0), 0.2, 0.05, -0.02]
    params_espl = [math.log10(0.1), math.log10(30.0), 0.1, math.log10(0.01)]
    params_bin = [
        math.log10(0.9),
        math.log10(0.1),
        0.1,
        math.pi / 4,
        math.log10(0.03),
        math.log10(30.0),
        0.2,
    ]
    params_binsource = [math.log10(30.0), math.log10(0.5), 0.1, -0.1, 0.2, 0.25]
    times = [0.0, 0.5, 1.0]

    pspl_par = vbm.PSPLLightCurveParallax(params_pspl_par, times)
    assert pspl_par[0] == pytest.approx([9.1378997206166, 8.295808624915175, 4.880319807389971])
    assert pspl_par[1] == pytest.approx([0.0456585870715635, -0.0684878806073451, -0.18263434417457683])

    espl_par = vbm.ESPLLightCurveParallax(params_espl + [0.01, -0.01, 0.02], times)
    assert espl_par[0] == pytest.approx([1.3440926958609347, 1.3412876676316723, 1.3295711524893499])
    assert espl_par[2] == pytest.approx([1.0000001322809091, 0.9999994708763634, 0.9999988049808939])

    binary_par = vbm.BinaryLightCurveParallax(params_bin + [0.01, -0.02], times)
    assert binary_par[0] == pytest.approx([6.116472560681031, 6.365829810886778, 5.5737645301895835])

    binary_orb = vbm.BinaryLightCurveOrbital(params_bin + [0.01, -0.02, 0.0], times)
    expected_mags = [
        [6.116472560681275, 6.365829810886778, 5.5737645301895835],
        [6.188685172628886, 6.47012490217936, 5.84369728244906],
    ]
    expected_seps = [
        [0.955273596967172, 0.955273596967172, 0.955273596967172],
        [0.9505012079624582, 0.944546904197071, 0.8798652487672949],
    ]
    assert any(binary_orb[0] == pytest.approx(option) for option in expected_mags)
    assert any(binary_orb[3] == pytest.approx(option) for option in expected_seps)

    binary_kepler = vbm.BinaryLightCurveKepler(params_bin + [0.01, -0.02, 0.0], times)
    assert binary_kepler[0] == pytest.approx([1.0, 1.0, 1.0])
    assert all(math.isnan(value) for value in binary_kepler[1])
    assert all(math.isnan(value) for value in binary_kepler[2])
    assert all(math.isnan(value) for value in binary_kepler[3])

    bin_source_par = vbm.BinSourceLightCurveParallax(params_binsource + [0.01, -0.02], times)
    assert bin_source_par[0] == pytest.approx([8.963599757556635, 8.479736532572481, 4.981161017643781])


def test_bin_source_extensions(vbm):
    vbm.SetObjectCoordinates(b"17:59:04 +14:00:03")
    params_binsource = [math.log10(30.0), math.log10(0.5), 0.1, -0.1, 0.2, 0.25]
    times = [0.0, 0.5, 1.0]

    ext_xallarap = vbm.BinSourceExtLightCurveXallarap(
        params_binsource + [math.log10(0.03), 0.1, 0.2, 0.3, 0.4, 0.5], times
    )
    assert ext_xallarap[0] == pytest.approx([7.24902330898381, 8.69941143370305, 4.159256005813179])
    assert ext_xallarap[3] == pytest.approx(
        [0.12931776449322846, -0.13154188461151683, -0.3506346678166603]
    )


def test_triple_light_curves(vbm):
    vbm.SetObjectCoordinates(b"17:59:04 +14:00:03")
    params_triple = [
        math.log10(0.9),
        math.log10(0.1),
        math.log10(0.05),
        0.1,
        math.pi / 4,
        math.log10(0.02),
        math.log10(30.0),
        0.2,
        0.01,
    ]
    times = [0.0, 0.5, 1.0]

    triple = vbm.TripleLightCurve(params_triple, times)
    assert triple[0] == pytest.approx([1.0004196183002045, 1.0025599092526722, 1.0754847895102284])

    triple_par = vbm.TripleLightCurveParallax(params_triple + [0.01, -0.02], times)
    assert triple_par[0] == pytest.approx([1.0004197386959401, 1.002560394463894, 1.076233335896558])

    combined = vbm.LightCurve(
        [math.log10(0.9), math.log10(0.1), 0.1, math.pi / 4, math.log10(0.03), math.log10(30.0), 0.2],
        times,
    )
    assert combined[0] == pytest.approx([1.7557725756871105, 1.1356616087214126, 1.0224419542493528])


def test_astrometric_outputs_and_combine(vbm):
    vbm.LoadESPLTable(str(DATA_DIR / "ESPL.tbl"))
    vbm.LoadSunTable(str(DATA_DIR / "SunEphemeris.txt"))
    vbm.SetObjectCoordinates(b"17:59:04 +14:00:03")
    params_bin = [
        math.log10(0.9),
        math.log10(0.1),
        0.1,
        math.pi / 4,
        math.log10(0.03),
        math.log10(30.0),
        0.2,
    ]
    times = [0.0, 0.5, 1.0]

    astro_binary = vbm.BinaryAstroLightCurve(params_bin, times)
    assert len(astro_binary[0]) == len(times)
    for series in astro_binary:
        assert len(series) == len(times)
        assert all(math.isfinite(value) or math.isnan(value) for value in series)

    centroids = vbm.CombineCentroids(astro_binary, 0.4)
    for series in centroids:
        assert len(series) == len(times)
        assert all(math.isfinite(value) or math.isnan(value) for value in series)


def test_flag_toggles(vbm):
    assert not vbm.turn_off_secondary_source
    assert vbm.t_in_HJD

    vbm.turn_off_secondary_source = True
    vbm.t_in_HJD = False
    assert vbm.turn_off_secondary_source
    assert not vbm.t_in_HJD
