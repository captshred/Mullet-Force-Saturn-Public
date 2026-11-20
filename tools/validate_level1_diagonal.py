#!/usr/bin/env python3
"""Verify the Phase 3B delta, unchanged approved downhill pixels, and background budget."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "320f0465c1e2c6addbedbbace7ed99e87b390791"
APPROVED_HILL = "b95759d321b9a77a401620e1c552ed28f8c24a0a"
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


def validate(medium_guitar=False, mix_pass1=False):
    assert not mix_pass1 or medium_guitar
    extra_scope = set()
    if medium_guitar:
        import validate_level1_guitar as guitar
        extra_scope = guitar.validate(mix=mix_pass1)
    if subprocess.run(["git", "cat-file", "-e", BASE], cwd=ROOT, capture_output=True).returncode:
        git("fetch", "--no-tags", "--depth=1", "origin", BASE)
    if subprocess.run(["git", "cat-file", "-e", APPROVED_HILL], cwd=ROOT, capture_output=True).returncode:
        git("fetch", "--no-tags", "--depth=1", "origin", APPROVED_HILL)
    changed = set(git("diff", "--name-only", BASE, "--").decode().splitlines())
    assert changed <= PHASE_DELTA | extra_scope, changed - (PHASE_DELTA | extra_scope)

    downhill_delta = {
        "src/intersection_data.h", "src/world_config.h", "tests/intersection/world.c",
        "tools/test-intersection-runtime.py", "tools/validate_level1_diagonal.py",
        "docs/level1-diagonal.md",
    } | {ART + name for name in ("IXMAP.BIN", "IXOFF.BIN", "IXPACK.BIN", "IXPIX.BIN", "manifest.json")}
    changed = set(git("diff", "--name-only", APPROVED_HILL, "--").decode().splitlines())
    assert changed <= downhill_delta | extra_scope, changed - (downhill_delta | extra_scope)

    art = ROOT / ART
    manifest = json.loads((art / "manifest.json").read_text())
    assert manifest["parent"] == APPROVED_HILL and (manifest["width"], manifest["height"]) == (2560, 368)
    for name, digest in manifest["sha256"].items():
        data = (art / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest, name
        if name != "IXPIX.BIN":
            assert (ROOT / "build/cd" / name).read_bytes() == data, name
    old = git("show", f"{APPROVED_HILL}:{ART}IXPIX.BIN")
    current = (art / "IXPIX.BIN").read_bytes()
    assert len(current) == 2560 * 368
    for y in range(304):
        assert current[y*2560:y*2560+2240] == old[y*2240:(y+1)*2240], y
    for x in range(1920, 2560):
        y = 150 + (x - 1920) // 5
        assert all(current[y*2560+x::2560]), x
    for x in range(2262, 2560):
        y = 51 + (x - 1920) // 5
        assert all(current[y*2560+x:(y+100)*2560+x:2560]), x

    assert manifest["resident_cell_bytes"] == 106496 and manifest["VDP2_reserved_bytes"] == 434176
    assert all(manifest[f"{chip}_delta_bytes"] == 0 for chip in ("VDP1", "VDP2", "SCSP"))
    assert manifest["background_heap_bytes"] < manifest["heap_capacity_bytes"]
    link_map = (ROOT / "build/game.map").read_text()
    end = int(re.search(r"0x([0-9a-f]+)\s+__bend =", link_map)[1], 16)
    assert end < 0x060c0000, hex(end)
    print("PASS exact Phase 3B-1 pixels, opaque new road and parking lot, protected source delta, disc assets and graphics budgets")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--medium-guitar", action="store_true")
    parser.add_argument("--mix-pass1", action="store_true")
    args = parser.parse_args()
    validate(args.medium_guitar, args.mix_pass1)
