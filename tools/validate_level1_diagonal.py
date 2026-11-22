#!/usr/bin/env python3
"""Verify the Phase 3B delta, unchanged approved downhill pixels, and background budget."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "320f0465c1e2c6addbedbbace7ed99e87b390791"
APPROVED_HILL = "45ac7b3e80e77b1971e796b4eaa6b2a5aa3f6cff"
ART = "assets/level1-intersection/"
DEFINITIVE = "732fbf3ddeef383fcb80ddfddd4b977afe9ab2b2"
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


HQ_DELTA = {
    "src/parallax.c", "src/intersection_data.h",
    "tools/validate_level1_diagonal.py", "tools/validate_level1_guitar.py",
    "tools/level1_music_mix.py",
    "docs/level1-diagonal.md", "docs/downhill-hq-comparison.png",
} | {ART + name for name in ("IXMAP.BIN", "IXOFF.BIN", "IXPACK.BIN", "IXPIX.BIN", "manifest.json")}
VEHICLE_DELTA = {
    "assets/cd/MF88.TGA", "src/game.c", "src/game.h", "src/main.c", "src/music.c",
    "assets/cd/CARPASS.TON",
    "src/enemy_bank_config.h", "make/saturn.mk", "tools/build-native.sh",
    "tools/build-source-complete.sh", "tools/audit-sprite-memory.py",
    "tools/test-intersection.py", "tools/test-intersection-runtime.py", "tools/test-ricky-jump-render.py",
    "tests/intersection/vehicle.c", "tests/intersection/world.c", "docs/level1-vehicle-ambush.md",
    "downloads/mullet-force-vehicle-ambush.zip",
}
CLARITY_REVIEW = {
    "docs/downhill-clarity-review/" + name for name in (
        "01-laundry-parking-native.png", "02-auto-service-native.png",
        "03-downhill-composite-native.png", "04-source-runtime-evidence.png",
        "IXPIX-proposed.BIN", "README.md",
    )
}
LINE_REVIEW = {
    "docs/horizontal-line-restoration-review/" + name for name in (
        "A-original-native.png", "B-structural-overlay-4x.png",
        "C-corrected-native.png", "D-before-after-4x.png", "E-changed-pixels-4x.png",
        "F-full-downhill-native.png", "G-garage-upper-decks-and-cars-4x.png",
        "H-storefront-details-4x.png", "I-full-change-map-2x.png",
        "IXPIX-garage-proposed.BIN", "IXPIX-full-proposed.BIN", "README.md",
    )
}
MEGA_DELTA = {
    "tools/clean-parking-garage.py",
    "tools/correct-garage-geometry.py",
    "downloads/garage-geometry-correction/mullet-force-garage-geometry.zip",
    "downloads/garage-geometry-correction/garage-geometry-comparison.png",
    "downloads/garage-geometry-correction/garage-geometry-scroll.mp4",
    "downloads/parking-garage-cleanup/mullet-force-parking-garage-cleanup.zip",
    "downloads/parking-garage-cleanup/garage-before-after.png",
    "tools/prepare-mega-arcade.py", "tools/pack-level1-panorama.py", "docs/level1-mega-arcade.md",
    "downloads/mullet-force-mega-arcade-phase4a.zip", "src/world_config.h",
    "tools/import-mega-arcade-art.py", "downloads/mullet-force-mega-arcade-art.zip",
    "tests/parallax_mock/jo/jo.h", "tests/intersection/cache.c",
    "tools/recompose-mega-arcade.py", "downloads/mullet-force-mega-arcade-phase4a2.zip",
}
HQ_DELTA |= VEHICLE_DELTA | CLARITY_REVIEW | LINE_REVIEW | MEGA_DELTA | {
    "downloads/mullet-force-downhill-clarity.zip",
    "downloads/mullet-force-horizontal-line-restoration.zip",
}
PHASE_DELTA |= HQ_DELTA


BRUCE_ASSET_TREE = "84dd2903d3f8120e663a718d025a8ce9eb235f06"
BRUCE_RUNTIME_DELTA = {
    "src/enemy_sprite_bank.c", "src/enemy_sprite_bank.h",
    "src/bruce.c", "src/bruce.h", "src/game.h", "src/ricky_animation.c",
    "make/saturn.mk", "tools/build-native.sh", "tools/build-source-complete.sh",
    "tools/stage-bruce-bank.py", "tools/validate_level1_diagonal.py",
    "tests/bruce_runtime_test.c",
    "docs/bruce-phase3a-runtime.md", "docs/bruce-phase3b-combat.md", "Makefile",
}


def bruce_scope():
    if not (ROOT / "assets/bruce").is_dir():
        return set()
    assert git("rev-parse", "HEAD:assets/bruce").decode().strip() == BRUCE_ASSET_TREE
    assert not git("diff", "HEAD", "--", "assets/bruce"), "approved Bruce assets changed"
    assets = set(git("ls-tree", "-r", "--name-only", "HEAD", "assets/bruce").decode().splitlines())
    return BRUCE_RUNTIME_DELTA | assets


def validate_hq_scope():
    if subprocess.run(["git", "cat-file", "-e", APPROVED_HILL], cwd=ROOT, capture_output=True).returncode:
        git("fetch", "--no-tags", "--depth=1", "origin", APPROVED_HILL)
    changed = set(git("diff", "--name-only", APPROVED_HILL, "--").decode().splitlines())
    import drop_zone_sequence
    import level1_housekeeping
    scope = HQ_DELTA | bruce_scope() | drop_zone_sequence.SCOPE | level1_housekeeping.SCOPE
    assert changed <= scope, changed - scope
    return scope


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

    validate_hq_scope()

    if (ROOT / "assets/cd/CARPASS.TON").exists():
        tone = (ROOT / "assets/cd/CARPASS.TON").read_bytes()
        from level1_housekeeping import CAR_FRAMES, sample
        layer, start = sample(tone, 3)
        assert tone[layer+3] & 0xf0 == 0x10
        assert int.from_bytes(tone[layer+6:layer+8], "big") == 0
        assert int.from_bytes(tone[layer+8:layer+10], "big") == CAR_FRAMES
        assert tone[start+CAR_FRAMES:] == bytes(-(start+CAR_FRAMES) % 4)
        report = json.loads((ROOT / "assets/music/report.json").read_text())
        free = 0x80000 - report["sound_ram_high_water"] - len(tone)
        assert free >= 0 and free == report["level1_housekeeping"]["car_profile_free_bytes"]
    art = ROOT / ART
    manifest = json.loads((art / "manifest.json").read_text())
    width, height = manifest["width"], manifest["height"]
    assert manifest["parent"] == APPROVED_HILL and width in (2560, 3200, 3328) and height == 368
    for name, digest in manifest["sha256"].items():
        data = (art / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest, name
        if name != "IXPIX.BIN":
            assert (ROOT / "build/cd" / name).read_bytes() == data, name
    old = git("show", f"{APPROVED_HILL}:{ART}IXPIX.BIN")
    panorama = (art / "IXPIX.BIN").read_bytes()
    assert len(panorama) == width * height
    geometry_pass = importlib.import_module("correct-garage-geometry")
    previous = geometry_pass.baseline()
    assert panorama == geometry_pass.paint(previous)
    assert len(panorama) == len(previous) and width == geometry_pass.WIDTH
    for i, (before, after) in enumerate(zip(previous, panorama)):
        if before != after:
            row, column = divmod(i, width)
            assert 136 <= row <= 297 and 2552 <= column <= 2688
            assert before and after, "garage geometry changed transparency"
            assert column >= 2560 or row < 292, "garage geometry reached the downhill roadway"
    panorama = previous  # Compare the parent against the older approved art checks below.
    cleanup = importlib.import_module("clean-parking-garage")
    approved = cleanup.baseline()
    assert panorama == cleanup.paint(approved), "unexpected garage panorama changes"
    assert width == cleanup.WIDTH and len(panorama) == len(approved)
    for i, (before, after) in enumerate(zip(approved, panorama)):
        if before != after:
            row, column = divmod(i, width)
            assert 265 <= row <= 322 and 2561 <= column <= 2688
            assert before and after, "garage cleanup changed transparency"
    current = b"".join(panorama[y:y+2560] for y in range(0, len(panorama), width))
    if width > 2560:
        assert all(0 not in panorama[y+2560:y+width] for y in range(127*width, len(panorama), width))
        assert all(panorama[y+2559] == panorama[y+2560]
                   for y in range(127*width, len(panorama), width) if panorama[y+2559])
    assert len(old) == len(current)
    for y in range(368):
        start = y * 2560
        assert current[start:start+1928] == old[start:start+1928], y
    for x in range(1928, 2560):
        drop = (x - 1920) // 5
        road = (168 + drop) * 2560 + x
        assert current[road::2560] == old[road::2560], x
        column = current[x:road:2560]
        first_solid = next(i for i, pixel in enumerate(column) if pixel)
        assert all(column[first_solid:]), x
    proposal = ROOT / "docs/downhill-clarity-review/IXPIX-proposed.BIN"
    line_proposal = ROOT / "docs/horizontal-line-restoration-review/IXPIX-full-proposed.BIN"
    if line_proposal.exists():
        assert current == line_proposal.read_bytes(), "runtime art differs from the reviewed line restoration"
        geometry = proposal.read_bytes()
        assert current.count(0) == geometry.count(0)
        assert all((a == 0) == (b == 0) for a, b in zip(current, geometry))
    elif proposal.exists():
        assert current == proposal.read_bytes(), "runtime art differs from the reviewed geometry"
    if proposal.exists():
        if subprocess.run(["git", "cat-file", "-e", DEFINITIVE], cwd=ROOT, capture_output=True).returncode:
            git("fetch", "--no-tags", "--depth=1", "origin", DEFINITIVE)
        definitive = git("show", f"{DEFINITIVE}:{ART}IXPIX.BIN")
        for x in range(1928, 2560):
            protected = (146 + (x - 1920) // 5) * 2560 + x
            assert current[protected::2560] == definitive[protected::2560], x
            if line_proposal.exists():
                assert current[protected::2560] == geometry[protected::2560], x
    from wingsuit_disc import directory_records
    disc = (ROOT / "build/mullet-force.bin").read_bytes()
    root = list(directory_records(disc, disc[16*2048+156:16*2048+190]))
    # Count both ISO directory records for "." and "..", as GFS does.
    visible = {name for name, _ in root[:256]}
    audio = {"CUSTOM.MAP", "FX.SEQ", "FX.TON", "STAGE.SEQ", "STAGE.TON"}
    if (ROOT / "build/cd/CARPASS.TON").exists():
        audio.add("CARPASS.TON")
    assert audio <= visible, f"Level 1 audio outside GFS root table: {sorted(audio-visible)}"
    print("PASS Level 1 audio files fit the 256-record GFS root lookup")

    palette = ROOT / "build/cd/NSPAL.BIN"
    assert hashlib.sha256(palette.read_bytes()).hexdigest() == manifest["palette_sha256"]
    assert manifest["packed_source_storage"] == "low-work-ram"
    assert manifest["packed_low_work_ram_bytes"] == manifest["packed_source_bytes"] <= 0x80000
    assert manifest["background_heap_bytes"] == manifest["map_offset_heap_bytes"] + manifest["decode_cache_heap_bytes"]
    assert manifest["peak_cd_staging_heap_bytes"] < manifest["heap_capacity_bytes"]

    assert manifest["resident_cell_bytes"] == 106496 and manifest["VDP2_reserved_bytes"] == 434176
    assert all(manifest[f"{chip}_delta_bytes"] == 0 for chip in ("VDP1", "VDP2", "SCSP"))
    assert manifest["background_heap_bytes"] < manifest["heap_capacity_bytes"]
    link_map = (ROOT / "build/game.map").read_text()
    end = int(re.search(r"0x([0-9a-f]+)\s+__bend =", link_map)[1], 16)
    assert end < 0x060c0000, hex(end)
    print("PASS exact starting storefront and roadway pixels, opaque HQ facades, protected source delta, disc assets and graphics budgets")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--medium-guitar", action="store_true")
    parser.add_argument("--mix-pass1", action="store_true")
    args = parser.parse_args()
    validate(args.medium_guitar, args.mix_pass1)
