# HQ jump anatomy refinement

Branch: `hq-jump-anatomy-fix`. Baseline: `8c339aca6cefffeb9d15679d97bb8a26ffd262de` (`hq-jump-animation-test`). No merges.

## Recovery and scope

The interrupted task left six edited lower-body source PNGs, indexed textures, packing code, native comparisons, diagnostic joint overlays, and a successful native build/test run. These were preserved and completed rather than regenerated. Untouched baseline sources and rendered poses are archived in `assets/hq-jump-anatomy/before/`; SHA locks cover unrelated source, artwork and audio.

The kick now has a longer, connected thigh/shin chain and full-size boot; the tuck separates the folded legs and boots; descent opens the knees and aligns the ankles toward the approved landing stance. Existing head and upper-body pieces are retained. Only Buck/Chuck lower poses 1 (tuck), 2 (descent), and 3 (kick) were edited. A targeted image-edit guide was used for lower-leg reconstruction, followed by native pixel cleanup and mapping into the existing indexed palette. No whole-character scaling or regeneration is used in game.

The root is still (64,92) on the 128×96 native canvas. The review canvas adds 16 pixels above it. Inspection found the original root/scale correct; lower anatomy and the overlap at rows 44–49 caused the perceived disconnection. The pelvis registration and texture crop offsets were checked; no world anchor, upper-body scale, phase selection or physics changes were necessary. Descent shin/ankle editing is localized below the knee, not a whole-leg translation. The first airborne/ascent pose, takeoff, guard and landing are pixel-identical to the baseline. HJ00/01/05/06 are byte-identical.

The earlier screenshot references were unavailable as attachments; the described issues were matched to the assembled baseline kick, tuck and descent. Visual approval remains with the user.

## Packing and memory

| Allocation | Baseline | Refined |
|---|---:|---:|
| VDP1 texture pool capacity | 458,488 | 458,488 |
| Resident texture bytes | 456,224 | 457,888 |
| Free bytes | 2,264 | 600 |
| Jo/SGL texture definitions | 250/255 | 254/255 |
| Jump bank bytes | 24,608 | 26,272 |

The increase is **1,664 bytes**. There are 240 resident payloads and 14 existing zero-payload crop views, totaling 254 definitions. Four tightly cropped second bands split the kick/descent rectangles; they are texture pieces, not additional animation frames. Existing primary resource IDs are preserved and HJ10–13 are appended. Crops use 8-pixel width alignment, binary transparent index zero, the exact existing shared palette, and mirrored native offsets. No additional palette bank, streaming, runtime CD reads, or removal of approved resident assets. The runtime reads Jo's actual allocation counters and confirms these totals. A final ankle refinement changed an interim estimate of 632 free bytes to the final **600**. This is extremely tight and leaves only one definition; further art work needs a separate memory plan.

## Previews

`assets/hq-jump-anatomy/` includes native and nearest-neighbor 4× before/after kick, tuck and descent comparisons for both fighters. Cyan/yellow projected hip/knee/ankle annotations and orange seam markers are development-only artist annotations, not anatomical measurement or game assets. They are never included in the CD texture bank.

`docs/hq-jump-anatomy-captures/` contains real input-driven Yabause captures and side-by-side baseline/refined full-jump and jump→kick→landing GIFs at 1× and 4×. Baseline captures remain untouched in `docs/hq-jump-captures/`. These sequences originate from the emulator frontend's button inputs; no emulated RAM writes drive the animations.

## Validation

Native build, `make check`, `make test`, indexed texture/palette validation, immutable-source checks and sprite-bank mock tests passed. The native Yabause libretro jump scenario verifies 705 identical baseline gameplay states, 760,492 matching rendered native pixels across both actors/all six phases/both directions, stable texture VRAM, and actual allocation counters. Both flights last 42 simulation ticks; peak height remains 16,170/256 pixels and landing counts 6→0. The legacy aerial-bat assembly matches 1,099,577 baseline pixels.

The rendered kick and descent may use one extra draw command per fighter. There is no new gameplay state, cache or texture upload in the draw path. Jab, bat, dash, torch and audio sources remain SHA-identical to the baseline; regression runtime results are supplied as JSON beside the captures.

## Limitations

This is native Yabause libretro validation, not WebRetro or physical Saturn testing. No hardware performance or audio audition claim. Pixel checks mask crowd occlusion and list coverage explicitly. Native 88px art cannot show every anatomical detail; the farther leg can overlap the pelvis, but both chains are distinct in the review poses. Aerial bat intentionally retains its approved legacy complete assembly. The approved landing pose is unchanged; only the incoming descent stance is revised. User visual review is required before treating the artwork as approved.

Additional native Yabause regressions passed: torch 705 identical gameplay states / 297,853 matching pixels; input-driven repeated jabs 143,755 matching pixels with no automatic held-button repetition; combat 705 identical states / 238,570 matching pixels, including 24 momentum-slide deltas, 81 stationary swing checks and 187 dash velocity checks. All report stable texture memory. Music source and binary preservation checks passed; sound RAM high water remains 296,416/524,288 bytes.
