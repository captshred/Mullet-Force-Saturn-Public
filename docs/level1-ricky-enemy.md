# Phase 6: Ricky enemy integration

Branch: `feature/level1-ricky-enemy`. Phase 5 base: `1dd66746f37333914408234fc14d520858ac59fd`. Authoritative PNG upload: `d761baff87836dd4eaf74adc0d7d92070980a863`. This extends Phase 5; no THE ONE tag or baseline branch is moved.

## Artwork and conversion

Authoritative source: [Ricky_HQ_Animation_Sheet.png](../Ricky_HQ_Animation_Sheet.png), SHA256 `7928d4f38fcd4a76fae9053d1ab466b10af6d8c2e966b1ecacaf903c5e62627b`.

The printed sheet says 24 frames, but depicts 25: idle 3, walk 6, punch 3, chain 4, jump 2, hurt 2, knockdown/death 3, turn 2. All 25 are retained. [Atlas](../assets/ricky/atlas.png), [machine-readable inventory](../assets/ricky/manifest.json), PNGs and native TGAs are in `assets/ricky/`.

`python3 tools/prepare-ricky-art.py` reproduces crops, indexed TGAs, atlas, palette and native metadata. Dependencies: Pillow, NumPy, SciPy (authoring only; native build consumes committed conversions). All artwork pixels come from the supplied PNG. Reviewed masks separate overlapping neighboring chains, remove floor strips and discard labels/background; small outline gaps are closed before transparent masking. No replacement art, generated pixels or reconstructed limbs. Nearest-neighbor scaling is consistent within each row; the larger turn drawings use their own scale to match the roughly 84-pixel standing height. Jump 2 retains its elevation above the ground anchor. Widths are padded to multiples of eight, allocations rounded to 32 bytes.

Native format is indexed 8-bit, one dedicated palette with 254 quantized source colors, no dithering. Raw TGA index 0 is the transparency key; raw 255 is forbidden because Jo adds one to non-key indices. RGB555 CRAM conversion is generated from the same palette. Full-body sprites avoid multi-part arm duplication and chain alignment drift. Horizontal flipping uses the same root anchor.

| Pose | ID | Width × height | Anchor x,y | Allocated bytes |
|---|---:|---:|---:|---:|
| idle-0 | 152 | 56 × 85 | 27, 84 | 4768 |
| idle-1 | 153 | 56 × 83 | 27, 83 | 4672 |
| idle-2 | 154 | 56 × 84 | 26, 84 | 4704 |
| walk-0 | 155 | 48 × 84 | 26, 84 | 4032 |
| walk-1 | 156 | 40 × 84 | 19, 84 | 3360 |
| walk-2 | 157 | 48 × 84 | 27, 84 | 4032 |
| walk-3 | 158 | 32 × 84 | 18, 84 | 2688 |
| walk-4 | 159 | 48 × 84 | 36, 84 | 4032 |
| walk-5 | 160 | 56 × 84 | 33, 84 | 4704 |
| punch-0 | 161 | 56 × 86 | 29, 86 | 4832 |
| punch-1 | 162 | 72 × 83 | 27, 83 | 5984 |
| punch-2 | 163 | 56 × 84 | 29, 84 | 4704 |
| chain-0 | 164 | 64 × 80 | 30, 81 | 5120 |
| chain-1 | 165 | 72 × 96 | 32, 96 | 6912 |
| chain-2 | 166 | 72 × 100 | 39, 100 | 7200 |
| chain-3 | 167 | 128 × 83 | 36, 83 | 10624 |
| jump-0 | 168 | 48 × 61 | 22, 61 | 2944 |
| jump-1 | 169 | 64 × 76 | 28, 100 | 4864 |
| hurt-0 | 170 | 56 × 78 | 32, 80 | 4384 |
| hurt-1 | 171 | 48 × 60 | 20, 61 | 2880 |
| death-0 | 172 | 72 × 50 | 36, 62 | 3616 |
| death-1 | 173 | 80 × 43 | 37, 46 | 3456 |
| death-2 | 174 | 80 × 20 | 36, 24 | 1600 |
| turn-0 | 175 | 48 × 82 | 18, 84 | 3936 |
| turn-1 | 176 | 48 × 83 | 18, 85 | 4000 |

## Resident bank and budget

| Region | Definitions | VDP1 bytes |
|---|---:|---:|
| Unchanged persistent prefix, IDs 0–137 (including 14 views) | 138 | 224,000 |
| Unchanged Corporate Punk, IDs 138–151 | 14 | 33,024 |
| Ricky, IDs 152–176 | 25 | 114,048 |
| Total | 177 | 371,072 |
| Free of 458,488 usable texture bytes | 78 definitions | 87,416 |
| Protected Buck/Chuck reserve | — | 49,152 |
| Additional margin after reserve | — | 38,264 |

[Actual boot allocation audit](ricky-runtime/allocation.csv). The 40 KB estimate was a planning target: the full 25-pose body bank is larger, while preserving the hard reserve and extra margin. Meeting 40 KB would require a separately reviewed part/tile decomposition or a lower-color format; no poses or source quality were sacrificed for that target.

Corporate Punk and Ricky remain simultaneously resident. Spawning performs no CD reads, texture registrations or palette swaps. The composite descriptor installs CP first, then Ricky. Its validation checks every private ID, size, indexed format, contiguous allocation, palette hash and reserve. Existing Phase 5 drain/free/reload/failure/retire code is byte-for-byte unchanged. Reloading replaces the complete suffix, with private IDs invalidated during drain and teardown.

Palette 2 reuses the already-allocated, dormant legacy Buck palette. Direct renderer traces verify no unchanged indexed draw uses it. No new CRAM bank is allocated. Palette 4 (CP/shared hero weapon) and palette 5 (CP burn) retain their exact values. Ricky uses palette 2, plus the existing flame/ember overlays; CP's burn remap is not applied to Ricky's different palette. VDP2 textures/maps/allocations are unchanged. SCSP sample bytes, music, driver, command scheduler and E108/WDEATH protections are unchanged: no new sound-bank allocation. Existing swoosh, hurt and impact events are reused.

## Gameplay and animation

The two existing enemy slots, spawn RNG/locations/grace/pacing, camera, score and 40-KO transition remain. A separate successful-spawn counter chooses five CP then three Ricky per eight spawns (37.5% Ricky), allowing CP+CP, mixed, and Ricky+Ricky. It consumes no spawn RNG. Ricky has the same six HP and defeat score as a regular CP; his distinction is attack range and controller, not altered hero damage.

Ricky pursues along either axis or diagonally, with stable existing co-op target selection. A chain is committed within 76 pixels and nine pixels of depth, faces the captured direction, winds up for 22 ticks, activates for four, then recovers for 24. Its hitbox reaches 82 pixels, consistent with the extended artwork. Within 36 pixels he uses a 12-tick punch windup, three active ticks and 24 recovery ticks, with 40-pixel reach. Each attack hits each player at most once and respects height, depth, facing and invulnerability. Windup/recovery cannot damage. Existing player attacks interrupt him; normal burn processing and death/score handling are shared. Running bat retains its approved regular-enemy KO behavior. Corporate Punk AI 3.0 functions and constants are unchanged.

| State | Source poses |
|---|---|
| Idle | idle 0–2, 12 ticks each |
| Walk | walk 0–5, 6 moving ticks each |
| Punch | punch 0 windup, punch 1 extension/active, punch 2 recovery |
| Chain | chain 0 ready, 1 rise, 2 overhead during windup; 3 extended active; 0 recovery |
| Hurt | hurt 0–1 |
| Knockdown/death | death 0–2 over existing 30 ticks |
| Jump/turn | all four native poses exposed through explicit pose API and tested in native fixtures; no new jump or turn movement mechanics |

Buck/Chuck FF+A buffering, attacks, movement, flame sustain, audio scheduling and Level 2 logic/assets were not edited. Ricky-only state is appended to the game structure (12 bytes), with the native compiler flag propagated consistently to gameplay and rendering units.

## Validation and limits

- Native `stage-default` build; `make check`; `make test`; actual boot allocation audit.
- Original Phase 5 preservation/regression suite runs unchanged from its exact archived source. All Phase 5 files outside the explicitly reviewed integration list remain frozen.
- Direct current-versus-Phase-5 replay: 30,000 CP-only co-op ticks, every original game byte identical; 7,666 renderer cases and 150,855 draw commands match decoded pixels, geometry, order and shared palettes. This counterfactual keeps CP spawns to isolate unchanged systems, and does not claim full mixed gameplay is pixel-identical.
- Ricky host tests under undefined-behavior sanitizer: both players, chain/punch timing, single-hit latch, wrong lane/height/facing, interruption, jab/kick/bat/running bat/aerial bat, fire, axis/diagonal pursuit, class schedule, mixed/two-Ricky simultaneous hit protection, one KO per death and 40-KO stage entry.
- Actual loaders/manager in host tests: 256 combined suffix reloads with persistent metadata/pixels and all palettes unchanged; busy hardware, failed loads at both CP and early/middle/last Ricky resources, and invalid handles latch failure without stale draws.
- Yabause libretro pin `8926b0c6c347f8c5c755911ddb0ac695420ffbf8`, HLE, one thread, no cartridge. [Eight native reloads](ricky-runtime/bank-reloads.json): nine identical generations of persistent pixels, complete enemy pixels and palettes 2–5; correct reserve; then normal development X handoff to Level 2, no bank/Level 2 error, last sprite ID 27, 711 Level 2 ticks, nonzero audio during wait and Level 2.
- [Two separate fresh production starts](ricky-runtime/cold-starts.json): both reached Level 2 at frame 1843 with error 0; 556 aligned Level 2 states and 546 images matched, plus matching Level 1 states/images. Physical controller inputs exercise real settling/clear/CD/driver loading through the approved development X shortcut.
- [50 native pose fixtures](ricky-runtime/pose-fixtures.json): all 25 poses, both facings with two Rickys, mixed CP/Ricky, both hero sprites present. These are test-only controlled actor/pose fixtures using production loaders/draw_game/VDP1, not naturally spawned gameplay or a hardware approval.

Captured examples: [CP + Ricky chain](ricky-runtime/cp-ricky-chain.png), [two Ricky chains](ricky-runtime/two-ricky-chain.png), [walk](ricky-runtime/two-ricky-walk.png), [knockdown](ricky-runtime/two-ricky-knockdown.png), [skull-back turn](ricky-runtime/two-ricky-turn.png).

Hardware, full manual co-op playtesting, natural 40-KO playthrough and subjective audio listening remain owner validation. Emulator transitions do not prove the historical intermittent E108 issue can never recur.

## Build and publication

Local native build: `bash tools/setup.sh`, then `bash tools/build-stage.sh --native`, `make check`, `make test`. The wrapper enables Ricky only for this complete profile. Matching `build/mullet-force.bin` and `build/mullet-force.cue` must stay together. No authoring Python dependencies are needed for a normal build.

GitHub Actions: **Manual Saturn playtest build** → **Run workflow** → workflow branch `feature/level1-ricky-enemy`, profile `stage-default`, `source_ref` the exact final commit SHA from the delivery response. Download `mullet-force-stage-default-<full SHA>` when successful; retention is one day. The feature branch push does not auto-trigger this workflow. Dispatch is unavailable with the current Actions credentials, so no hosted artifact is claimed.

Optional emulator scripts: `tools/test-ricky-bank-runtime.py`, `tools/test-ricky-art-runtime.py`, and `tools/test-ricky-playable-runtime.py` require the pinned libretro core and headers; pass fresh output directories. The playable cold-start script takes the same production CUE/program as both phase1 and phase2 arguments to compare two separate processes. Native fixture builds never modify the playable source or baseline.
