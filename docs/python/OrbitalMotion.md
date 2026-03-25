[Back to **Parallax**](Parallax.md)

# Orbital motion

Binary and triple lenses orbit around the common center of mass. If the microlensing event is long enough, we should take orbital motion into account. However, to first order, microlensing is only sensitive to changes in the projected separation and orientation of the binary lenses, while most orbital parameters remain unconstrained. Rather than adding too many dimensions to our parameter space, in order to describe the subtle deviations in our microlensing event, it might be sufficient to restrict to circular orbits. Let us start by binary lenses and then extend to triple lenses

## Orbital motion in binary lenses

For binary lenses, VBMicrolensing offers two functions:

```
BinaryLightCurveOrbital
BinaryLightCurveKepler
```

The first function describes circular orbital motion, while the second considers elliptic Keplerian orbital motion. Note that we deprecate the "linear approximation", which is popular in many microlensing papers, since it does not correspond to any physical trajectories and may lead to unphysical solutions.

Both functions discussed here include the parallax calculation. Therefore, a preliminary call to `VBM.SetObjectCoordinates` is mandatory (see [Parallax](Parallax.md)). If you want to fit orbital motion without parallax, you may set the two components of the parallax to zero.

Finally, the reference time for orbital motion calculation is always $t_{0,orb}=t_0$, i.e. the time of closest approach of the source to the center of mass. Notice that if you specify a different reference time for parallax $t_{0,par}$ (see [Parallax](Parallax.md#reference-time-for-parallax-t_0par)), this has no effect on $t_{0,orb}$.

## Circular orbital motion

Here is an example of use of `BinaryLightCurveOrbital`:

```
import VBMicrolensing
import math
import numpy as np
import matplotlib.pyplot as plt

VBM = VBMicrolensing.VBMicrolensing()

s = 0.9       # Separation between the lenses
q = 0.1       # Mass ratio
u0 = 0.0       # Impact parameter with respect to center of mass
alpha = 1.0       # Angle of the source trajectory
rho = 0.01       # Source radius
tE = 30.0      # Einstein time in days
t0 = 7500      # Time of closest approach to center of mass
paiN = 0.3     # North component of the parallax vector
paiE = -0.2     # East component of the parallax vector
gamma1 = 0.011   # Orbital motion component ds/dt/s
gamma2 = -0.005   # Orbital motion component dalpha/dt
gamma3 = 0.005   # Orbital motion component dsz/dt/s

# Array of parameters. Note that s, q, rho and tE are in log-scale
pr = [math.log(s), math.log(q), u0, alpha, math.log(rho), math.log(tE), t0, paiN, paiE, gamma1, gamma2, gamma3]

t = np.linspace(t0-tE, t0+tE, 300) # Array of times

VBM.SetObjectCoordinates("17:59:02.3 -29:04:15.2") # Assign RA and Dec to our microlensing event

magnifications, y1, y2 = VBM.BinaryLightCurve(pr,t)      # Calculation of static binary-lens light curve
magnificationspar, y1par, y2par = VBM.BinaryLightCurveParallax(pr,t)      # Calculation of light curve with parallax
magnificationsorb, y1orb, y2orb, sorb = VBM.BinaryLightCurveOrbital(pr,t)      # Calculation of light curve with orbital motion

plt.plot(t,magnifications,"g")
plt.plot(t,magnificationspar,"m")
plt.plot(t,magnificationsorb,"y")
```

<img src="figures/BinaryLens_lightcurve_orbital.png" width = 400>

The light curve including orbital motion is in yellow in this plot. 

Note that the `BinaryLightCurveOrbital` returns magnifications, source positions and one additional list containing the separation between the two lenses as it evolves under the orbital motion. This is a very important information because caustics rapidly change with the separation between the lenses.

In the plot for the source trajectory, we can plot caustics at different times with different colors. Here is an example

```
caustictimes = [100,150,200]
colors = [(0,0,1,1),(0.4,0,0.6,1),(0.6,0,0.4,1)]
for i in range(0,3):
    caustics = VBM.Caustics(sorb[caustictimes[i]],q)
    for cau in caustics:
        plt.plot(cau[0],cau[1],color = colors[i])
plt.plot(y1orb,y2orb,"y")
for i in range(0,3):
    plt.plot([y1orb[caustictimes[i]]],[y2orb[caustictimes[i]]],color=colors[i],marker="o")
```

<img src="figures/BinaryLens_lightcurve_orbital_caustics.png" width = 400>

## From velocity components to orbital elements

A circular orbital motion is completely specified by the three components of the angular velocity $\vec \gamma$ of the secondary mass with respect to the first mass. We have

$\gamma_1 \equiv \frac{1}{s} \frac{ds}{dt}$, this is the component along the lens axis;

$\gamma_2 \equiv \frac{d\alpha}{dt}$, this is the component orthogonal to the lens axis;

$\gamma_3 \equiv \frac{1}{s}\frac{ds_z}{dt}$, this is the component along the line of sight.

All values are specified at time $t_{0,orb}=t_{0,par}$. The units are $day^{-1}$.

For more details, you might see the appendix of [Skowron et al. (2011)](https://ui.adsabs.harvard.edu/abs/2011ApJ...738...87S/abstract). In general, the component $\gamma_3$ is poorly constrained by the data, but it is important to stress that setting $\gamma_3=0$ is NOT equivalent to the linear approximation. Since microlensing is only sensitive to the projected distance, orbits with $\gamma_3 \rightarrow - \gamma_3$ are indistinguishable.

Conventional orbital elements can be easily recovered from the components of $\vec \gamma$. In particular, we have

$$a = s \frac{\sqrt{\gamma_1^2 + \gamma_3^2}}{\gamma_3}$$

$$n = \frac{2\pi}{T} =  \frac{\gamma_3}{\sqrt{\gamma_1^2 + \gamma_3^2}} |\vec \gamma |$$

$$ \cos i = \frac{\gamma_3}{\sqrt{\gamma_1^2 + \gamma_3^2}} \frac{\gamma_2}{ |\vec \gamma|}$$

$$ \tan \phi_0 =- \frac{\gamma_1 |\vec \gamma|}{\gamma_3 \sqrt{\gamma_1^2 + \gamma_3^2}} $$

where $a$ is the orbital radius (still in units of the Einstein angle), $T$ is the orbital period in days, $i$ is the inclination with respect to the sky plane, $\phi_0$ is the phase angle from the line of nodes of the orbit with the sky plane. As stated before, it is very difficult to have precise estimates of the orbital parameters even if only one of the three components is poorly constrained.

## Keplerian orbital motion

If the microlensing event is long compared to the orbital period of the binary lens, it is possible to attempt a full orbital fit including eccentricity. A convenient parameterization introduced by [Bozza, Khalouei and Bachelet (2021)](https://ui.adsabs.harvard.edu/abs/2021MNRAS.505..126B/abstract) considers two additional parameters to the three components of the vector $\vec \gamma$.

$r_s \equiv \frac{s_z}{s}$, the ratio of the longitudinal coordinate of the second lens to the projected separation

$a_s \equiv \frac{a}{\sqrt{s_z^2+s^2}}$, the ratio of the semimajor axis to the current 3-D separation of the lenses.

The function `BinaryLightCurveKepler` therefore accepts a total of 14 parameters and its use is similar to that of `BinaryLightCurveOrbital`. So we do not repeat the example here.

The relations of these parameters to the conventional orbital elements are shown in detail in the appendix of [Bozza, Khalouei and Bachelet (2021)](https://ui.adsabs.harvard.edu/abs/2021MNRAS.505..126B/abstract).

## Orbital motion in triple lenses

The full three-body problem requires sophisticated integration of coupled differential equations. However, in some limits, we can neglect some interaction terms and use Keplerian orbital motion. Since the number of parameters is already very large, in VBMicrolensing we introduce a function `TripleLightCurveOrbital` with a minimal set of orbital parameters only for the second lens relative to the first lens assuming **circular motion**. For the third lens, we offer two choices: 
-  **coplanar circular orbital motion** around the first lens (appropriate for multi-planetary systems);
-  **static third lens** (useful when the third lens generates a very short localized anomaly while we are sensitive to the orbital motion of the two main bodies).

Note that the coplanarity assumption allows to derive the components of the orbital motion of the third lens from the components of the orbital motion of the second lens, given the relative projected position (specified through the parameters $s_{13}$ and $\psi$), and the third Kepler's law.

```
import VBMicrolensing
import math
import numpy as np
import matplotlib.pyplot as plt

VBM = VBMicrolensing.VBMicrolensing()


s = 0.9       # Separation of the first planet
q = 0.001       # Mass ratio of first planet
u0 = 0.1       # Impact parameter with respect to center of mass
alpha = 1.0       # Angle of the source trajectory
rho = 0.01       # Source radius
tE = 30.0      # Einstein time in days
t0 = 7500      # Time of closest approach to center of mass
s13 = 1.5       # Separation of second planet
q3 = 0.0003    # Mass ratio of second planet
psi = 0.6      # Position angle of second planet with respect to first
paiN = 0.3     # North component of the parallax vector
paiE = -0.2     # East component of the parallax vector
gamma1 = 0.0000011   # Orbital motion component ds/dt/s of the second lens
gamma2 = 0.005   # Orbital motion component dalpha/dt of the second lens
gamma3 = 0.005   # Orbital motion component dsz/dt/s of the second lens

t = np.linspace(t0, t0+18*tE, 300) # Array of times
VBM.SetObjectCoordinates("17:59:02.3 -29:04:15.2") # Assign RA and Dec to our microlensing event

# Array of parameters. Note that s, q, rho, tE, s13 and q3 are in log-scale
pr = [math.log(s), math.log(q), u0, alpha, math.log(rho), math.log(tE), t0, math.log(s13), math.log(q3), psi, 
      paiN, paiE, gamma1, gamma2, gamma3]

# Calculate the light curve
results = VBM.TripleLightCurveOrbital(pr,t)
```

`TripleLightCurveOrbital` returns a list containing the magnifications, the source positions ($y_1$ and $y_2$), the separations of the second lens $s_{12}$, the separations of the third lens $s_{13}$, the position angle of the third lens from the second lens $\psi$. All these quantities vary in time and are reported in the results list and accessible to the user.

It is important to note that similarly to the `BinaryLightCurveOrbital` function, the reference frame always aligns the horizontal axis with the line joining the second lens to the first. So, it is a frame co-rotating with the first pair of lenses. If we want to go back to an inertial frame we can repeat the calculation with the `TripleLightCurveParallax` function and rotate back as in the following example

```
resultspar = VBM.TripleLightCurveParallax(pr,t)

seps = np.array(results[3])
seps2 = np.array(results[4])
psis = np.array(results[5])
# Calculate the rotation angle at each time
phi1 = np.array([np.arctan2(y2,y1) for (y1,y2) in zip(results[1],results[2])]) - np.array([np.arctan2(y2,y1) for (y1,y2) in zip(resultspar[1],resultspar[2])])

plt.plot(seps*np.cos(phi1),seps*np.sin(phi1),'b') # Plot the orbit of the first planet
plt.plot(seps2*np.cos(phi1+psis),seps2*np.sin(phi1+psis),'g') # Plot the orbit of the second planet
plt.plot([(seps*np.cos(phi1))[0]],[(seps*np.sin(phi1))[0]],'or') # Red dot at starting point
plt.plot([(seps2*np.cos(phi1+psi))[0]],[(seps2*np.sin(phi1+psi))[0]],'or') # Red dot at starting point
plt.plot([0],[0],'or') # Red dot at first lens
ran = 2
plt.xlim(-ran,ran)
plt.ylim(-ran,ran)
```

<img src="figures/multiplanetsorbit.png" width = 400>

In order to keep the third lens static, just set `VBM.block_tertiary_lens = True` before the calculation.

[Go to **Binary Sources**](BinarySources.md)
