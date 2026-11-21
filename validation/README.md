# RF verification

## VNA check

1. Calibrate a 50 Ω two-port VNA to the two SMA cable ends. Connect J1 to Port 1 and J2 to Port 2. If using a one-port measurement, terminate the unused antenna port in 50 Ω.
2. Sweep 5.00–5.50 GHz, including both endpoints. The input target is **S11 and S22 below −10 dB throughout the band**. Record S21 and S12 and the maximum coupling over the full band.
3. Save the complex Touchstone file with the copper-to-copper gap, optional shim thickness, connector batch, and a photo of the assembly. Repeat after fitting any bracket or housing and measure antenna-to-antenna coupling in the intended installation.

## Simulation reference

The supplied HFSS 2018 sweeps use 101 points spaced 5 MHz apart and 50 Ω renormalization. Port order is J1, J2. The simulated planes are 8.89 mm outward from the respective PCB edges at the approximated SMA mating planes. Copper is modeled as PEC. The model includes an approximation of the 132415 Rev B launch and conductive ground shims. Physical seams, solder fillets, mating contacts, fasteners, and material variability remain part of the first-build VNA check.

| Configuration | Worst S11 | Worst S22 | Minimum port isolation |
|---|---:|---:|---:|
| [Nominal open-back assembly](A04_nominal_HFSS.s2p) | −13.80 dB | −13.55 dB | 22.84 dB |
| [0.10 mm spacer below the driver](A04_0p10mm_shim_HFSS.s2p) | −16.31 dB | −16.00 dB | 24.99 dB |

For the nominal assembly, four simulated combinations of correlated material variation and 4.90/5.10 mm patch gaps gave worst S11/S22 of −13.47/−12.15 dB. The 0.10 mm trial also passed two simulated material combinations with worst values of −15.83/−14.28 dB across the two runs. Results shown here describe a single stand-alone antenna.
