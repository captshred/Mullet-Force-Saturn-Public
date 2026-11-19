#!/usr/bin/env python3
"""Verify the Phase 3B delta, unchanged Phase 3A pixels, and background budget."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "320f0465c1e2c6addbedbbace7ed99e87b390791"
ART = "assets/level1-intersection/"
PHASE_DELTA = {
    "Makefile",
    "src/arcade_fx.h",
    "src/intersection_data.h",
    "src/main.c",
    "src/parallax.c",
    "src/world_config.h",
    "tests/intersection/cache.c",
    "tests/intersection/world.c",
    "tools/level1-sfx-pcm8-pass1.py",
    "tools/test-intersection.py",
    "tools/test-intersection-runtime.py",
    "tools/validate_level1_diagonal.py",
    "docs/level1-diagonal.md",
} | {ART + name for name in ("IXMAP.BIN", "IXOFF.BIN", "IXPACK.BIN", "IXPIX.BIN", "manifest.json")}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def validate():
    if subprocess.run(["git", "cat-file", "-e", BASE], cwd=ROOT, capture_output=True).returncode:
        git("fetch", "--no-tags", "--depth=1", "origin", BASE)
    changed = set(git("diff", "--name-only", BASE, "--").decode().splitlines())
    assert changed <= PHASE_DELTA, changed - PHASE_DELTA

    art = ROOT / ART
    manifest = json.loads((art / "manifest.json").read_text())
    assert manifest["parent"] == BASE and (manifest["width"], manifest["height"]) == (2240, 304)
    for name, digest in manifest["sha256"].items():
        data = (art / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest, name
        if name != "IXPIX.BIN":
            assert (ROOT / "build/cd" / name).read_bytes() == data, name
    old = git("show", f"{BASE}:{ART}IXPIX.BIN")
    current = (art / "IXPIX.BIN").read_bytes()
    assert len(current) == 2240 * 304
    for y in range(240):
        assert current[y*2240:y*2240+1920] == old[y*1920:(y+1)*1920], y
    for x in range(1920, 2240):
        y = 150 + (x - 1920) // 5
        assert all(current[y*2240+x::2240]), x

    assert manifest["resident_cell_bytes"] == 106496 and manifest["VDP2_reserved_bytes"] == 434176
    assert all(manifest[f"{chip}_delta_bytes"] == 0 for chip in ("VDP1", "VDP2", "SCSP"))
    assert manifest["background_heap_bytes"] < manifest["heap_capacity_bytes"]
    link_map = (ROOT / "build/game.map").read_text()
    end = int(re.search(r"0x([0-9a-f]+)\s+__bend =", link_map)[1], 16)
    assert end < 0x060c0000, hex(end)
    print("PASS exact Phase 3A pixels, opaque new road, protected source delta, disc assets and graphics budgets")


if __name__ == "__main__":
    validate()
