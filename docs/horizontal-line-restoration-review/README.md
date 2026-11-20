# PARKING garage horizontal line restoration · Stage 1

This proof of concept starts from the approved geometry build, `fcaa71db7f587a88cb458149aec8aebfd22d089f`. The brief arrived without a separate garage screenshot, so the inspection used the approved indexed panorama and its existing review imagery.

- [A. Approved garage at native resolution](A-original-native.png)
- [B. Structural guide at 4×](B-structural-overlay-4x.png)
- [C. Proposed garage at native resolution](C-corrected-native.png)
- [D. Before and after at 4× nearest-neighbor](D-before-after-4x.png)
- [E. Exact changed pixels at 4×](E-changed-pixels-4x.png)

Cyan marks the intended beam-cap trajectories. Pink marks the exposed rail segments, with a break at the upright. The difference image uses magenta for every changed indexed pixel.

The concrete cap highlights alternated between adjoining pixel rows even where a deck edge should read as level. The proof swaps existing palette indices within hand-selected runs on those edges. It also aligns the two exposed upper-deck rails to the right of the red car. Only rail runs clear of vehicle outlines and posts are edited. The beam caps retain their existing changes in hue, brightness, and material. The rail sections crossing parked cars, perspective edges, and deck joints remain as in the approved art.

| Feature | Native target row | Pixels changed |
| --- | ---: | ---: |
| Left wing cap beneath the silver car | 128 | 100 |
| Left wing cap beneath the blue car | 172 | 30 |
| Right wing cap beneath the red car | 151 | 76 |
| Right wing cap beneath the gold car and van | 200 | 110 |
| Exposed upper rail, right wing | 141 | 40 |
| Exposed lower rail, right wing | 146 | 36 |
| **Total** | | **392** |

The indexed diff is confined to twelve rows within the garage proof area. The transparent-pixel mask is identical across the full panorama. The proposal uses the approved RGB555 palette. The separately saved `IXPIX-garage-proposed.BIN` is a 2560 × 368 row-major indexed review copy.

The 392 changed pixels touch 79 tile positions. Recounting with the runtime mask yields the same 7,797 unique tiles and 499,008 uncompressed tile bytes as the approved build. Estimated VDP2 reservation remains 434,176 bytes with the fixed resident street cache. Compression and scrolling behavior will be measured if the artwork reaches playable integration.
