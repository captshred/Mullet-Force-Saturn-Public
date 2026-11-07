#!/usr/bin/env python3
"""Recolor existing native cells; preserve the audio-fixed executable verbatim.

No SDK rebuild: public source predates the privately compiled audio fixes.
Only three equal-length ISO file extents are replaced. Original assets/locks
remain immutable. The recipe and committed runtime cells are the art source.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import zipfile
from wingsuit_disc import directory_records, SECTOR

R = Path(__file__).resolve().parents[1]
A = R / 'assets/level2-neon-city'
BASE_ZIP_SHA = '997bb4b47131a8c4c74c714cd6472eb1dacb9c5f3e6060d85e3041c56facaf6a'
BASE_BIN_SHA = 'a3e3a75834a28a1b6c9e562f54fd5f6ca29e95a6664940f50c34603cbfe0121e'
NAMES = ('WCELL.BIN', 'WROOF.BIN', 'WPAL.BIN')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def generate():
    recipe = json.loads((A / 'recipe.json').read_text())
    reference = (R / recipe['reference']).read_bytes()
    assert sha(reference) == recipe['reference_sha256']
    palette = struct.unpack('>255H', reference)
    result = {'WPAL.BIN': struct.pack('>16H', *(palette[i-1] for i in recipe['level1_palette_entries_1_based']))}
    counts = {}
    for name in NAMES[:2]:
        original = (R / 'assets/wingsuit' / name).read_bytes()
        data = bytearray(original)
        for start in range(0, len(data), 64):
            tile = original[start:start+64]
            for y in range(8):
                row = tile[y*8:y*8+8]
                # Existing horizontal rim clusters only; no isolated pink dots.
                if y >= 4 and b'\x06\x06\x06\x06' in row:
                    for x, value in enumerate(row):
                        if value == 6:
                            data[start+y*8+x] = 9
            # Reuse existing facade windows for occasional warm illumination.
            if tile.count(8) >= 4 and (start // 64) % 3 == 0:
                for i, value in enumerate(tile):
                    if value == 8:
                        data[start+i] = 15
        # Removing the two accent roles reconstructs every original pixel.
        assert bytes({9: 6, 15: 8}.get(v, v) for v in data) == original
        assert len(data) == len(original)
        counts[name] = sum(x != y for x, y in zip(original, data))
        result[name] = bytes(data)
    return result, counts

def level2_records(disc):
    root = dict(directory_records(disc, disc[16*SECTOR+156:16*SECTOR+190]))
    return dict(directory_records(disc, root['ALEVEL2']))

def extent(record):
    return struct.unpack_from('<I', record, 2)[0]*SECTOR, struct.unpack_from('<I', record, 10)[0]

def patch(base, assets):
    assert sha(base) == BASE_BIN_SHA, 'wrong audio baseline'
    records = level2_records(base)
    result = bytearray(base)
    ranges = []
    for name in NAMES:
        offset, size = extent(records[name])
        assert size == len(assets[name]), (name, 'allocation changed')
        assert base[offset:offset+size] == (R/'assets/wingsuit'/name).read_bytes(), (name, 'baseline mismatch')
        result[offset:offset+size] = assets[name]
        ranges.append((offset, offset+size))
    validate_candidate(base, bytes(result), assets)
    return bytes(result), ranges

def validate_candidate(base, result, assets):
    assert sha(base) == BASE_BIN_SHA
    records = level2_records(base)
    ranges = []
    for name in NAMES:
        offset, size = extent(records[name])
        assert result[offset:offset+size] == assets[name], (name, 'wrong candidate payload')
        ranges.append((offset, offset+size))
    # Complete image comparison: includes executable, audio, Level1, every other
    # scene, ISO directories, unused bytes, and even per-sector padding.
    cursor = 0
    for start, end in sorted(ranges):
        assert start >= cursor
        assert result[cursor:start] == base[cursor:start]
        cursor = end
    assert result[cursor:] == base[cursor:]
    assert len(result) == len(base)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', action='store_true', help='Deliberately regenerate candidate native assets')
    parser.add_argument('--out', type=Path, default=R/'build/download')
    args = parser.parse_args()
    assets, counts = generate()
    for name, data in assets.items():
        if args.export:
            (A/name).write_bytes(data)
        assert (A/name).read_bytes() == data, (name, 'candidate differs from recipe')
    archive = R/'downloads/mullet-force-level2-audio-engine-review.zip'
    assert sha(archive.read_bytes()) == BASE_ZIP_SHA
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        contents = {name: z.read(name) for name in z.namelist()}
    for line in contents['SHA256SUMS.txt'].decode().splitlines():
        digest, name = line.split('  ', 1)
        assert sha(contents[name]) == digest
    disc, ranges = patch(contents['mullet-force.bin'], assets)
    contents['mullet-force.bin'] = disc
    baseline_info = contents['BUILD-INFO.txt'].decode()
    contents['BASELINE-BUILD-INFO.txt'] = contents['BUILD-INFO.txt']
    contents['BUILD-INFO.txt'] = (baseline_info.replace(BASE_BIN_SHA, sha(disc)) +
        '\nCandidate: art/level2-neon-city\n'
        'Assembly: equal-length Level 2 background extent substitution; executable preserved.\n'
        f'Audio baseline commit: {json.loads((A/"recipe.json").read_text())["parent"]}\n').encode()
    report = {
        'base_bin_sha256': BASE_BIN_SHA, 'candidate_bin_sha256': sha(disc),
        'changed_files': list(NAMES), 'modified_extents': ranges,
        'all_bytes_outside_background_extents_identical': True,
        'material_pixels_changed_in_cell_bank': counts,
        'ground_tiles': 578, 'raised_tiles': 194, 'tile_delta': 0,
        'palette_entries': 16, 'cram_bytes': 32, 'palette_banks_added': 0,
        'vdp2_background_payload_bytes': 65792, 'vdp2_reservation_bytes': 434176,
        'vdp2_unreserved_bytes': 90112, 'vram_delta_bytes': 0,
        'vdp1_texture_bytes': 33792, 'vdp1_definitions': 28,
        'scsp_high_water_bytes': 447588,
        'validation': 'Native asset/ISO preservation; see separate emulator results if available. Hardware untested.'
    }
    contents['NEON-VALIDATION.json'] = (json.dumps(report, indent=2)+'\n').encode()
    contents['NEON-REVIEW.md'] = (R/'docs/level2-neon-city.md').read_bytes()
    playback = (R/'docs/level2-neon-emulator-results.json').read_bytes()
    assert json.loads(playback)['candidate_bin_sha256'] == sha(disc), 'playback results belong to a different image'
    contents['NEON-EMULATOR-RESULTS.json'] = playback
    contents['SHA256SUMS.txt'] = ''.join(f'{sha(data)}  {name}\n' for name, data in sorted(contents.items()) if name != 'SHA256SUMS.txt').encode()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, data in contents.items():
        (args.out/name).write_bytes(data)
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
