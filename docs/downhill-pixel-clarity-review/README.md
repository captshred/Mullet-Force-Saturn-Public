# Downhill pixel-art restoration · Stage 1

The starting point is the approved geometry build, `fcaa71db7f587a88cb458149aec8aebfd22d089f`.

## Import audit

The original 1764 × 892 HQ source matches the SHA-256 in the approved manifest. Its sign lettering, window muntins, and concrete highlights have sharper color transitions than the Saturn panorama, although many details are smaller than a native pixel after reduction. The original conversion first Gaussian-prefiltered the source (σ 0.8 vertically and 0.65 horizontally), then bilinearly sampled each façade in curb-relative coordinates. Each resulting pixel could therefore contain several source colors. A small local contrast adjustment followed, then a rounded RGB lookup and weighted nearest match to the allowed entries of the existing RGB555 palette. Both spatial blending and the smaller palette can mute or merge fine adjacent highlights. Phase 3C translated indexed rows by whole pixels and introduced no further filtering.

The panorama is packed as exact 8 × 8 indexed tiles using a 512-byte block codec. Neither tile deduplication nor compression averages colors. The street is rendered on VDP2 NBG1 at 1× with integer pixel positions. Native Yabause screenshots from the approved build already show the softer details seen in the indexed art. This establishes baked softness in still frames. Motion shimmer and any filtering at display scale require separate runtime observation.

## Review images

- [Native façade comparisons](01-native-facades.png)
- [Fine details at 3× nearest-neighbor enlargement](02-detail-3x.png)
- [Wide native comparison](03-wide-native.png)

Both experiments use the approved geometry's sampling coordinates and the existing RGB555 palette. The footprint version picks one actual source pixel near the median of a 3 × 3 source footprint. The nearest version picks the source pixel closest to the mapped point. Neither blends output colors. Both restrict changes to façade interiors, protect strong existing boundaries, and require neighboring support for a tonal change. Rooflines, the transparency mask, the road, sidewalks, curbs, ramp, and markings were checked against the approved bytes.

I recommend the footprint version. It recovers some sign, window and garage detail while avoiding the harsher brick and concrete speckling of the nearest version. The difference is modest at native size. Some thin highlights and lettering remain limited by the Saturn sampling grid and palette.

| Proposal | Changed pixels | Changed 8 × 8 tile positions | Total unique indexed tiles |
| --- | ---: | ---: | ---: |
| Footprint representative | 5,529 | 981 | 7,797 |
| Nearest source pixel | 8,470 | 1,099 | 7,797 |

The approved panorama also has 7,797 unique tiles. Both proposals have the same 499,008 bytes of unique uncompressed tile data. The estimated VDP2 reservation stays at 434,176 bytes with the existing 106,496-byte resident street-cell region. Packed byte size, per-scroll uploads, and motion stability remain to be measured after approval.

Black above the roofs represents transparent skyline pixels in these isolated street-layer previews. The separate `IXPIX-footprint.BIN` and `IXPIX-nearest.BIN` files are 2560 × 368 row-major indexed review copies. The runtime assets, palette, and renderer remain at the approved revision. No playable build was generated for this review.
