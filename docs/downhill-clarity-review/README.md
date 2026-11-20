# Downhill background clarity · Stage 1

The approved baseline is [732fbf3ddeef383fcb80ddfddd4b977afe9ab2b2](https://github.com/captshred/Mullet-Force-Saturn-Public/commit/732fbf3ddeef383fcb80ddfddd4b977afe9ab2b2), resolved from `the-one-vehicle-ambush-definitive`.

- [Coin Laundry and PARKING](01-laundry-parking-native.png)
- [AUTO SERVICE and the downhill transition](02-auto-service-native.png)
- [Wide downhill composite](03-downhill-composite-native.png)
- [Original source excerpts and approved native Yabause captures](04-source-runtime-evidence.png)

The three before-and-after sheets use matching 1:1 pixel dimensions and the existing RGB555 palette. Black above the roofline represents transparent index 0 in these isolated street-layer previews. In the approved game the skyline sits behind that layer.

## Findings

The HQ authoring art shows horizontal sign bands and garage beams alongside a sloping curb. The downhill import applies a curb-following vertical offset to each column, including the architecture. The indexed panorama has stair steps on nominally horizontal roof and trim edges, and the approved 320 × 240 Yabause captures reproduce that pattern. The authoring-to-native conversion also prefilters and resamples the image before palette conversion, accounting for some baked softness.

`src/street.c` draws the street as 8 × 8 indexed cells on VDP2 NBG1 at 1× scale with integer scroll positions on both axes. The fractional quarter-speed scroll in `src/parallax.c` applies to the separate NBG2 skyline. VDP1 does not transform the street. The evidence isolates baked steps and softness without measuring how much motion shimmer comes from individual pixel motion or display interpolation.

## Proposal

Five façade spans use integer row shifts of up to four pixels across the upper walls. This levels the roof edges and reduces the staircase along bands and window frames while keeping existing vertical jambs, colors and architectural details. The correction tapers within the lower walls above the sloping sidewalks and garage driveway. Intentional depth cues and small native-resolution diagonal details remain. The proposal retains the palette and the existing fine texture, including any softness already present in individual details.

`IXPIX-proposed.BIN` is a separate row-major 2560 × 368 indexed review asset. Comparing it with the approved panorama shows 41,890 changed pixels. All columns left of world X 1928 are byte-identical, as is the part of each changed column from 11 pixels above the original road reference downward. Every revised façade remains opaque below its roof in the edited region. The road, curbs, ramp, markings and pavement retain their original pixels.

Expected VDP1 change is 0 bytes, with the 49,152-byte hero reserve intact. The proposal has the same raw indexed dimensions and palette as the original. Packed tile use and runtime motion will be measured after approval. This branch contains review artwork only. No build or CI run was requested during Stage 1.
