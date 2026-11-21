"""Run KiCad DRC and export one Gerber/Excellon ZIP per antenna PCB."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BOARD_TYPES = ("FEED", "DRIVEN", "PARASITIC")


def run(cli, *arguments):
    subprocess.run([cli, "pcb", *map(str, arguments)], check=True)


def package(cli, kind, manufacturing, verification):
    name = f"RF111_ANT_{kind}_A04"
    board = HERE / (name + ".kicad_pcb")
    is_feed = kind == "FEED"
    common = "F.Cu,B.Cu,F.Mask,B.Mask,Edge.Cuts"
    silk = "B.SilkS" if is_feed else "F.SilkS"
    layers = common + "," + silk

    with TemporaryDirectory(prefix="rf111-ant-cam-") as folder:
        stage = Path(folder)
        log = stage / "drc.json"
        run(cli, "drc", "--format", "json", "--output", log, board)
        drc = json.loads(log.read_text(encoding="utf-8"))
        expected = []
        if (sorted(v["type"] for v in drc["violations"]) != expected
                or any(v["severity"] != "warning" for v in drc["violations"])
                or drc["unconnected_items"] or drc["schematic_parity"]):
            raise RuntimeError(f"Unexpected DRC findings in {name}: {drc}")
        shutil.copyfile(log, verification / (name + "-DRC.json"))
        log.unlink()

        output = str(stage) + "/"
        run(cli, "export", "gerbers", "--output", output, "--layers", layers, board)
        run(cli, "export", "drill", "--output", output, "--format", "excellon",
            "--excellon-units", "mm", "--excellon-separate-th", board)
        files = sorted(p for p in stage.iterdir() if p.is_file())
        # KiCad emits a syntactically valid but empty PTH file for the carriers.
        files = [p for p in files if is_feed or p.name != name + "-PTH.drl"]
        for ending in (".gtl", ".gbl", ".gts", ".gbs", ".gm1", "-NPTH.drl"):
            if not any(p.name.endswith(ending) for p in files):
                raise RuntimeError(f"Missing {ending} in {name}")
        zip_path = manufacturing / (name + "_Gerber.zip")
        with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
            for p in files:
                archive.write(p, p.name)
        with ZipFile(zip_path) as archive:
            if archive.testzip():
                raise RuntimeError(f"ZIP integrity failed for {zip_path}")
    return zip_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", default=shutil.which("kicad-cli") or "kicad-cli")
    arguments = parser.parse_args()
    manufacturing = ROOT / "fabrication"
    verification = ROOT / "verification"
    manufacturing.mkdir(exist_ok=True)
    verification.mkdir(exist_ok=True)
    packages = [package(arguments.cli, kind, manufacturing, verification) for kind in BOARD_TYPES]
    checksum_lines = [
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}" for p in packages
    ]
    (manufacturing / "SHA256SUMS.txt").write_text("\n".join(checksum_lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
