# Corrected streetlamp poles — visual approval pending

Branch: `art/level1-background-touchups`.
Correction parent: `e23b9bceb8543e6316637b7fb8bd66d25241f377`.
The previous cleanup removed the wrong upper support at both lamps. Both new
user gameplay screenshots identify the same distinction: **LEFT is the actual
streetlamp pole; RIGHT is an unwanted extra strip**.

## Full-height before/after previews

- [VINYL native gameplay screenshot comparison, complete lamp, 6×](native-vinyl-lamp-before-after.png).
- [MULLET FORCE native gameplay screenshot comparison, complete lamp, 6×](native-mullet-lamp-before-after.png).
- [VINYL unobstructed background comparison, 6×](vinyl-post-before-after.png).
- [MULLET FORCE lamp: sidewalk to lamp head, 6×](mullet-post-before-after.png).
- [Full background before/after](full-before-after.png).
- [ION ARCADE comparison — sign unchanged by this correction](ion-arcade-before-after.png).
- [Current repair regions](repair-regions.png).
- Native production Yabause: [left lamp](native-left-view.png),
  [ION/VINYL view](native-ion-vinyl-view.png), [verification report](native-report.json).

The BEFORE side is the previous incorrect cleanup, not the older intact source.
The gameplay comparisons are matched Yabause captures at cameras 0 and 261,
from separately built production discs for e23b9bc and the correction. Both
complete poles are unobstructed. No supplied gameplay screenshot was painted.
These unobstructed native-background enlargements show the complete poles;
foreground players/UI in gameplay captures can obscure their bases.

Visual checks performed before committing:

1. Each lamp has exactly one continuous dark-metal support from its sidewalk
   base up to the original curved bracket and illuminated head.
2. The surviving support is the LEFT one, restored byte-for-byte from the
   original artwork, with its original width, shading and highlights.
3. The RIGHT blue/gray core is removed along its full height to the sidewalk.
4. Its replacement is actual nearby indexed wall/mortar, storefront-shadow and
   sidewalk texture sampled at the same source row, not a flat fill.
5. The complete repaired ION ARCADE sign is byte-identical to `e23b9bc`.
   The MULLET FORCE/VINYL signs, lamp heads, glow and all other background pixels
   outside the tightly defined correction regions are also unchanged.

## Native source and precise scope

The source remains `assets/city-cleanup/CIPIX.BIN`. The indexed correction starts
from the unmodified original background under
[`art/level1-background-touchups/original`](../../art/level1-background-touchups/original/),
replays the existing ION repair exactly, and leaves the actual left supports intact.
Only the separate right strips are removed:

| Location | Restored/kept LEFT support, complete reference box | Removed RIGHT strip |
|---|---|---|
| MULLET FORCE | x 151–158, y 61–157 | x 160–164, y 74–153 |
| VINYL | x 519–526, y 61–157 | x 528–532, y 74–153 |

Coordinates refer to the native 640×240 source. The former right strips receive
pixels from 14 columns to their left at the same Y, matching brick courses and
sidewalk rows. The source sample regions contain no metal pole. Neither the real
left supports nor the sign boundaries overlap the removal masks.

`pole-correction-before.bin` preserves the exact incorrect cleanup for review.
Provenance records both that SHA and the original recovery assets. Validation
requires the full left-support boxes to match the intact original, the former
right-strip pixels to match the selected environment samples, and every pixel
outside these correction regions to match the previous cleanup. It also locks
the entire repaired ION, MULLET FORCE and VINYL sign rectangles.

The preparation and packing commands remain:

```sh
python3 tools/prepare-level1-background-touchups.py
python3 tools/preview-level1-background-touchups.py
bash tools/build-stage.sh --native
make check
```

## Validation and memory

Actual unique tiles remain **1,664**, occupying **106,496 cell bytes**. Facade map
(16,384 bytes), chunk table (4,800 bytes), palette (510 bytes), skyline assets and
memory-budget headers are unchanged. Additional VDP1, VDP2 and CRAM allocation:
**0 bytes**. Runtime gameplay/AI, Ricky's approved tattoo, audio and Level 2 are
byte-identical to the approved parent source.

Background validation checks native indexed masks, restored left supports,
removed right strips, untouched signs, all packed cells/maps, every packaged disc
file and the executable source fingerprint. Historical preservation/automated
suites remain unmodified on their approved parent snapshot. Production Yabause
checks use only normal controller input and read-only snapshots: camera 0/320,
exact loaded background/sky payloads, changing neon phases, asset error 0.

The new previews are an approval candidate. Nothing is merged and no THE ONE tag
moves. Final subjective visual approval remains with the user.

## Manual Saturn playtest build

Workflow: **Manual Saturn playtest build** (`.github/workflows/build.yml`).
Use workflow from: **art/level1-background-touchups**.
Profile: **stage-default**.
`source_ref`: the full correction commit SHA in the delivery report.
Keep the matching BIN/CUE pair from `mullet-force-stage-default-<full SHA>` together.
Artifact retention is one day.
