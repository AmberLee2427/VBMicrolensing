# TripleAstroLightCurve Test Plan

## Shadowed Variables

- [ ] `/Users/malpas.1/Code/VBMicrolensing/VBMicrolensing/lib/VBMicrolensingLibrary.cpp:5444` – declaration shadows a field of 'VBMicrolensing' [-Wshadow]
```
double rho = exp(pr[4]), tn, tE_inv = exp(-pr[5]), di, mindi, u, u0 = pr[2], t0 = pr[6], pai1 = pr[10], pai2 = pr[11];
```
- [ ] `/Users/malpas.1/Code/VBMicrolensing/VBMicrolensing/lib/VBMicrolensingLibrary.cpp:5445` – declaration shadows a field of 'VBMicrolensing' [-Wshadow] 
```
double q[3] = { 1, exp(pr[1]),exp(pr[8]) };
```
- [ ] `/Users/malpas.1/Code/VBMicrolensing/VBMicrolensing/lib/VBMicrolensingLibrary.cpp:5448` – declaration shadows a field of 'VBMicrolensing' [-Wshadow] 
```
complex s[3];
```
- [ ] `/Users/malpas.1/Code/VBMicrolensing/VBMicrolensing/lib/VBMicrolensingLibrary.cpp:5450` – declaration shadows a field of 'VBMicrolensing' [-Wshadow] 
```
double Et[2];
```

## Function

```cpp
void VBMicrolensing::TripleAstroLightCurve(double* pr, double* ts, double* mags, double* c1s, double* c2s, double* c1l, double* c2l, double* y1s, double* y2s, int np) {
	double rho = exp(pr[4]), tn, tE_inv = exp(-pr[5]), di, mindi, u, u0 = pr[2], t0 = pr[6], pai1 = pr[10], pai2 = pr[11];
	double q[3] = { 1, exp(pr[1]),exp(pr[8]) };
	double FR[3]; 
	double FRtot;
	complex s[3];
	double salpha = sin(pr[3]), calpha = cos(pr[3]), sbeta = sin(pr[9]), cbeta = cos(pr[9]);
	double Et[2];
	iastro = 12;
	dPosAng = 0;
	parallaxextrapolation = 0;

	s[0] = exp(pr[0]) / (q[0] + q[1]);
	s[1] = s[0] * q[0];
	s[0] = -q[1] * s[0];
	s[2] = exp(pr[7]) * complex(cbeta, sbeta) + s[0];
	//	_sols *Images; double Mag; // For debugging
	if (astrometry) {
		FR[0] = 1;
		FR[1] = (turn_off_secondary_lens) ? 0 : exp(pr[1] * mass_luminosity_exponent);
		FR[2] = exp(pr[8] * mass_luminosity_exponent);
		FRtot = FR[0] + FR[1] + FR[2];
	}

	SetLensGeometry(3, q, s);

	for (int i = 0; i < np; i++) {
		ComputeParallax(ts[i], t0);
		tn = (ts[i] + lighttravel - t0) * tE_inv + pai1 * Et[0] + pai2 * Et[1];
		u = u0 + pai1 * Et[1] - pai2 * Et[0];
		y1s[i] = u * salpha - tn * calpha;
		y2s[i] = -u * calpha - tn * salpha;
		//mindi = 1.e100;
		//for (int j = 0; j < n; j++) {
		//	di = fabs(y1s[i] - s[j].re) + fabs(y2s[i] - s[j].im);
		//	di /= sqrt(q[j]);
		//	if (di < mindi) mindi = di;
		//}
		//if (mindi >= 10.) {

		//	mags[i] = 1.;
		//}
		//else {
			mags[i] = MultiMag2(y1s[i], y2s[i], rho);
		//}
		if (astrometry) {
			c1s[i] = astrox1;
			c2s[i] = astrox2;
			ComputeCentroids(pr, ts[i], &c1s[i], &c2s[i], &c1l[i], &c2l[i]);
			c1l[i] += (s[0].re * FR[0] + s[1].re * FR[1] + s[2].re * FR[2])*cos(PosAng)/FRtot; // Flux center of the three lenses from origin
			c2l[i] += (s[0].im * FR[0] + s[1].im * FR[1] + s[2].im * FR[2]) * sin(PosAng) / FRtot;
		}

	}
}

#pragma endregion

#pragma region lightcurves
```

## Python Binding

```cpp
    vbm.def("TripleAstroLightCurve",
        [](VBMicrolensing& self, std::vector<double> params, std::vector<double> times)
        {
            if (!self.AreCoordinatesSet()) {
                py::print("Use SetObjectCoordinates before any parallax calculation!");
                std::vector< std::vector<double> > results{  };
                return results;
            }
            if (self.satellite > self.nsat) {
                py::print("! Ephemerides table not available for this satellite!");
                std::vector< std::vector<double> > results{  };
                return results;
            }
            std::vector<double> mags(times.size());
            std::vector<double> c1s(times.size());
            std::vector<double> c2s(times.size());
            std::vector<double> c1l(times.size());
            std::vector<double> c2l(times.size());
            std::vector<double> y1s(times.size());
            std::vector<double> y2s(times.size());
            self.astrometry = true;
            self.parallaxsystem = 1;
            self.TripleAstroLightCurve(params.data(), times.data(), mags.data(), c1s.data(), c2s.data(), c1l.data(), c2l.data(),
                y1s.data(), y2s.data(), times.size());
            std::vector< std::vector<double> > results{ mags, c1s, c2s, c1l, c2l,y1s,y2s };
            if (self.parallaxextrapolation > 0) py::print("Input time is outside range of lookup tables: extrapolation is used.");
            return results;
        },
        R"mydelimiter(
            Triple light curve and astrometry for a full array of observations.

            Parameters
            ----------
            params : list[float]
                List of parameters [log_s, log_q, u0, alpha, log_rho, log_tE, t0, 
                                    log(s13), log(q3), psi
                                    paiN, paiE,     #components of the parallax vector
                                    muS_N, muS_E,   # proper motion components of the source (mas/yr)
                                    pai_S,          # parallax of the source (mas)
                                    thetaE          # Einstein angle (mas) 
                                    ] 
            times : list[float] 
                Array of times at which the magnification is calculated.
 
            Returns
            -------
            results: list[list[float],list[float],list[float],list[float],list[float],list[float],list[float]] 
                [Magnification array,
                    centroid of images N array, centroid of images E array, 
                    centroid of lens N array, centroid of lens E array,
                    source position y1 array, source position y2 array]
            )mydelimiter");
    // Other functions
```

## Usage Example

Figuring out what needs to be set before running this function.

```python
