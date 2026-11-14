# Level 1 Phase 3A — The Intersection

Candidate branch: `feature/level1-intersection-phase3a`. No merge and no approved THE ONE tag updates. Hardware and gameplay approval remain pending.

**Approved starting SHA:** `43cd82d33dd6195a036f9775f8b0e961fedbe9bb`. This is the user-approved combat-tuning branch head, including Phase 2 Neon Strip, Ricky's jump-chain/aggression, three-enemy co-op/two-enemy solo, and immediate grounded-punch jump cancel. Neither an older Phase 1 nor an older Phase 2 build was substituted.

**Runtime/native package source:** `5725578cece3072d8bee01499f7914e9e0711403`. The delivery adds captures, packaging, reports and validation-harness refinements; runtime source and assets remain identical. The final delivery SHA is the candidate branch head.

## Visual review

1. [Full 1,920 × 240 panorama](panorama.png)
2. [LAST CALL LIQUORS → intersection transition](liquor-transition.png) · [native traversal transition](native-transition.png)
3. [Background-only native 320 × 240 crop](intersection-native.png) · [complete new 640 × 240 section](intersection-640.png)
4. [Native gameplay: Buck, Chuck and three enemies](gameplay.png) · [uninterrupted combat excerpt](combat.gif)
5. [Annotated proposed Phase 3B route](perspective-future-route.png)
6. [VDP2/tile/CPU/audio comparison](memory-comparison.csv) · [sprite residency audit](sprite-memory.csv)

The new section introduces tall brick corner buildings, a restrained DELI/HOTEL/RECORDS frontage, lit and dark upper windows, a distant cross street, receding lamps, traffic signal, curb geometry and crosswalk. The main foreground roadway remains flat and horizontal. The diagonal gold arrow appears only in the annotated review image; no diagonal movement/collision path or MEGA ARCADE is implemented.

All source pixels at world X 0–1279 and every original palette entry are preserved exactly. None of the original mini-mall, Neon Strip or skyline artwork was regenerated. Native indexed new art uses the existing palette; the small HOTEL tubing participates in the existing pink animation. Preview skies composite the unchanged skyline through the new transparent upper silhouettes; the actual game retains quarter-speed skyline parallax.

Visual inspection covered the storefront join, building scale/silhouettes, vanishing point, crosswalk/road geometry, poles, lettering, texture repetition and all tile seams. Pixel/cache tests independently verify the actual native tile output. Human art and gameplay approval are still required.

## World, camera and combat

| Setting | Approved | Phase 3A |
|---|---:|---:|
| World width | 1,280 px | **1,920 px** |
| Player X bounds | 26–1254 | **26–1894** |
| Walkable depth Y | 168–229 | **168–229, unchanged** |
| Camera bounds | 0–960 | **0–1600** |
| Camera speed | 2 px/fixed tick | **unchanged** |
| Forward checkpoint floors | 0 / 320 / 640 | **0 / 320 / 640 / 960 / 1280** |
| Enemy offscreen apron | -96–1408 | **-96–2048** |
| Solo/co-op population | 2 / 3 | **2 / 3, unchanged** |

Checkpoint positions are configurable through `MF_WORLD_CHECKPOINTS`. Reaching camera X=1600/player X=1894 remains a temporary endpoint; it never automatically clears the stage or enters Level 2. The existing development X skip is preserved for regression testing.

The existing spawn scheduler and its player/peer distance checks now use the extended world bounds. Enemies still enter along the main roadway from offscreen aprons, using existing grace/walk-in behavior. The decorative side street introduces no new spawn lane, enemy type, playable path or collider.

`game.c`, `game.h`, Ricky's controller/art, player attack damage, hurt/KO/scoring, combo/FF+A buffering, hold-A charge/sustain, input mapping, audio and all Level 2 files are byte-identical to the approved starting SHA. Only world constants, background loading/cache/window routing, the section HUD label and retirement of the new CPU cache at the existing Level 2 handoff change.

## Tile architecture and memory

The existing two-page VDP2 ring and **1664-tile / 106,496-byte** resident A0 cache are retained. The source dictionary contains **5328** tiles: **3089** original visible tiles plus **2239** newly authored tiles. The original 3424-tile source file is untouched. Its 335 sky-only tiles were already hidden behind NBG2; the new runtime map exposes that same independent skyline through transparent cells instead of duplicating hidden sky payloads.

Logical source IDs may exceed 4095 because only resident physical IDs, at most 1663, enter the VDP2 pattern names. Source IDs remain bounded 16-bit values. The ring preserves the original +1 raster registration, palette bank, skyline phase/windows and wrap semantics. Its upper facade window now permits new building silhouettes above y56; transparent original-region cells leave the original skyline visible.

The 340,992-byte logical tile payload is packed losslessly to **207,704 bytes**, including three DMA-alignment pad bytes. An independently bounded eight-tile/512-byte LZ/Huffman block format and 2668-byte offset table support random access. Load-time validation checks every block, source-map ID and file length. No gameplay CD reads or allocations occur.

A fixed 128-block CPU cache prepares upcoming source groups, nearest column first, up to 128 pixels beyond the ring guard. At most two missing groups are prepared per callback. A bitset pins current/prior video scan-out; future CPU preparation cannot evict pinned video tiles. Native/UBSan tests show a maximum **30 tile uploads / 1920 bytes per ring update**, with both current and previous visible scan-outs valid.

| Resource | Approved | Phase 3A | Change |
|---|---:|---:|---:|
| VDP1 definitions / textures | 177 / 371,072 B | same | **0** |
| Protected future sprite reserve | 49,152 B | same | **0** |
| VDP2 resident facade cells | 106,496 B | same | **0** |
| VDP2 ring map | 16,384 B | same | **0** |
| Total VDP2 reserved | 434,176 B | same | **0** |
| Palette / CRAM banks | original | same | **0** |
| SCSP high-water / free | 485,812 / 38,476 B | same | **0** |
| Static source/tables/scratch estimate | 242,352 B | 242,006 B | **-346 B** |
| Retained CPU decode-cache payload | 0 | 68,284 B | **+68,284 B** |
| Actual Jo allocator block | 0 | 68,292 B | **+68,292 B** |
| Jo heap capacity | 393,216 B | same | **0** |
| Linked code/data/BSS end | `0x060e4274` | `0x060e4984` | **+1808 B** |

The new heap allocation uses the existing CPU heap; it does not enlarge any engine pool. Native telemetry places its payload at **`0x060844cc`**, ending at **`0x06094f88`**, below the linked SDK sort-work boundary `0x060c0000`. It is freed before Level 2 begins; both fresh native skip runs assert that retirement.

The audit now reads the actual linked **SGLAREA Pbuffer boundary `0x060e5784`**, rather than relying on the SDK header's approximate memory-map comments or the older `0x060f0000` guard. The candidate linked end leaves **3584 bytes** below that boundary. The earlier oversized packing trial was rejected after emulator testing exposed work-memory overlap; the delivered layout passes the stricter check. SDK/compiler pins, SGLAREA, Docker base, video/audio reservations and asset sizes remain unchanged.

## Validation results

**PASS:** native `stage-default`, `make check`, `make test`, current-source UBSan gameplay/world/cache/combat regressions, unchanged approved historical suites, deterministic packing, VDP1/VDP2/SCSP audits, and packaged source/artifact checksums.

Current tests cover:

- Every camera X=0–1600 in both directions; original/new native pixels, prior scan-out, ring wrap, cold resets, large mock camera changes, VDP2 bank-tail guards and malformed/truncated source streams.
- Complete solo and co-op traversal to the new endpoint, reverse traversal to checkpoint 1280, smooth fixed-tick camera bounds, co-op tether/no stranding, offscreen spawning, slot retirement without KO credit, join/leave and no automatic stage clear.
- Solo maximum **2**, co-op maximum **3** throughout the extended world. The approved combat fixture matrix now also runs at cameras **1280 and 1600**, with every slot/class attacking, taking damage, dying and retiring.
- Every punch/cross startup, active and recovery tick for both heroes; hit/miss/already-dealt damage, moving cancellation, three independent hit-latch bits, buffered A, held B, hit-stop, hurt/death/bat/torch guards, FF+A buffering and flame charging through damage.
- Ricky's launch/air/landing, captured trajectory, single-hit latches, lane/height misses, interruption, cooldown and rendering, extended to all new camera checkpoints. The 4 × 60,000-tick input-only combat stress exercise records punches, standing chains and jumping chains without NPC forcing.
- Actual production renderer: 144 mixed CP/Ricky/chain/bat/flame/embers/impact fixtures, maximum 45 sprite draws, unchanged shared texture residency.

[Native traversal telemetry](native-traversal.json) records camera maximum **1600**, checkpoint maximum/backstop **1280**, three active enemies and **zero asset/parallax errors**. Its controller walks both characters, pauses for 360 ticks of normal combat in the intersection, reaches the endpoint, then reverses. It uses no RAM writes, forced healing, teleports or save-state loading.

The camera remains bounded to **2 pixels per fixed simulation tick**. In the heavy co-op capture, the existing catch-up loop sometimes combines fixed ticks into one video callback; the largest recorded callback displacement is 7 pixels. The supplied footage is for visual/gameplay review and does not establish hardware frame-time approval.

[Two independent cold boots](cold-starts.json) of this same candidate have **zero state/image mismatches**, zero runtime errors and healthy normal X-skip → settling/clear → Level 2 loading/audio readiness. They compare **555 common Level 2 ticks / 545 images**. The wrapper also checks the new CPU cache is absent once the Level 2 handoff starts. Current native allocator/readiness and Fire/Hit/Flame/Explosion/audio-resource regressions pass; this is not an audio-listening claim.

See [machine-readable validation](validation.json) and [current test results](test-results.txt). Hardware and human gameplay/art approval remain pending.

## Playable package and exact manual build settings

[Download the matching BIN/CUE ZIP](../../downloads/mullet-force-level1-intersection-phase3a.zip). Extract both files together and open the CUE. The archive includes source identity, source/payload checksums, review notes, memory results and licenses.

Workflow: **Manual Saturn playtest build** (`.github/workflows/build.yml`).

- **Use workflow from:** `feature/level1-intersection-phase3a`
- **profile:** `stage-default`
- **source_ref:** full final candidate branch-head SHA, or `feature/level1-intersection-phase3a` to resolve that head

For the exact native package here, use source ref **`5725578cece3072d8bee01499f7914e9e0711403`**. The profile already selects preserved audio. The existing workflow uploads one matching playable artifact with one-day retention. No workflow, merge or approved-tag changes were made.
