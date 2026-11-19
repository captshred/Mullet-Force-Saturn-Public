#!/usr/bin/env python3
"""Verify the Phase 3B delta, protected approved geometry and repacked visual art, and background budget."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "320f0465c1e2c6addbedbbace7ed99e87b390791"
APPROVED_HILL = "382b226b476b305c9ebab8e6d2ddbe763603d41b"
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
    if subprocess.run(["git", "cat-file", "-e", APPROVED_HILL], cwd=ROOT, capture_output=True).returncode:
        git("fetch", "--no-tags", "--depth=1", "origin", APPROVED_HILL)
    changed = set(git("diff", "--name-only", BASE, "--").decode().splitlines())
    assert changed <= PHASE_DELTA, changed - PHASE_DELTA

    polish_delta = {
        "src/intersection_data.h", "tools/validate_level1_diagonal.py", "docs/level1-diagonal.md",
    } | {ART + name for name in ("IXMAP.BIN", "IXOFF.BIN", "IXPACK.BIN", "IXPIX.BIN", "manifest.json")}
    changed = set(git("diff", "--name-only", APPROVED_HILL, "--").decode().splitlines())
    assert changed <= polish_delta, changed - polish_delta

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
    assert len(old) == len(current)
    for y in range(368):
        start = y * 2560
        assert current[start:start+1928] == old[start:start+1928], y
    for x in range(1920, 2560):
        drop = (x - 1920) // 5
        road = (158 + drop) * 2560 + x
        assert current[road::2560] == old[road::2560], x
        assert all(current[road::2560]), x
        # The only transparent pixels in a facade column are above its roof.
        if 1928 <= x < 2240:
            column = current[drop*2560+x:road:2560]
            first_solid = next(i for i, pixel in enumerate(column) if pixel)
            assert all(column[first_solid:]), x
        if x >= 2257:
            roof = 61 if x < 2398 else 85
            assert all(current[roof*2560+x:road:2560]), x
    # Each storefront starts at a level roof on its own stepped foundation.
    for start, end, roof in ((1936, 2028, 13), (2029, 2133, 41), (2134, 2239, 57)):
        row = current[roof*2560+start:roof*2560+end+1]
        assert row and row[0] and row == row[:1]*len(row), start
    assert hashlib.sha256((ROOT / "build/cd/NSPAL.BIN").read_bytes()).hexdigest() == manifest["palette_sha256"]

    assert manifest["resident_cell_bytes"] == 106496 and manifest["VDP2_reserved_bytes"] == 434176
    assert all(manifest[f"{chip}_delta_bytes"] == 0 for chip in ("VDP1", "VDP2", "SCSP"))
    assert manifest["background_heap_bytes"] < manifest["heap_capacity_bytes"]
    link_map = (ROOT / "build/game.map").read_text()
    end = int(re.search(r"0x([0-9a-f]+)\s+__bend =", link_map)[1], 16)
    assert end < 0x060c0000, hex(end)
    print("PASS exact pre-bend and road pixels, opaque facades and parking lot, protected source delta, disc assets and graphics budgets")


if __name__ == "__main__":
    validate()
