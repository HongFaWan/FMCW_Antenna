# FMCW_Antenna

A04 is a **5.00–5.50 GHz dual-linear-polarized antenna** with orthogonal aperture feeds, two stacked circular patches, and a copper horn that flares from 45 to 65 mm. Each antenna uses three 45 × 45 mm PCBs and two Amphenol RF 132415 Rev B SMA connectors.

这是 A04 双极化天线开源制板包。每套各下单一块馈电板、驱动贴片板和寄生贴片板。建议先按敞开背面装配，两片贴片铜面间距为 5.00 mm。板材厚度以介质芯厚为准。 [中文下单参数](fabrication/下单参数.md)

## Build one antenna

| PCB | KiCad project | Gerber and drill ZIP | Dielectric core |
|---|---|---|---|
| Feed | [KiCad](kicad/RF111_ANT_FEED_A04.kicad_pro) | [Gerber](fabrication/RF111_ANT_FEED_A04_Gerber.zip) | RO4350B, 0.508 mm |
| Driven patch | [KiCad](kicad/RF111_ANT_DRIVEN_A04.kicad_pro) | [Gerber](fabrication/RF111_ANT_DRIVEN_A04_Gerber.zip) | F4BM220, 2.50 mm |
| Parasitic patch | [KiCad](kicad/RF111_ANT_PARASITIC_A04.kicad_pro) | [Gerber](fabrication/RF111_ANT_PARASITIC_A04_Gerber.zip) | F4BM220, 0.508 mm |

1. Submit one ZIP per PCB with the stackup and routing notes. [Fabrication notes](fabrication/README.md) · [SHA-256 checksums](fabrication/SHA256SUMS.txt)
2. Cut and fold the copper walls and make the ground tabs and SMA shims. Assemble with a **5.00 mm copper-to-copper gap** between the patches. [Assembly instructions and DXF drawings](mechanical/assembly.md)
3. Calibrate a 50 Ω two-port VNA at the SMA cable ends. Check both input reflections over the entire band and record J1↔J2 isolation. [VNA procedure and HFSS comparison data](validation/README.md)

## Validation

| Open-back configuration | Worst S11 | Worst S22 | Minimum J1↔J2 isolation |
|---|---:|---:|---:|
| Nominal assembly | −13.80 dB | −13.55 dB | 22.84 dB |
| With a 0.10 mm spacer beneath the driven carrier | −16.31 dB | −16.00 dB | 24.99 dB |

These are HFSS results over 5.00–5.50 GHz. Use the nominal assembly for the first build. Compare both configurations on a VNA before adopting the 0.10 mm spacer. The three PCBs are the same in both configurations. All three PCB designs passed KiCad 10.0.8 DRC and the CAM geometry check. [Independent CAM check](verification/CAM_readback.json)

## Source and license

The hardware source, manufacturing files, documentation, and computed antenna data in this repository are available under [CERN-OHL-P-2.0](LICENSE). The stacked-patch and flared-horn concept was inspired by Henrik Forstén's antenna articles. The articles and linked component drawings are available from their respective publishers. [Interferometric SAR antenna](https://hforsten.com/interferometric-synthetic-aperture-radar-drone.html) · [Polarimetric antenna](https://hforsten.com/homemade-polarimetric-synthetic-aperture-radar-drone.html#antennas)
