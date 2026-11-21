"""Read back the final A04 Gerber/Excellon files against the assembly geometry."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile


BOARD_TYPES = ("FEED", "DRIVEN", "PARASITIC")
COPPER_MASK = (".gtl", ".gbl", ".gts", ".gbs")
MOUNT_HOLES = {(37.0, -37.0), (37.0, -73.0), (73.0, -37.0), (73.0, -73.0)}
BOX = (32.5, -77.5, 77.5, -32.5)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def member(zip_file, suffix):
    matches = [name for name in zip_file.namelist() if name.endswith(suffix)]
    require(len(matches) == 1, f"Expected one {suffix} in {zip_file.filename}: {matches}")
    return zip_file.read(matches[0]).decode("ascii")


def profile(gerber):
    require("%FSLAX46Y46*%" in gerber and "%MOMM*%" in gerber, "Unexpected Gerber coordinates")
    segments = []
    current = None
    for line in gerber.splitlines():
        m = re.fullmatch(r"X(-?\d+)Y(-?\d+)D0([12])\*", line)
        if m is None:
            continue
        point = (int(m[1]) / 1e6, int(m[2]) / 1e6)
        if m[3] == "1":
            require(current is not None and current != point, "Invalid profile stroke")
            require(current[0] == point[0] or current[1] == point[1], "Expected orthogonal profile")
            segments.append((current, point))
        current = point
    require(segments, "Missing profile segments")
    adjacent = {}
    for start, end in segments:
        adjacent.setdefault(start, set()).add(end)
        adjacent.setdefault(end, set()).add(start)
    require(len(adjacent) == len(segments) and all(len(v) == 2 for v in adjacent.values()),
            "Open or duplicate edges in profile")
    p = [segments[0][0]]
    previous, current = p[0], segments[0][1]
    while current != p[0]:
        require(current not in p, "Malformed board profile")
        p.append(current)
        previous, current = current, next(iter(adjacent[current] - {previous}))
    require(len(p) == len(adjacent), "Multiple closed profiles in the board outline")
    bounds = (min(x for x, _ in p), min(y for _, y in p),
              max(x for x, _ in p), max(y for _, y in p))
    require(bounds == BOX, f"Unexpected outline bounds {bounds}")
    return p


def drills(text):
    require("METRIC" in text and "G90" in text, "Unexpected drill coordinates")
    result = []
    tools = {int(i): float(d) for i, d in re.findall(r"^T(\d+)C([\d.]+)\s*$", text, re.M)}
    active = None
    for line in text.splitlines():
        if m := re.fullmatch(r"T(\d+)", line):
            active = tools[int(m[1])]
        if m := re.fullmatch(r"X(-?[\d.]+)Y(-?[\d.]+)", line):
            require(active is not None, f"No drill tool for {line}")
            result.append((float(m[1]), float(m[2]), active))
    return result


def flashes(gerber):
    definitions = {}
    active = None
    result = []
    for line in gerber.splitlines():
        m = re.fullmatch(r"%ADD(\d+)([RC]),([\d.X]+)\*%", line)
        if m:
            definitions[int(m[1])] = (m[2], *map(float, m[3].split("X")))
        m = re.fullmatch(r"D(\d+)\*", line)
        if m:
            active = int(m[1])
        m = re.fullmatch(r"X(-?\d+)Y(-?\d+)D03\*", line)
        if m:
            result.append((int(m[1]) / 1e6, int(m[2]) / 1e6, *definitions[active]))
    return result


def regions(gerber):
    blocks = re.findall(r"G36\*(.*?)G37\*", gerber, re.S)
    return [[(int(x) / 1e6, int(y) / 1e6)
             for x, y in re.findall(r"X(-?\d+)Y(-?\d+)D0[12]\*", block)] for block in blocks]


def contains(polygon, x, y):
    inside = False
    for (a, b), (c, d) in zip(polygon, polygon[1:] + polygon[:1]):
        if (b > y) != (d > y) and x < (c - a) * (y - b) / (d - b) + a:
            inside = not inside
    return inside


def board_xy(x, y):
    return (round(55 + x, 6), round(-55 + y, 6))


def launch_xy(port, u, v):
    return board_xy(-22.5 + u, v) if port == 0 else board_xy(4 + v, -22.5 + u)


def footprint_shape(port, u, v, length, width):
    a, b = (length, width) if port == 0 else (width, length)
    return (*launch_xy(port, u, v), "R", a, b)


def check_feed(z, geometry):
    top = member(z, ".gtl")
    bottom = member(z, ".gbl")
    top_flashes = Counter(flashes(top))
    bottom_flashes = Counter(flashes(bottom))
    bottom_mask = regions(member(z, ".gbs"))
    full_mask = regions(member(z, ".gts"))
    plane = regions(top)
    require(len(plane) == len(full_mask) == 1, "Expected continuous top ground and full mask opening")
    ground = []
    via = []
    for port in (0, 1):
        signal = footprint_shape(port, 1.025, 0, 2.05, 1.50)
        require(bottom_flashes[signal] == 1, f"Wrong Rev B signal land J{port+1}")
        for v in (-4.25, 4.25):
            land = footprint_shape(port, 3.30, v, 6.00, 1.60)
            ground.append(land)
            via.append((*launch_xy(port, 5.95, v), .30))
            for x in (.31, 6.29):
                for y in (v - .79, v + .79):
                    pt = launch_xy(port, x, y)
                    require(any(contains(p, *pt) for p in bottom_mask), "Bottom GND land covered")
                    require(contains(full_mask[0], *pt), "Top GND land covered")
        for x in (.01, 2.04):
            for y in (-.74, .74):
                require(any(contains(p, *launch_xy(port, x, y)) for p in bottom_mask),
                        "Signal land covered")
    for land in ground:
        require(top_flashes[land] == bottom_flashes[land] == 1, f"Wrong Rev B ground land {land}")
    plated = drills(member(z, "-PTH.drl"))
    require(Counter(plated) == Counter(via), "Incorrect actual plated launch via map")
    for port, slot in enumerate(geometry["ports"]):
        for du, dv, is_copper in [(0, .11, False), (.15, -3, False), (.70, -2, True),
                                     (1.7, 4.7, False), (-1.7, -4.7, False),
                                     (2.65, 4.7, True), (1.4, 3.6, True)]:
            u, v = slot["center"][0] + du, slot["center"][1] + dv
            xy = board_xy(u, v) if port == 0 else board_xy(v, u)
            require(contains(plane[0], *xy) == is_copper, f"Incorrect J{port+1} H slot at {xy}")
    for side, center in [("-X", -11), ("-Y", -9), ("+X", 0), ("+Y", 0)]:
        for depth in (.40, 2.47):
            for v in (center-1.95, center+1.95):
                a = (-22.5 + depth) if side[0] == "-" else (22.5 - depth)
                pt = board_xy(a, v) if side[1] == "X" else board_xy(v, a)
                require(contains(plane[0], *pt) and contains(full_mask[0], *pt),
                        f"Ground tab has no exposed ground at {pt}")
    return {"Rev_B_signal_and_grounds": True, "ground_tabs_exposed": 4,
            "slotted_ground_checked": True, "PTH_mm": sorted(plated)}


def check_carrier(z, kind, geometry):
    is_driven = kind == "DRIVEN"
    live, dead = (".gtl", ".gbl") if is_driven else (".gbl", ".gtl")
    open_mask = ".gts" if is_driven else ".gbs"
    diameter = geometry["patches"][0 if is_driven else 1]["size"]
    require(flashes(member(z, live)) == [(55, -55, "C", diameter)], "Wrong radiator")
    require(not flashes(member(z, dead)) and "G36*" not in member(z, dead), "Unwanted back copper")
    require((55, -55, "C", round(diameter + .60, 6)) in flashes(member(z, open_mask)),
            "Radiator mask opening differs")
    require(not any(n.endswith("-PTH.drl") for n in z.namelist()), "Unexpected plated file")
    return {"active_copper": live, "patch_diameter_mm": diameter, "PTH_mm": []}


def check_profile(z, kind):
    contour = profile(member(z, ".gm1"))
    expect = {board_xy(x, y) for x in (-22.5, 22.5) for y in (-22.5, 22.5)}
    if kind == "DRIVEN":
        for side, ctr, wid, depth in [("-X", 0, 11, 6.30), ("-Y", 4, 11, 6.30),
                                        ("-X", -11, 5.2, 3.2), ("-Y", -9, 5.2, 3.2),
                                        ("+X", 0, 5.2, 3.2), ("+Y", 0, 5.2, 3.2)]:
            for inset in (0, depth):
                for v in (ctr - wid/2, ctr + wid/2):
                    a = -22.5 + inset if side[0] == "-" else 22.5 - inset
                    expect.add(board_xy(a, v) if side[1] == "X" else board_xy(v, a))
    require(set(contour) == expect and len(contour) == len(expect), f"Bad {kind} board profile")
    return len(contour)


def verify(root, kind, geometry):
    name = f"RF111_ANT_{kind}_A04"
    zip_path = root / "fabrication" / f"{name}_Gerber.zip"
    drc = json.loads((root / "verification" / f"{name}-DRC.json").read_text(encoding="utf-8"))
    require(drc["source"] == f"{name}.kicad_pcb" and
            not any(drc[k] for k in ("violations", "unconnected_items", "schematic_parity")),
            f"Missing clean DRC report for {name}")
    with ZipFile(zip_path) as z:
        require(z.testzip() is None, f"Unreadable package {name}")
        for ext in (".gtl", ".gbl", ".gts", ".gbs", ".gm1", "-NPTH.drl"):
            member(z, ext)
        require(any(f.endswith(".gbo" if kind == "FEED" else ".gto") for f in z.namelist()),
                "Missing assembly orientation silkscreen")
        holes = drills(member(z, "-NPTH.drl"))
        require(Counter(holes) == Counter((x,y,3.2) for x, y in MOUNT_HOLES), f"Bad NPTH map {name}")
        segments = check_profile(z, kind)
        detail = check_feed(z, geometry) if kind == "FEED" else check_carrier(z, kind, geometry)
    return {"zip": zip_path.name, "sha256": hashlib.sha256(zip_path.read_bytes()).hexdigest(),
            "drc_violations": 0, "closed_profile_segments": segments, "outline_mm": [45, 45],
            "NPTH_mm": sorted(holes), **detail}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    root = cli.parse_args().root
    geometry = json.loads((root / "kicad" / "geometry.json").read_text(encoding="utf-8"))
    results = [verify(root, kind, geometry) for kind in BOARD_TYPES]
    sums = (root / "fabrication" / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines()
    require(set(sums) == {f"{r['sha256']}  {r['zip']}" for r in results}, "ZIP digest mismatch")
    (root / "verification" / "CAM_readback.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
