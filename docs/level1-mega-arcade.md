# Level 1 Phase 4A · MEGA ARCADE geometry playtest

Baseline `the-one-downhill-clarity-definitive` resolves to
`dce0d49cbba8da61b90df7b42ed446d47a54c41a`. Every approved indexed panorama
pixel through world X 2559 is retained. The art after that point is a temporary
layout for a garage, arcade and tree-lined lot.

| Geometry | Range |
| --- | --- |
| World art | X 0–3327, Y 0–367 |
| Player centers, subject to the normal camera tether | X 26–3302 |
| Camera origin | X 0–3008 |
| Original slope | X 1920–2560 |
| Flat transition and garage | X 2560–2687 |
| Future arena footprint | X 2688–3327 (640 px, two screens) |
| Arena combat lanes | Y 168–229 in simulation (296–357 in the panorama) |

The flat lot holds the last downhill drop of 128 pixels. The approved camera
uses the same leading-edge Y calculation, horizontal follow, co-op tether,
and backstop. Actors can traverse and backtrack freely. Garage decks, the
marquee and entrance, and the right-side trees are painted into the existing
NBG1 panorama. Vehicles sit behind the combat lanes; the entrance recess has
no collision or interaction. The wide façade is revealed across neighboring
camera positions. The extension uses an opaque sky backdrop behind its
silhouettes on the same layer, with no additional moon or parallax layer.

The engine keeps its 1,664 resident street cells and existing tile-map ring.
The generated placeholder layout uses the existing palette and exact 8 × 8
tile deduplication, with 9,627 unique source tiles. The pack uses 370,048
bytes of the 524,288-byte low-work-RAM slot, leaving 154,240 bytes there.
The peak transient staging request is 370,052 bytes in the configured
393,216-byte heap. The retained background request is 113,603 bytes.
VDP1 texture use is 386,432 bytes and the 49,152-byte reserve is intact.
VDP2 reservation remains 434,176 bytes. The audio budget is unchanged.

To regenerate the placeholder layout, run
`python3 tools/prepare-mega-arcade.py --output /tmp/mega-panorama.bin` and
`python3 tools/pack-level1-panorama.py /tmp/mega-panorama.bin`. The packer
accepts a row-major 8-bit panorama using the existing Level 1 palette.
Future approved art can replace the rightmost 768 columns using this tool
without changing stage or camera coordinates. The current pack must fit the
staging allocation, which is the tighter limit than the low-work-RAM slot.
