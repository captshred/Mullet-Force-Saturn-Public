#!/usr/bin/env python3
"""Prune audited legacy assets from the staged Noah production profile."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def numbered(prefix, indices, extension="TGA", width=2):
    return {f"{prefix}{index:0{width}d}.{extension}" for index in indices}


def stage(disc):
    # These manifests record registrations already retired in the production loader.
    obsolete = set()
    for name in ("legacy-sprite-cleanup", "legacy-sprite-phase2", "duplicate-texture-cleanup"):
        obsolete.update(json.loads((ROOT / "assets" / f"{name}.json").read_text())["removed"])

    obsolete.update(numbered("RN", range(24)))
    for prefix in ("BU", "CH", "NL"):
        obsolete.update(numbered(prefix, range(15)))
    obsolete.update(numbered("EN", range(12)))
    for prefix, count in (("TU", 3), ("TC", 3), ("ST", 5)):
        obsolete.update(numbered(prefix, range(count), width=1))
    for prefix in ("RC", "RD", "COMBAT/CT"):
        obsolete.update(numbered(prefix, range(2), width=1))
    obsolete.update(numbered("COMBAT/CA", (51, 52)))

    # The original-three boot mask never loads these full-gallery alternatives.
    for prefix in ("AB", "AC"):
        obsolete.update(numbered(prefix, (pose * 10 + part for pose in range(4, 7)
                                          for part in range(3))))
    old_polish = set(range(39)) - {0, 1, 2, 18, 19, 20}
    obsolete.update(numbered("P", old_polish, width=3))
    obsolete.update(f"{stem}.BIN" for stem in (
        "STCELLS", "STMAP", "STPAL", "CIPAL", "PCHUNK", "PSKY", "PSMAP"
    ))
    obsolete.add("ALEVEL2/WDEATH.MAP")
    if len(obsolete) != 232:
        raise SystemExit(f"Expected 232 audited disc exclusions, got {len(obsolete)}")
    obsolete.update(numbered("RICKY/RK", (23, 24)))

    required = {
        "STAGE.TON", "STAGE.SEQ", "FX.TON", "FX.SEQ", "CUSTOM.MAP", "CARPASS.TON",
        "CICELL.BIN", "CIMAP.BIN", "NSPAL.BIN", "IXPACK.BIN", "IXOFF.BIN",
        "IXMAP.BIN", "LCSKY.BIN", "LCMAP.BIN", "MF88.TGA", "RBV00.TGA",
        "EXPLODE.TGA", "RICKY/BSFX.TON", "RICKY/BSFX.SEQ",
        "ALEVEL2/WDEATH.TON", "ALEVEL2/WDEATH.SEQ", "ALEVEL2/WMUSIC.MAP",
        "ALEVEL2/WMUSIC.TON", "ALEVEL2/WMUSIC.SEQ", "ALEVEL2/WFIRE.MAP", "ALEVEL2/WFIRE.TON",
    }
    required.update(numbered("COMBAT/CA", (0, 1, *range(3, 8), 28, 29, *range(31, 36))))
    for actor in ("B", "C"):
        required.update(numbered(f"COMBAT/N{actor}", range(1, 5), "BIN"))
    required.update(numbered("RICKY/RK", range(23)))
    required.update(numbered("CP", range(10)))
    required.update(numbered("CQ", range(4)))

    missing = {path for path in required if not (disc / path).is_file()}
    if missing or required & obsolete:
        raise SystemExit(f"Required disc files missing or excluded: {sorted(missing | (required & obsolete))}")
    for path in sorted(obsolete):
        (disc / path).unlink(missing_ok=True)

    # Include the two ISO dot records and count the future executable on a clean stage.
    root_records = len(list(disc.iterdir())) + 2 + int(not (disc / "0.bin").exists())
    if root_records > 256:
        raise SystemExit(f"Production root has {root_records} records, beyond the GFS limit")
    print(f"PASS production staging: {len(obsolete)} exclusions, {root_records} ISO root records")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("disc", type=Path)
    stage(parser.parse_args().disc)
