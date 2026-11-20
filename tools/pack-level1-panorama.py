#!/usr/bin/env python3
"""Repack an indexed Level 1 panorama with the Saturn's existing block codec."""
import argparse
import hashlib
import heapq
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

BLOCK_BYTES = 512
TILE_BYTES = 64
LOW_WORK_LIMIT = 0x80000
PACK_STAGING_BYTES = 65536
ROOT = Path(__file__).resolve().parents[1]


def tokens(block):
    """Find exact local LZ matches with the existing nine-bit distance."""
    positions = defaultdict(list)
    cursor = 0
    while cursor < len(block):
        best_length, distance = 0, 0
        for previous in reversed(positions[block[cursor:cursor + 3]]):
            length = 3
            while length < min(66, len(block) - cursor) and block[previous + length] == block[cursor + length]:
                length += 1
            if length > best_length:
                best_length, distance = length, cursor - previous - 1
            if length == 66:
                break
        limit = cursor + (best_length or 1)
        yield (256 + best_length - 3, distance) if best_length else (block[cursor], None)
        for i in range(cursor, limit):
            positions[block[i:i + 3]].append(i)
        cursor = limit


def huffman(blocks):
    frequencies = Counter(s for block in blocks for s, _ in block)
    tree = [(n, s, s) for s, n in sorted(frequencies.items())]
    heapq.heapify(tree)
    # The decoder's leaf and branch tie order is deterministic.
    serial = 320
    while len(tree) > 1:
        a, b = heapq.heappop(tree), heapq.heappop(tree)
        heapq.heappush(tree, (a[0] + b[0], serial, (a[2], b[2])))
        serial += 1
    table, codes = [], {}

    def visit(node, code=0, bits=0):
        if isinstance(node, int):
            codes[node] = (code, bits)
            return -node - 1
        entry = len(table)
        table.append(None)
        table[entry] = (visit(node[0], code * 2, bits + 1),
                        visit(node[1], code * 2 + 1, bits + 1))
        return entry

    assert visit(tree[0][2]) == 0
    return table, codes


def encode(block, codes):
    encoded = bytearray()
    value, bits = 0, 0
    for symbol, distance in block:
        fields = [codes[symbol]]
        if distance is not None:
            fields.append((distance, 9))
        for v, n in fields:
            value = value << n | v
            bits += n
            while bits >= 8:
                bits -= 8
                encoded.append(value >> bits)
                value &= (1 << bits) - 1
    if bits:
        encoded.append(value << (8 - bits))
    return encoded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('indexed', type=Path, help='row-major 8-bit indexed 368-row panorama')
    args = parser.parse_args()
    art = ROOT / 'assets/level1-intersection'
    pixels = np.fromfile(args.indexed, dtype=np.uint8).reshape(368, -1)
    height, width = pixels.shape
    if width < 2560 or width % 128:
        parser.error('the panorama width must be at least 2560 and a multiple of 128')
    render = pixels.copy()
    render[:56, :1280] = 0  # Existing NBG2 opening.
    tile_ids, cells = {}, []
    for first in range(0, width, 128):
        for y in range(0, height, 8):
            for x in range(first, first + 128, 8):
                tile = render[y:y+8, x:x+8].tobytes()
                cells.append(tile_ids.setdefault(tile, len(tile_ids)))

    raw = b''.join(tile_ids)
    blocks = [list(tokens(raw[i:i+BLOCK_BYTES].ljust(BLOCK_BYTES, b'\0')))
              for i in range(0, len(raw), BLOCK_BYTES)]
    table, codes = huffman(blocks)
    packed, offsets = bytearray(), []
    for block in blocks:
        offsets.append(len(packed))
        packed.extend(encode(block, codes))
    offsets.append(len(packed))
    payload = len(packed)
    packed.extend(bytes(-payload % 4))
    if len(packed) > LOW_WORK_LIMIT:
        parser.error(f'{len(packed)} packed bytes exceed the low work RAM budget')
    if len(tile_ids) >= 32768:
        parser.error('tile IDs exceed the renderer signed-short slot tables')

    files = {'IXPIX.BIN': pixels.tobytes(), 'IXPACK.BIN': bytes(packed),
             'IXOFF.BIN': struct.pack(f'>{len(offsets)}I', *offsets),
             'IXMAP.BIN': struct.pack(f'>{len(cells)}H', *cells)}
    decode_heap = 128 * 512 + len(blocks) * 4 + (len(blocks) + 7) // 8
    map_heap = len(files['IXMAP.BIN']) + len(files['IXOFF.BIN']) + 8
    manifest = json.loads((art / 'manifest.json').read_text())
    blank = tile_ids[bytes(TILE_BYTES)]
    manifest.update(
        width=width, height=height, tile_count=len(tile_ids),
        new_tiles=len(tile_ids)-manifest['retained_original_visible_tiles'],
        raw_source_bytes=len(raw), packed_source_bytes=len(packed), packed_data_bytes=payload,
        offset_bytes=len(files['IXOFF.BIN']), huffman_nodes=len(table),
        huffman_max_bits=max(n for _, n in codes.values()), block_count=len(blocks),
        blank_tile=blank, chunk_bytes=len(files['IXMAP.BIN']), decode_cache_heap_bytes=decode_heap,
        map_offset_heap_bytes=map_heap, background_heap_bytes=map_heap+decode_heap,
        packed_low_work_ram_bytes=len(packed), peak_cd_staging_heap_bytes=min(len(packed), PACK_STAGING_BYTES)+4,
        sha256={name:hashlib.sha256(data).hexdigest() for name,data in files.items()},
    )
    header = f"""#ifndef MF_INTERSECTION_DATA_H
#define MF_INTERSECTION_DATA_H
#define MF_INTERSECTION_TILES {len(tile_ids)}u
#define MF_INTERSECTION_PACK_BYTES {len(packed)}u
#define MF_INTERSECTION_PACK_DATA_BYTES {payload}u
#define MF_INTERSECTION_OFFSET_BYTES {len(files['IXOFF.BIN'])}u
#define MF_INTERSECTION_BLOCKS {len(blocks)}u
#define MF_INTERSECTION_BLANK {blank}u
#define MF_INTERSECTION_MAP_BYTES {len(files['IXMAP.BIN'])}u
#define MF_INTERSECTION_CACHE_TILES {manifest['resident_tiles']}u
#define MF_INTERSECTION_WIDTH {width}
#define MF_INTERSECTION_ROWS {height//8}
#define MF_INTERSECTION_HUFF_NODES {len(table)}u
static const short mf_intersection_huffman[MF_INTERSECTION_HUFF_NODES][2]={{{','.join('{%d,%d}' % p for p in table)}}};
#endif
"""
    for name, data in files.items():
        (art / name).write_bytes(data)
    (art / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (ROOT / 'src/intersection_data.h').write_text(header)
    print(f'{len(tile_ids)} source cells, {len(packed)} packed bytes, {map_heap + decode_heap} retained heap bytes')


if __name__ == '__main__':
    main()
