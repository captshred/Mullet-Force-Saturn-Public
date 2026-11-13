# Level 1 Phase 2 — neon strip art review candidate

Starting approved jump-chain baseline: `0de58676e2cb703f6e68552cc46ca0ec03809110`. Branch: `art/level1-neon-strip-phase2`. User art/hardware approval is pending. No merge, branch replacement or THE ONE tag change.

## Visual review

- [Full native 1280×240 panorama](panorama.png)
- [Original VINYL → pawn-shop transition, enlarged](transition.png)
- [LUCKY 7 PAWN, enlarged](lucky-7-pawn.png)
- [LAST CALL LIQUORS, enlarged](last-call-liquors.png)
- Native 320×240 production Yabause: [opening](01-opening.png), [transition while scrolling](02-past-original-boundary.png), [pawn shop with live enemies](03-extended-active-enemies.png), [liquor store with live enemies at endpoint](04-temporary-endpoint.png), [checkpoint backstop](05-checkpoint-backstop.png).

The pawn shop includes barred guitars/CRT electronics displays, a recessed doorway, payphone and torn concert posters. LAST CALL has green lettering/pink trim, grated bottle displays, OPEN tubing and a recessed doorway. Small worn trim, paper, brick marks and wet-road reflections add variety. The new overhead fixtures are mounted directly on the facade; no streetlamp support or freestanding pole is introduced. Visual inspection covered both storefronts and their boundaries, lettering, brick columns, grates, sidewalk registration and native runtime captures.

The panorama is the indexed facade/road overview with static sky samples. Actual gameplay uses the exact original separately scrolling quarter-speed skyline; it does not tile a second copy of the skyline in camera space. The original first 640 pixels are preserved index-for-index, and every palette color they use remains bit-identical, including the animated ION groups. Source sky and sidewalk samples in the extension reuse existing geometry. Both shops are actual background art, not interactive props.

## Encoding and memory audit

The initial audit found 1,664 original 8×8 tiles in A0, with only 384 additional tiles worth of contiguous A0 space. Two new facades were not treated as a free doubled atlas. The authored panorama has 3,424 exact unique indexed tiles (+1,760); keeping all 219,136 cell bytes resident would exceed A0. Instead, the existing map ring now resolves source tile IDs through a fixed 1,664-slot cell cache.

| Resource | Approved baseline | Candidate | Allocation delta |
|---|---:|---:|---:|
| Unique authored 8×8 tiles | 1,664 | 3,424 | Source data +1,760 |
| Resident A0 cell slots | 1,664 | 1,664 | 0 |
| Resident facade cells | 106,496 B | 106,496 B | 0 |
| Facade ring map in B0 | 16,384 B | 16,384 B | 0 |
| Skyline cells + map in B0 | 49,152 B | 49,152 B | 0 |
| VDP2 including protected SDK banks | 434,176 B | 434,176 B | 0 |
| Palette allocation | Same 255-color bank | Same bank | 0 |
| VDP1 textures | 177 / 371,072 B | 177 / 371,072 B | 0 |
| Protected Buck/Chuck VDP1 reserve | 49,152 B | 49,152 B | 0 |
| SCSP high-water / free | 485,812 / 38,476 B | 485,812 / 38,476 B | 0 |
| Persistent CPU cache/map state | 4,808 B | 242,352 B | +237,544 B |

A0's last 24,576 bytes and B0's last 65,536 bytes remain unused. SDK-owned A1/B1 banks are untouched. New source tile data is loaded into CPU storage once at boot, not copied wholesale to VRAM. Raw source IDs use a 9,600-byte chunk table; hardware pattern names remain one word, palette bank 1, even cell addresses, and within the original 1,664-slot allocation.

At each 8-pixel column boundary, the cache pins the current and previous 43-column guard windows, evicts only unneeded cell slots, uploads their exact 64-byte tiles and updates the existing ring. Sequential tests measure at most 29 tile uploads (1,856 bytes) per update. There are no gameplay CD reads, new VDP2 allocations or lossy tile merges. Opening cells can be reconstructed exactly after cache eviction; initialization also restores the original prefix for repeated loads.

The CPU tradeoff is explicit: the new static source/cache state adds about 232 KiB. The tested native linked image ends at `0x060e4214`, leaving 48,620 bytes before the conservative `0x060f0000` guard and 114,156 bytes before the top of the 1 MiB region. Validation rejects images reaching the guard. [Detailed memory audit](memory.json), [compiled sprite audit](sprite-memory.csv).

The 23 previously unused palette entries (225–239 and 248–255) carry selected gold/red/green shades. They were unused by both original facade and skyline sources. Every originally used palette word and all eight existing animated words remain exact. Pink liquor tubing shares existing pink animation indices; green/gold use static entries. New RGB555 source art is mapped to this fixed palette without dithering or global requantization. RGB555 RMS error is 0.818 channel steps (about 6.5 RGB888 units) over authored regions; original pixels have zero error. No palette bank is added and Ricky's base/burn palettes are untouched.

`assets/level1-neon-strip/SOURCE555.BIN` is the native art source. `tools/prepare-level1-neon-strip.py` reproducibly packs NSPIX, NSCELL, NSMAP, NSPAL, manifest and generated cache-size metadata. The high-resolution image-generation study stays outside the public runtime package. Existing city-cleanup assets and their conversion pipeline remain intact and are reused as the immutable original prefix.

## Preservation and validation

Passed native stage-default, make check, make test, deterministic asset round-trip, complete indexed source/tile reconstruction and palette isolation validation. The real cache/map writer is checked under UBSan at every camera offset 0–960 forward and reverse, including the 1024-pixel ring wrap, repeated loads, current/previous scan-out integrity and A0/B0 tail guards. The tests protect the exact old 640-pixel background, skyline assets and animation code.

Current-source world, combat, co-op, bat, flame/charge, Ricky jump-chain and renderer regressions pass. `src/game.c`, game state/configuration, input, AI, spawns, Ricky artwork and controllers, audio and Level 2 source/assets are byte-identical to the approved baseline. The only HUD edit replaces TEMP STREET with NEON STRIP; TEST END and stage behavior remain. Native packaging fingerprints the new art and packs only its needed runtime files for the live stage-default profile.

The unchanged approved-parent test suites also run from their own archived trees, preserving historical locks rather than weakening them for intentional new background content. Sprite and Fire/Hit/SCSP resource audits pass.

[Production traversal report](runtime.json) records the endpoint camera=960 and backstop camera/floor=640, with ordinary player damage and live enemies. All five selected player/camera/health snapshots match the previously recorded world-flow traversal. No RAM writes, teleports or enemy forcing are used. [Repeated Yabause cold starts and development X skip](cold-starts.json) have no state/image mismatches across 600 Level 1 state samples / 30 images and 555 aligned Level 2 ticks / 545 images. A [direct comparison against the recorded pre-Phase2 jump-chain production run](level2-baseline-comparison.json) also matches all 555 Level 2 ticks and 545 images exactly. These are HLE checks; hardware appearance, performance and audio listening remain user playtest items.

World width remains 1,280; checkpoint floors remain 0/320/640; no 40-KO clear is reinstated. Ricky's jumping chain/aggression, 3-HP bat, charging through damage, flame-contact stun, co-op, scoring and enemy proportions are preserved.

## Exact Manual Saturn playtest build settings

Workflow: **Manual Saturn playtest build** (`.github/workflows/build.yml`). Use workflow from `art/level1-neon-strip-phase2`. Set `profile` to `stage-default`. Set `source_ref` to the final full pushed commit SHA reported for this branch. Artifact: `mullet-force-stage-default-<resolved SHA>` (one-day retention). Use its matching BIN/CUE together. Art and playtesting approval remain pending.
