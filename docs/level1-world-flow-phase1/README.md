# Level 1 world flow — Phase 1 review candidate

Starting approved baseline: `30996986f76d17863f0fe6c5a87f2a5c17cf6c68` (final background/lamp corrections, tattoo and combat polish). Branch: `feature/level1-world-flow-phase1`. Hardware/playtesting approval is pending.

## Playable behavior

World width grows from 640 to 1280 pixels: two extra 320-pixel screens. Camera range is 0–960, with a maximum two-pixel movement per tick. Configurable checkpoint floors are 0, 320 and 640 in `src/world_config.h`; reaching the endpoint still allows backtracking to 640. Players stop at world x=1254; combat continues without stage clear. KO/scoring continues past 40. Existing settling, clear, Level 2 and development X skip remain available.

Co-op uses a 240-pixel movement leash and a camera target constrained by the trailing player. The leader waits for the partner to advance; neither partner is dragged or teleported. Joining/recovering players enter the current view. Offscreen spawn candidates retain the existing class mix, pacing, grace and slot count. New actors walk into visible telegraph range before using the existing combat controller. Inaccessible live stragglers retire without score/KO credit.

The original 640-pixel opening uses its original source columns. Beyond it, the last eight source tile columns (64 pixels of VINYL facade/sidewalk) repeat as intentionally temporary scenery. No new sign, character, texture, audio or background asset was made. An existing-font TEMP STREET / TEST END HUD label identifies the prototype. Original drums remain opening-area props.

The facade uses the existing 128-column VDP2 map as a ring, updating a 43-column visible/guard window at tile boundaries. It reads the existing PCHUNK data once during loading, with no gameplay CD streaming. This is a world-column mapping seam for future authored sections; later diagonal walk-depth rules and finale gates are not implemented.

## Captures

Normal controller input on a fresh production Yabause HLE boot, without RAM writes, debug teleport or invulnerability:

1. [Original mini-mall](01-opening.png)
2. [Beyond the old camera boundary](02-past-original-boundary.png)
3. [Extended street with active enemies](03-extended-active-enemies.png)
4. [Temporary endpoint](04-temporary-endpoint.png)
5. [Checkpoint backstop](05-checkpoint-backstop.png)

[runtime.json](runtime.json) records frame/camera/player positions. These are engine captures; hardware appearance, performance, feel and audio listening remain user-review items.

## Validation

Passed native stage-default build, make check and make test. Production-flag UBSan regressions exercise 75 actual fire KOs without clear, full forward/backward traversal, both co-op leader choices and catch-up, joining, spawns at multiple camera positions and the endpoint, entry telegraphs, retirement without KO credit, and explicit stage transition. The real ring-map writer is checked at every camera position forward and reverse against the original source tile data, including wraparound and opening identity. Current-source bat/flame, charge/palette and Ricky combat regressions pass. Scope checks protect all original assets/audio/Level 2 and combat controller bodies (except required world-bound constants), and execute the unchanged approved-parent regression suites separately.

Repeated fresh Yabause boots pass with no compared state/image mismatches: 600 Level 1 state samples, 30 Level 1 images, 555 aligned Level 2 ticks and 545 Level 2 images. Physical X skip exercises settling, clear, asset loading and live Level 2. See [cold-starts.json](cold-starts.json). The production traversal independently reaches camera=960 and returns to floor=640 while taking normal enemy damage.

## Memory

| Resource | Usage | Change |
|---|---:|---:|
| VDP1 textures | 177 definitions; 371,072 bytes | 0 |
| Protected Buck/Chuck texture reserve | 49,152 bytes | 0 |
| VDP2 facade cells/map + sky cells/map | 172,032 bytes | 0 |
| VDP2 including protected SDK reservation | 434,176 bytes | 0 |
| SCSP | 485,812 bytes used; 38,476 free | 0 |

CRAM banks and sprite dimensions are unchanged. VDP1 has 87,416 bytes remaining, including the protected reserve (38,264 bytes discretionary). The new persistent CPU storage is approximately 4.7 KiB: 4,804-byte cached chunk buffer, four-byte ring cursor and four-byte per-game checkpoint floor, plus a small constant checkpoint table. [sprite-memory.csv](sprite-memory.csv) is the current compiled texture audit. GPU/audio allocations and their source payloads are identical to the approved baseline.

## Manual build

GitHub Actions workflow **Manual Saturn playtest build** (`.github/workflows/build.yml`). Select workflow branch `feature/level1-world-flow-phase1`, profile `stage-default`, and source_ref equal to the final full commit SHA on this branch. Download `mullet-force-stage-default-<resolved SHA>` and use its matching BIN/CUE together; artifact retention is one day. No approved baseline tag is moved, and this branch is not merged.
