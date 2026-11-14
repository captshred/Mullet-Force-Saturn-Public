# Intersection foreground scale and window correction

Branch: `art/level1-intersection-scale-fix`. No merge or approved tag changes. Hardware/playtesting approval remains pending.

**Starting SHA:** `7312ce1a2c21ab7881ad9e617b60524bf5736cb6`.
**Runtime/art package SHA:** `63ff0ecf5398b991bace6a081a58dae683425f77`. The final branch-head delivery commit adds evidence and packaging without changing that art/runtime tree.

## Visual review

1. [Shopping-strip transition, before/after](transition-before-after.png). LAST CALL LIQUORS is included as the unchanged scale reference in both panels.
2. [Foreground residential building, before/after](residential-before-after.png) · [right commercial frontage](foreground-before-after.png).
3. [Full corrected intersection](intersection-640.png) · [full 1920px panorama](panorama.png) · [320px native background crop](intersection-native.png).
4. [Native gameplay with Buck, Chuck and Ricky](buck-ricky-gameplay.png) · [three-enemy gameplay](gameplay.png) · [normal-input combat clip](combat.gif).
5. [Opaque foreground windows at two scrolling positions](opaque-windows-scrolling.png).
6. [Updated tile/memory comparison](memory-comparison.csv) · [VDP1 audit](sprite-memory.csv).

The supplied gameplay screenshots were used to identify the foreground scale mismatch. The original storefronts provide the final architectural reference: ground floors now occupy approximately the same 90–96px facade height, doors are about 48–50px tall and 22px wide, and brick/window detail is substantially larger. The fronts retain a deli, shuttered entrance, hotel arch and restrained RECORDS signage. Upper floors continue beyond the viewport; entire roofs are no longer squeezed into view.

The approved cross street is a separate perspective plane. Its vanishing point, distant buildings, moon, lamps, skyline and road remain pixel-for-pixel intact. Only the near front planes are enlarged. The base/sidewalk at y152 and all pixels below it are unchanged, preserving curb/road alignment and the horizontal playable street.

## Exact art-only preservation and opacity

The correction mask covers new-section x0–240 and x416–639 above y152, excluding the real sky above the low left transition wall (x0–61, y0–55). Every pixel outside that mask is identical to the starting artwork. This explicitly freezes the receding road, side faces, moon, streetlights, skyline openings, sidewalk, crosswalk and foreground roadway.

**Zero transparent pixels remain inside the corrected foreground mask.** Window interiors are opaque dark blue/near-black, lit rooms or blinds. Intentional transparency in the actual sky remains. This property is independent of camera position or parallax phase; full scrolling tests verify the actual cache-decoded pixels in both directions. The side-by-side native scrolling screenshots provide the visual check.

The original mini-mall and Phase 2 Neon Strip remain pixel-for-pixel unchanged. All palette bytes, including animated neon entries, are byte-identical. Newly corrected front-plane pixels avoid the animated entry range; the existing side-facing HOTEL neon is preserved with the approved distant plane.

Every existing runtime `.c` file, gameplay/header configuration except generated background data, AI, collision/spawning, controls/jump cancel, solo/co-op population limits, camera/world/checkpoints, stage progression, audio and Level 2 file is checked against the exact starting SHA. Only native indexed background inputs, derived packed tiles/map/offsets/Huffman data, validation wiring and new review evidence change.

## Resource comparison

| Resource | Phase 3A | Scale fix | Delta |
|---|---:|---:|---:|
| Logical source tiles | 5328 | **5362** | +34 |
| Packed source payload | 207,704 B | **200,416 B** | **-7288 B** |
| Static source/tables estimate | 242,006 B | **234,823 B** | -7183 B |
| CPU decode-cache payload | 68,284 B | **68,304 B** | +20 B |
| Native allocator block | 68,292 B | **68,312 B** | +20 B |
| Linked code/data/BSS end | `0x060e4984` | **`0x060e2d74`** | **-7184 B** |
| Gap below linked SGL Pbuffer `0x060e5784` | 3584 B | **10,768 B** | +7184 B |
| VDP2 resident tiles / cells | 1664 / 106,496 B | same | **0** |
| VDP2 ring / total reservation | 16,384 / 434,176 B | same | **0** |
| VDP1 definitions / textures | 177 / 371,072 B | same | **0** |
| Protected future sprite reserve | 49,152 B | same | **0** |
| SCSP high-water / free | 485,812 / 38,476 B | same | **0** |

The larger architectural pixel clusters compress better. Only the generated background data changes; the existing decoder, cache/prefetch architecture and heap-capacity settings remain untouched. The extra five source blocks account for the 20-byte CPU metadata/cache adjustment. Native telemetry confirms the actual allocator size and valid placement; Level 2 cold-start checks verify normal cache retirement. No video/audio pool, palette bank, engine pin, Docker base or protected reservation increases.

## Validation

**PASS:** native `stage-default`, `make check`, `make test`, full background/tilemap/scrolling regression, UBSan world/combat/cache tests, repeated Yabause cold starts and Level 2 skip/audio-readiness regressions.

- Every camera position 0–1600, both directions, prior scan-out pinning, ring wraps, cold resets and malformed/truncated tile streams.
- Original 1280px region, unchanged palette, unchanged pixels outside the foreground correction mask and zero transparent foreground pixels.
- World remains 1920px; checkpoints 0/320/640/960/1280; walkable depth 168–229; solo/co-op maxima 2/3; Ricky jump-chain, punch jump cancel, FF+A and flame regressions.
- Native normal-input traversal reaches camera1600 and returns to checkpoint1280; Buck, Chuck, Corporate Punks and Ricky fight in the corrected intersection. No NPC forcing, RAM edits, forced healing or save-state loading. The longer review run uses an 1100-tick normal combat hold to include Ricky naturally.
- Two independent native cold starts: **zero state/image differences**, zero errors; **555 common Level 2 ticks / 545 matching images**, normal handoff/readiness and retired background CPU cache.
- Current tests read the generated tile-count constants and validate all current sources. A historical test's summary string still says 5328; the actual current count is **5362**, as recorded in the manifest and memory report.

[Native telemetry](native-traversal.json) · [cold-start comparison](cold-starts.json) · [validation record](validation.json) · [test results](test-results.txt).

All controls, camera timing and gameplay are unchanged. Emulator callback catch-up remains observable in the stress footage; these checks do not establish real-hardware frame-time or subjective art approval.

## Playable files and manual Actions settings

[Download matching BIN/CUE](../../downloads/mullet-force-intersection-scale-fix.zip). Keep both files together and open the CUE. The archive includes exact source identity, validation, matching checksums and licenses.

Workflow: **Manual Saturn playtest build** (`.github/workflows/build.yml`).

- **Use workflow from:** `art/level1-intersection-scale-fix`
- **profile:** `stage-default`
- **source_ref:** the full final branch-head SHA (or `art/level1-intersection-scale-fix` to resolve the current candidate)

For the exact packaged art/runtime build, use `63ff0ecf5398b991bace6a081a58dae683425f77`. The final delivery retains the same runtime/art content. Preserved audio and one-day playable artifact retention remain configured by the existing workflow.
