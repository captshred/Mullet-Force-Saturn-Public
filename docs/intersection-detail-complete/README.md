# Complete Phase 3A foreground pixel-art candidate

**Baseline:** `89b0332de1bd2c4e84e9f086cd0e078169bd8103`.
**Development branch:** `art/level1-intersection-detail-pass`.
All remaining coarse foreground fronts are redrawn. The approved hotel is unchanged. This is a complete visual-review candidate, not an art/hardware approval. No merge or THE ONE tag update.

## Visual review

1. [Full 640px Phase 3A extension, native resolution](intersection-640.png)
2. [Full 1920px Level 1 panorama](panorama.png)
3. [RECORDS before/after](records-before-after.png)
4. [Residential / balcony / shutter / DELI before/after](residential-before-after.png)
5. [Hotel-to-RECORDS close-up](hotel-to-records.png) and [native gameplay screenshot](native-hotel-records.png)
6. [Equal-scale pixel-detail comparison: original mini-mall, approved hotel, residential and RECORDS](detail-quality-comparison.png)
7. [Entire extension before/after](extension-before-after.png), [old strip boundary](old-strip-transition.png), [DELI/cross-street boundary](deli-to-intersection.png)
8. Native production: [combat](intersection-gameplay.png), [scrolling transition](transition.png), [endpoint](endpoint.png), [checkpoint backstop](checkpoint-backstop.png), [combat animation](intersection-combat.gif).

The new masonry, mortar, shutter slats, balcony rails, recessed panels, window sashes/blinds/reflections, ledges and cornices replace the underlying large clusters. DELI has small shelf/product details; RECORDS has distinct record sleeves/discs and a crisp native bitmap-style sign. The materials use the same static palette and native pixel scale as the hotel and original approved storefronts. Image studies introducing an awning or diagonal stair element were corrected before integration; neither is retained.

The two remaining coarse foreground zones were completed as one project: new-section x2–239 above y151 (excluding the low-wall skyline opening and its outer rim), and x538–639 above y151. That is world x1282–1519 and1818–1919. **45,244 native pixels change, zero outside this mask.** The complete hotel x416–535 / world1696–1815 is byte-identical, not regenerated or requantized. Side-facing/distant planes, original skyline openings, moon, streetlamps, vanishing point, road, crosswalk, sidewalk and plane boundaries are frozen. The original 1280px mini-mall/Neon Strip is index-for-index exact, including LUCKY7 PAWN / LAST CALL LIQUORS. Opening layouts and architectural footprints remain the approved native composition; this is material/joinery restoration, not a building-scale redesign.

[Edit proof](../../art/intersection-detail-complete/proof.json) · [validation record](validation.json).

## Memory solution and tradeoff

Lossless parsing experiments on the hotel payload saved only about2.9 KiB, insufficient as a general solution for restoring all the foreground detail. Instead, the compressed source no longer occupies a large static array in addition to the already-reserved Jo heap.

At Level1 load, one allocation in the existing fixed **393,216-byte Jo heap** owns the compressed file, its aligned NUL padding, and the existing decode-cache suffix. The file is size-checked before a direct read into that allocation, avoiding a second whole-payload temporary copy. No expansion RAM, extra video bank or new heap-capacity setting is used. A single owner is freed on failure, reload and normal Level2 handoff; the interior decode pointer is never freed independently.

This is a native memory-ownership change to boot/retirement, **not a new codec**. The 512-byte block/LZ512/global-Huffman format, decoded bytes, runtime decoder/cache/prefetch/render function bodies, two-block prefetch budget, VRAM residency and gameplay-I/O behavior stay unchanged. All of those functions are source-compared against89b0332. There are no gameplay allocation or CD-read calls added. Both compressed source and cache retire before Level2.

| Resource | Hotel baseline | Complete candidate |
|---|---:|---:|
| Unique source tiles | 5,362 | 5,369 |
| Packed source bytes | 207,300 | 225,892 |
| Static source/tables estimate | 241,703 B | 34,414 B |
| Decode cache + metadata payload | 68,304 B | 68,308 B |
| Retained background heap payload | 68,304 B | 294,204 B |
| Actual owner allocator block | 68,312 B | 294,212 B |
| Total fixed Jo heap capacity | 393,216 B | unchanged |
| VDP2 resident tiles / cells | 1,664 /106,496 B | unchanged |
| VDP2 ring / total reserved | 16,384 /434,176 B | unchanged |
| VDP1 definitions / textures | 177 /371,072 B | unchanged |
| Protected Buck/Chuck VDP1 reserve | 49,152 B | unchanged |
| SCSP high-water / free | 485,812 /38,476 B | unchanged |
| Palette bytes / additional banks | unchanged /0 | unchanged /0 |
| Tested linked image end | 0x060e4844 | 0x060b23f4 |
| Gap below actual SGL vertex work0x060e5784 | 3,904 B | 209,808 B |

Higher retained heap use is the explicit tradeoff. The heap capacity itself was already reserved and does not grow. The complete fixed heap now ends at0x060b1f20, below the SDK sort boundary0x060c0000; the exact live allocation is independently range-checked before reading. Validation checks both this whole-heap bound and the actual linked SGL vertex-work constant, rather than weakening the old memory guard. Load-time map-transfer slack is also enforced. No lossy tile merging, global palette reduction, sprite duplication, reserve borrowing or art-quality reduction is used to fit.

[Detailed memory comparison](memory-comparison.json) · [compiled sprite audit](sprite-memory.csv).

## Validation and rendering cadence

**PASS:** native stage-default, make check, make test, deterministic native art conversion and lossless packing, all-camera scrolling0–1600 forward/reverse, ring wraps/previous scan-out, corrupt/truncated stream handling, guarded VRAM tails, UBSan combat/world/co-op/Ricky/bat/flame/charge/jump-cancel/renderer tests, and sprite/Fire/Hit/audio memory audits.

New ownership tests exercise eight source-buffer reloads, exact file-size rejection, allocation/read/length failures, SDK-bound rejection before writing, base-only free and Stage2 retirement. Native telemetry shows the actual294,212-byte allocator block, both world endpoints/checkpoints, three enemy slots and zero asset/parallax errors.

The memory-only prototype matched all3,300 recorded game-prefix samples against the hotel baseline. Full-art combat traces are not frame-identical: render/input-latch scheduling can change contact and hit-stop, so game.ticks is not used as an FPS metric. A separate direct, read-only production A/B rebuild compares render-update observations using last_vblank:

| Over3,300 samples | Rebuilt89b0332 sources | Complete candidate |
|---|---:|---:|
| Observed update frames | 3,110 | 3,112 |
| Update observations per60Hz second | 56.563 | 56.599 |
| 99th-percentile VBlank lag | 2 frames | 2 frames |
| Rare maximum observed lag/gap | 7 frames | 8 frames |

The candidate is within the baseline emulator update cadence, with two more observed updates; this is not a claim of hardware GPU frame rate or frame-identical combat. The report retains the rare maximum difference instead of hiding it. Hardware appearance, timing and audio listening remain user playtest items.

[Native cadence A/B](native-cadence-comparison.json) · [combat timing diagnostic](gameplay-timing-comparison.json) · [normal-input traversal](native-traversal.json).

[Repeated cold starts](cold-starts.json) have no state/image differences, with556 aligned Level2 ticks /546 images and verified retirement of BOTH background pointers. A [direct comparison against the recorded approved hotel build](level2-baseline-comparison.json) matches555 common Level2 ticks and545 images exactly. No emulator RAM writes, forced NPC attacks/healing, teleports or warm-state loading are used.

Gameplay, input, enemy limits/AI/spawns, Ricky attacks, camera/world/checkpoints, scoring, audio and Level2 source/assets are byte-identical to89b0332. Only background art/generated metadata, source-buffer ownership, validation wiring and review tooling/evidence change. Historical suites remain intact and run from their own approved archived sources.

## Reproduction and delivery

Native sources are `art/intersection-detail-complete/residential-native.png` and `records-native.png`; high-resolution generation studies are not needed. `tools/apply-intersection-detail-complete.py` enforces the exact mask/palette, then `tools/prepare-intersection-detail-complete.py` reuses the existing lossless encoder and reports static-versus-heap storage accurately. `tools/preview-intersection-detail-complete.py` regenerates review crops. Older hotel/Phase3A preview files stay frozen.

The memory checkpoint5fe97be, art checkpointb767c23, lettering refinement35bafe1 and validation/cadence tooling1399628 were pushed separately. The final branch-head delivery adds evidence without altering runtime/art payloads. No intermediate building approval was requested; all remaining foreground fronts are finished in this candidate.

**Manual Saturn playtest build:** select workflow from `art/level1-intersection-detail-pass`, `profile=stage-default`, `source_ref=<final full commit SHA reported in chat>`. Artifact: `mullet-force-stage-default-<resolved SHA>` (one-day retention). Keep the matching BIN/CUE together. **Candidate is ready for visual and hardware review; not declared user-approved.**
