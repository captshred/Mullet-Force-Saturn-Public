# Level 1 Phase 4A · MEGA ARCADE

The art pass starts from the tested Phase 4A geometry source
`24c0cdc0d2d1d1e986ff6d8e9e2273b8a6304362`. The definitive downhill
baseline is `dce0d49cbba8da61b90df7b42ed446d47a54c41a`. Approved panorama
pixels through world X 2559 are retained byte for byte.

## Layout

| Geometry | Range |
| --- | --- |
| World art | X 0–3327, Y 0–367 |
| Player centers, subject to the existing tether | X 26–3302 |
| Camera origin | X 0–3008 |
| Original slope | X 1920–2560 |
| Garage and its transition into the lot | Approximately X 2560–2758 |
| Unobstructed arena floor | X 2688–3327 |
| Entrance center and playable end | Approximately X 3287 and X 3302 |
| Arena combat lanes | Simulation Y 168–229, panorama Y 296–357 |

The garage ends at the left side of the arena view. The trees, skyline and
parked vehicles frame the open lot behind the combat lanes. The camera
scrolls into the full frontage with the entrance behind the rightmost
playable point. The entrance is scenery for this phase. The flat road,
horizontal follow, Y projection, co-op tether and reverse checkpoint use
the existing Phase 4A geometry.

## Indexed art and memory

The approved concept is cropped and mapped by feature across the rightmost
768 columns. The facade uses the final view, while the garage and open lot
receive their own horizontal proportions. The existing RGB555 palette is
used without dithering. The concept moon was removed, and new floor
reflections are subdued toward the foreground for sprite readability.
The art uses ordinary 8 × 8 NBG1 cells with the existing map ring. No
additional layers or VDP1 textures are required.

The 459,488-byte pack fits the 524,288-byte low-work-RAM slot with 64,800
bytes to spare. It is read in sector-aligned chunks using a single
65,540-byte high-work-RAM staging allocation. The compressed format, tile
cache and loader's stage-lifetime ownership are retained. There are no CD
reads during scrolling. The retained background allocation is 114,732
bytes. VDP2 still reserves 434,176 bytes, with 106,496 bytes for resident
street cells. VDP1 still uses 386,432 bytes with the 49,152-byte hero reserve
protected. Audio assets and SCSP allocation are unchanged.

With the approved 2172 × 724 concept PNG available locally, reproduce the
indexed panorama with
`python3 tools/import-mega-arcade-art.py "/path/to/concept.png" --output /tmp/mega-panorama.bin`
and repack it with
`python3 tools/pack-level1-panorama.py /tmp/mega-panorama.bin`.
The authoring source is kept outside the repository.
