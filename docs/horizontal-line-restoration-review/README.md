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

## Expanded visual review

This proposal includes the first garage proof and extends it across both garage wings and the neighboring downhill storefronts. The comparison sheets use the approved geometry build on the left.

- [F. Full downhill comparison at native resolution](F-full-downhill-native.png)
- [G. Both garage wings, upper decks, rails, and parked cars at 4×](G-garage-upper-decks-and-cars-4x.png)
- [H. AUTO SERVICE, MOTOR PARTS, and COIN LAUNDRY at 4×](H-storefront-details-4x.png)
- [I. Full change map at 2×](I-full-change-map-2x.png)

The expanded garage edits align upper deck cap highlights and selected railing runs, including the lower right deck. They straighten short roof, hood, shoulder, and bumper highlights on the five parked vehicles. Each car retains its original roof profile, sloping windshield and hood contours, proportions, and shading. The storefront pass levels sign-border highlights at AUTO SERVICE and COIN LAUNDRY and repairs small discontinuities on a MOTOR PARTS window header and sill. Existing letterforms, structural posts, reflected light, and decorative texture remain in place.

The workflow uses explicit pixel-run selections and swaps existing palette indices between adjacent rows. The full proposal, `IXPIX-full-proposed.BIN`, changes **1,062 pixels** from the approved art, including the original 392-pixel proof. The additional 670 changes comprise 356 garage architecture pixels, 114 parked-car pixels, and 200 storefront pixels. The changes touch 218 tile positions and preserve the 7,797 unique indexed tiles. The estimated VDP2 reservation remains 434,176 bytes. The full transparency mask, all columns left of the downhill edit, and the protected roadway region are pixel-identical to the approved art.

This deliverable is for visual review. In-game scrolling and hardware behavior have yet to be tested.
