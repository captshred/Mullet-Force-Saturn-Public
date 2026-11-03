# Buck and Chuck running waist cohesion

Branch `player-run-waist-seam-fix`, based on validated denim-cleanup commit `3f26c763306e3f231fbaf52870fe9b6a301134dc`. No merges or protected-branch changes.

## Diagnosis: C19 / C21 are poses, not texture IDs

`src/main.c` prints `HIGH DETAIL MOVEMENT B%02d C%02d` using `mf_player_animation_pose()`. The gallery uses the same numbering. Running poses are 18–21; C19/C21 are Chuck's second/fourth running poses (indices 1/3), with B19/B21 the corresponding Buck poses. They are not filenames CA19/CA21 or resident texture numbers.

Every running frame uses three registered pieces at a fixed (64,92) root. The first cut is y28; the lower cut is y66 in the folded poses or y72 in contact poses. The waist at y42–44 lies INSIDE the middle texture, not at either runtime piece boundary. Both gameplay and gallery use the same resident IDs and offsets, with ordinary hardware mirroring. There is no frame-specific extra offset, overlay or layering error at the waist.

The visible separation was a baked shading/cap discontinuity near y44, where historical run construction combined an approved upper body with the new leg layer. Alpha was already connected; this was not an empty VDP1 allocation or a missing texture row. Moving an entire piece would also move approved legs and clothing and misalign the bat hand.

## Surgical repair

| Fighter | Pose 1 | Pose 2 / 19 | Pose 3 | Pose 4 / 21 |
|---|---:|---:|---:|---:|
| Buck changed native pixels | 0 | 27 | 0 | 40 |
| Chuck changed native pixels | 0 | 23 | 0 | 14 |

Total **104 pixels**, all within x57–78 / y42–44. Use each pose's own existing black-shirt/belt and upper-trouser palette pixels to replace the flat cap/dark divider with a continuous, tapered waistband. Buck's second and fourth poses use different belt rows; his fourth pose also loses five excess cap pixels beyond the natural waist contour. Chuck's fourth pose needs only the divider below the approved denim repair filled; his second pose also needs the belt-to-trouser shading restored.

Every pixel above y42 and below y44 is unchanged. Thus head, hair, face, clothing above the waist, arms, bat grips and leg anatomy below the waistband retain their exact pixels and positions. Frame bounds, roots, piece coordinates, timing, definitions and hardware mirroring are unchanged. Only five excess waist-cap alpha pixels are removed; no character translation or scaling occurs. Original source banks remain immutable. New derivatives are under `assets/run-waist-seam/`.

All **68 pixels of the previous Chuck denim cleanup remain pixel-identical**, including the shoulder and repaired frame-4 beltline. The first and third poses remain byte-for-byte identical in native RGBA. No character generation, full-sheet regeneration, animation frames or gameplay edits are involved. All files under `src/` are SHA-256 locked unchanged.

The four corresponding copies of the running upper body used during bat preparation receive the same waist repair. Existing bat-carry hands, weapon textures, windup/strike/recovery mappings, momentum and timing stay unchanged. Eight equal-sized payload replacements: RN04, RN10, RN16, RN22 and COMBAT/CA21, CA27, CA49, CA55. No new resident texture path or upload is introduced.

## Exact memory and build

```
bash tools/build-run-waist-seam.sh --native
# Omit --native for the pinned Docker build.
```

`MF_PLAYER_RUN_WAIST=1` is an isolated disc-payload option requiring the approved denim/hurt/death profile. Disable it and use `build-chuck-denim-cleanup.sh` to reproduce the previous bank. The new files replace existing disc names after the approved banks are copied. The renderer/gameplay C files are untouched.

| Allocation | Before | After | Change |
|---|---:|---:|---:|
| VDP1 used, actual pool 458,488 bytes | 446,304 | 446,304 | 0 |
| Free bytes | 12,184 | 12,184 | 0 |
| Payload textures | 239 | 239 | 0 |
| Existing zero-payload views | 14 | 14 | 0 |
| Definitions, limit 255 | 253 | 253 | 0 |
| Additional palettes | 0 | 0 | 0 |

The supplied 448,672-byte number belongs to the earlier HQ-hurt build before obsolete player death textures were replaced. The latest baseline and new build both measure **446,304** at runtime. VDP2 and sound RAM are unchanged; sound high-water remains 420,000 / 524,288. No texture cache, streaming, per-frame disc reads or duplicate uploads.

## Validation and actual gameplay

Native SH-2 BIN/CUE build, `make check`, `make test`, source locks, exact indexed reconstruction, transparency, mirroring and ISO payload checks pass. All eight replacement TGA headers, palettes, sizes and indices outside their recorded repair masks are identical to their predecessors. Separate tests verify that each crop is exclusively referenced by its intended fighter/run/preparation pose. Historical validators first verify the new disc bytes, then normalize only verified equal-sized substitutions for their existing immutable source-bank checks.

The two controller-only native Yabause scenarios compare with the downloaded previous approved build: the existing two-player combat/dash sequence, plus a same-direction side-by-side run and reversal. No emulated RAM writes, injected damage or game hooks. Both scenarios cover all 16 actor/run-pose/facing combinations, loop boundaries and carry-to-swing transitions. Dash, jab and running-bat traces are identical to control; actual opaque sprite pixels match native expected pieces. All gameplay source/state, speed, combat, hurt/death, Corporate Punk, music and SFX are preserved.

Across the two scenarios: **1,410 identical gameplay snapshots**, **733,443 matching native sprite pixels**, **38,031,883 unchanged pixels outside the authorized character regions**. The scenarios cover 17 and 19 carry-to-swing samples respectively. Runtime counters verify the memory table, unchanged CRAM and stable texture VRAM.

`MF_RUN_WAIST_SIDE_BY_SIDE` exists only in the external development emulator frontend. It supplies real two-pad inputs, starting both players, double-tapping the same direction, reversing and pressing the existing attack button. It is not compiled into the Saturn game and adds no game control or feature.

## Review files and limits

`assets/run-waist-seam/` contains all eight transparent native PNGs, both fighters' native/4× before-after contact sheets and waist close-ups, and native/4× offline running GIFs in both directions. Each frame also has a development diagnostic: red y44 historical art join, orange actual sprite cuts, cyan anatomical pelvis landmark, yellow true engine root (64,92). There is no separate engine pelvis anchor; the cyan point is an explicitly documented review landmark, not a changed runtime offset. Diagnostics are never packed into the game.

`docs/run-waist-captures/` contains actual full-scene side-by-side and combat/run-to-bat GIFs, screenshots of every actor/run-pose/facing combination and comparison JSON. These are real controller-driven emulator captures, unlike the explicitly named offline previews.

Pixel comparisons exclude HUD, screen clipping and genuinely occluding nearer actors/effects. Final aesthetic approval remains visual playtest. Native libretro Yabause HLE/software rendering is tested; WebRetro, physical Saturn, SAROO/optical drive and real-hardware performance are not claimed.
