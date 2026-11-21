# PCB fabrication

Order each of the three Gerber ZIPs as a separate board. Each antenna needs one of each PCB. The outlines are nominally 45.00 × 45.00 mm, with four Ø3.20 mm non-plated mounting holes on 36.00 × 36.00 mm centers. Route along the center of Edge.Cuts.

| Board | Dielectric core thickness | Finished copper and finish |
|---|---|---|
| Feed | Rogers RO4350B, 0.508 mm | 35 µm on both sides, ENIG. F.Cu is the slotted ground. B.Cu is the feed network. |
| Driven patch | Wangling F4BM220, 2.50 mm | 35 µm on F.Cu, ENIG, Ø20.00 mm patch. Clear B.Cu. |
| Parasitic patch | Wangling F4BM220, 0.508 mm | 35 µm on B.Cu, ENIG, Ø21.70 mm patch. Clear F.Cu. |

The quoted thicknesses are dielectric thickness, exclusive of copper and finish. Confirm the exact laminate, core thickness, copper thickness and routing tolerances before fabrication. The feed-board simulation uses design Dk 3.66. Both patch boards use Dk 2.20. The F4BM standard thicknesses above are listed with ±0.08 mm and ±0.04 mm tolerances, respectively. [Rogers RO4350B](https://www.rogerscorp.com/advanced-electronics-solutions/ro4000-series-laminates/ro4350b-laminates) · [Wangling F4BM220](https://www.wang-ling.com.cn/allproducts/160.html)

- The feed board has four Ø0.30 mm plated ground vias. Etch the two H apertures out of the ground copper and retain the dielectric below. Preserve the solder mask openings as drawn. The SMA signal land is 1.50 × 2.05 mm. Each ground land is 1.60 × 6.00 mm, centered on ±4.25 mm either side of its connector axis.
- The driven board has two edge reliefs 11.00 mm wide × 6.30 mm deep for the SMA jaws and four more 5.20 mm wide × 3.20 mm deep for the horn ground tabs. Keep the internal corner radius at or below 0.50 mm, and hold width and depth to ±0.10 mm. Check the fabricator's tool diameter before approving the order.
- Use two 132415 Rev B SMA edge-launch connectors per antenna. The feed board measures about 0.578 mm copper-to-copper. Use fitted tinned-copper shims to bridge the nominal 0.36 mm gap below the two jaws on the non-signal side of each connector. [Amphenol customer drawing](https://www.amphenolrf.com/en-us/assets/file/4065786574/) · [Assembly instructions](../mechanical/assembly.md)

The distributed Gerbers are ready to send with the fabrication notes. Open the three projects in KiCad 10.0.8 or compatible and keep the project-local footprint library beside them. To regenerate the Gerbers and DRC reports with KiCad CLI, run these commands from the repository root.

    python kicad/export_fabrication.py
    python verification/verify_cam.py

Set the export script's --cli option if kicad-cli is outside PATH. Exporting rewrites the three ZIPs and their manifest. ZIP digests can change with the KiCad version and export timestamps. [Published checksums](SHA256SUMS.txt) · [中文下单参数](下单参数.md)
