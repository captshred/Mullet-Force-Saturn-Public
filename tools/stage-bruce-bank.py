#!/usr/bin/env python3
"""Verify the approved Bruce textures and stage the dedicated CD suffix."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys

root = Path(__file__).resolve().parents[1]
art = root / "assets/bruce"
out = Path(sys.argv[1])
frames = []
for clip in ("idle", "walk", "punch", "charge", "slam", "hit-stun", "fall"):
    manifest = json.loads((art / clip / "manifest.json").read_text())
    for frame in manifest["frames"]:
        frames.append((art / clip / frame["texture"], frame))

boot = json.loads((art / "charge/manifest.json").read_text())["shared_boot_view"]
assert boot == json.loads((art / "punch/manifest.json").read_text())["shared_boot_view"]
palette = (art / "idle/BR00.TGA").read_bytes()[18:786]
textures = {}
names = set()
for path, frame in frames:
    data = path.read_bytes()
    width, height = struct.unpack_from("<HH", data, 12)
    assert (width, height) == (frame["width"], frame["height"]) and width % 8 == 0
    assert data[:3] == bytes((0, 1, 1)) and data[16:18] == bytes((8, 32))
    assert data[18:786] == palette and len(data) == 786 + width * height
    pixels = data[786:]
    assert 0 in pixels and 255 not in pixels
    decoded = bytes(index + 1 if index else 0 for index in pixels)
    assert hashlib.sha256(decoded).hexdigest() == frame["decoded_sha256"]
    assert frame["bytes"] == (width * height + 31) & ~31
    assert frame["anchor"] == [64 - frame["bounds"][0], 112 - frame["bounds"][1]]
    assert path.name not in names
    names.add(path.name)
    textures[(width, height, pixels)] = (path, frame)

size = sum((w * h + 31) & ~31 for w, h, _ in textures)
assert len(textures) == len(frames) == 19 and size == 162240
assert size + 239360 + 49152 <= 458488
assert [(p.name) for p, _ in frames[:5]] == [
    "BR00.TGA", "BR02.TGA", "BW00.TGA", "BW01.TGA", "BW02.TGA",
]
folder = out / "cd/BRUCE"
folder.mkdir(parents=True, exist_ok=True)
lines = [f"#define BRUCE_BYTES {size}u", f"#define BRUCE_DEFS {len(textures)}",
         f'#define BRUCE_BOOT_WIDTH {boot["width"]}', f'#define BRUCE_BOOT_HEIGHT {boot["height"]}',
         f'#define BRUCE_BOOT_OFFSET {boot["byte_offset"]}',
         f'#define BRUCE_BOOT_X {boot["anchor"][0]}', f'#define BRUCE_BOOT_Y {boot["anchor"][1]}',
         "static const bruce_frame bruce_frames[BRUCE_DEFS] = {"]
for path, frame in textures.values():
    shutil.copyfile(path, folder / path.name)
    x, y = frame["anchor"]
    shared = int(bool(frame.get("shared_boot_view") or frame.get("shared_views")))
    lines.append(f'    {{"{path.name}", {frame["width"]}, {frame["height"]}, {x}, {y}, {shared}}},')
lines += ["};", "static const unsigned short bruce_colors[255] = {"]
for start in range(0, 255, 12):
    row = []
    for i in range(start, min(start + 12, 255)):
        b, g, r = palette[i * 3:i * 3 + 3]
        row.append(f"0x{0x8000 | (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10):04x}")
    lines.append("    " + ", ".join(row) + ",")
lines.append("};")
(out / "bruce_bank_data.h").write_text("\n".join(lines) + "\n")
