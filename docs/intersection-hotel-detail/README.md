# Hotel facade and stone arch — approval milestone

**Branch:** `art/level1-intersection-detail-pass`.
**Exact approved starting baseline:** `8d85905eb12421cfe356b994ebab43893680e1b1`.
**Scope:** hotel front facade and stone arch only. Record-store and residential detail work has NOT started. User visual/hardware approval is pending; no merge or THE ONE tag update.

## Review previews

- [Native-size and enlarged hotel before/after](before-after.png)
- [Whole intersection before/after](intersection-before-after.png)
- [Native 640px intersection](intersection-640.png) and [1920px panorama](panorama.png)
- [Clear hotel during native gameplay](hotel-gameplay.png), [Buck/Chuck/Ricky combat](combat-gameplay.png), [endpoint](endpoint.png)
- [Short native hotel combat capture](hotel-gameplay.gif)

The first art checkpoint was pushed as `88a6ea9`; validation wiring was pushed separately as `a1a9282`. This delivery adds the test evidence and previews, retaining the same runtime/art payloads. Native captures use the first checkpoint's art/code with identical final runtime files. Development milestones are committed and pushed so work can be recovered independently of this conversation.

## What changed

The underlying native indexed material pixels were replaced, rather than decorating the old enlarged clusters with extra lines. The hotel now has staggered small brick courses, small mortar highlights, separate radial arch stones with bevel/pitting/chips, finer pier blocks, recessed door panels/mullions/brass pulls and amber glass reflections, and slimmer window sashes/curtains. The untouched approved mini-mall storefronts supplied the pixel-detail/style reference.

The authoring crop is 120×152 native pixels. A strict inset mask limits edits to new-intersection x418–533, y0–150 (world x1698–1813). The outer plane boundaries, bottom threshold/sidewalk and adjacent buildings stay frozen. Within that mask **15,918 native pixels** change; **zero** pixels change outside it. This preserves the approved architectural footprint and door/arch scale, and all intersection perspective geometry. The original vertical HOTEL neon on the side plane is untouched. Review the images for final art judgment; finer pixel density alone is not a quality approval.

A diagnostic on overlapping 2×2 samples changes from 34.0% uniform-color samples to 2.3%, consistent with replacing the coarse repeated clusters. It is supplementary evidence only; [native-clusters.json](native-clusters.json) records it. No new palette colors are installed: the rebuilt pixels use existing static RGB555 entries. Every shared palette byte and all animated-neon pixels outside the hotel mask remain exact. Edited foreground pixels remain opaque and avoid animated indices.

`art/intersection-hotel-detail/hotel-native-study.png` is the saved native authoring input. `before.bin`, `mask.bin` and `proof.json` provide the exact baseline/recovery and edit boundary. `tools/apply-hotel-detail.py` maps only the masked source pixels to the unchanged palette. `tools/prepare-hotel-detail.py` runs the existing lossless block512/LZ512/Huffman packing pipeline, directing new previews here so historical approved previews stay frozen. No runtime overlay is involved. The high-resolution image-generation study is not required by conversion or native builds.

## Memory and preservation

| Resource | Approved baseline | Hotel milestone | Delta |
|---|---:|---:|---:|
| Source tiles | 5,362 | 5,362 | 0 |
| Packed CPU art payload | 200,416 B | 207,300 B | +6,884 B |
| Static source/tables estimate | 234,823 B | 241,703 B | +6,880 B |
| CPU decode-cache payload | 68,304 B | 68,304 B | 0 |
| VDP2 resident tiles / cell bytes | 1,664 / 106,496 B | same | 0 |
| VDP2 ring / total reserved | 16,384 / 434,176 B | same | 0 |
| VDP1 definitions / texture bytes | 177 / 371,072 B | same | 0 |
| Protected Buck/Chuck VDP1 reserve | 49,152 B | same | 0 |
| Palette-bank allocation | Existing banks | same | 0 |
| SCSP high-water / free | 485,812 / 38,476 B | same | 0 |

The finer materials increase compressed CPU payload, not video or audio memory. The tested native linked image ends at `0x060e4844`, below the pinned SGL's actual vertex-work address `0x060e5784`, leaving **3,904 bytes**. Validation reads that linked SDK address and rejects overlap. No heap-capacity, sprite dimensions, decoder architecture, SDK/compiler pin, audio allocation or protected reserve change was made. [Validation/memory record](validation.json) · [compiled sprite audit](sprite-memory.csv).

All existing runtime `.c` files and gameplay/configuration headers are byte-identical to exact `8d85905`; only generated background data metadata changes. All original assets except the localized hotel/derived background packs remain byte-identical. This includes the older 1280px mini-mall/neon strip, record store, residential buildings, receding road/vanishing point, sky, lamps, crosswalk and street. World width stays 1920, checkpoints stay 0/320/640/960/1280, and controls, co-op population, AI, Ricky jump-chain, combat, stage progression, audio and Level 2 are unchanged.

## Validation

**PASS:** native stage-default, make check, make test, deterministic native conversion/packing, hotel-only scope and opacity/palette guards. Existing full cache/Huffman corruption tests, every-camera scrolling in both directions, ring-wrap/previous-scan-out protections, UBSan combat/world/co-op/Ricky/bat/flame/charge/jump-cancel/renderer regressions and Fire/Hit resource audits pass.

[Native traversal](native-traversal.json) reaches camera1600, returns to checkpoint1280, uses the original 68,304-byte cache (68,312-byte allocator block), and records zero asset/parallax errors with three live enemy slots. The normal-input combat capture includes Buck, Chuck and Ricky; the clear hotel image is frame3412 from the same fresh production run. No RAM writes, NPC forcing, forced healing or save-state loading were used.

[Repeated cold starts and Level 2 skip](cold-starts.json) report no state/image mismatches: 600 Level 1 state samples / 30 images, and 555 aligned Level 2 ticks / 545 images. Background CPU cache retirement is checked at the normal Stage 2 handoff. These are emulator checks, not hardware approval.

## Manual Saturn playtest build

Workflow: **Manual Saturn playtest build** (`.github/workflows/build.yml`). Use workflow from `art/level1-intersection-detail-pass`, profile `stage-default`, and `source_ref` equal to the final full milestone commit SHA reported in chat. Download `mullet-force-stage-default-<resolved SHA>` and keep its matching BIN/CUE together (one-day artifact retention).

**STOP HERE:** hotel approval is required before any record-store, residential or other-building redraw begins.
