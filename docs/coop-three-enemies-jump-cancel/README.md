# Three-enemy co-op and immediate punch jump cancel

Candidate branch: `balance/coop-three-enemies-jump-cancel`. No merge or THE ONE tag changes. Hardware/playtesting approval remains pending.

Approved starting baseline: **f05bc55d357f258fc924d41f5bdd58050a317e60** (`art/level1-neon-strip-phase2`). This is the Phase 2 Neon Strip commit, directly after Ricky jump-chain `0de5867`, with the 1,280px world-flow extension in its ancestry. Main (`03de852`) was older and was not used as the starting point.

Implementation/native package source: **0f5daa1b82de22fa2050d49673a8ddb4a2462d81**. The delivery commit adds this report, captures and a matching playable archive; source files remain identical. The final delivery SHA is available from the candidate branch head.

## Behavior and actor audit

Actual Level 1 actor capacity was **2**, now **3**. `mf_enemy_limit()` permits 2 with one joined player and 3 with both joined players. `mf_enemy_count()` counts every non-ABSENT slot, including DYING actors, regardless of Corporate Punk/Ricky class. Both stage spawning and the legacy respawn path enforce this population rule. Defeated players remain joined during their existing recovery; physical P2 disconnect deactivates that player, and Start rejoins through the existing recovery path.

Joining does not immediately create an actor: the existing randomized scheduler, offscreen candidate search, grace and walk-in telegraph perform the spawn. After P2 leaves, all three enemies continue their AI/death/retirement paths; replacements wait until fewer than two slots are occupied. KO/scoring paths are unchanged.

The audit replaced enemy-only `1-index` assumptions with bounded peer scans for class behavior/lane selection, target pressure and pursuit spacing. The two-player arrays keep their existing indexing. Enemy actor/class/AI/burn-owner/punch/jump arrays and corporate presentation arrays are all capacity-sized. Render, collision, torch, hit-latch, retirement and bank-drain loops iterate all three slots. Punch hit masks use bits 3..5, safely within their existing integer field. Ricky's controller, attack timing, aggression and art are byte-identical. Both enemy classes share the existing resident definitions; neither requires per-actor texture copies or SDK animation slots.

The enemy HUD now fits three bars inside 320 pixels/40 text columns during co-op, retaining the original solo layout. It also retains three-column placement while the third actor slot remains occupied after disconnect.

## Jump priority and safety

The cause was `!p->attack` in the jump gate, which rejected a fresh B edge during a punch. On that edge, `player_step()` now clears an ordinary grounded punch before the jump gate and before hit resolution, then takes the original launch path. It clears the attack timer, air flag, hit mask, queued jab, stale buffered A and pending running-bat state; the original launch path resets combo/gesture/torch charge. Damage already dealt is retained. A canceled punch cannot hit again, and holding B never retriggers a jump.

The guard requires grounded height/velocity, a normal punch, no bat, no aerial attack and no torch; it remains inside the existing living/hurt-state gates. Bat/torch actions do not acquire punch cancellation. FF+A command classification/buffering and hold-A charge/sustain remain covered by current regressions. Existing global hit-stop is preserved: B received during a freeze is buffered and cancels on the first advancing simulation tick, without waiting for punch recovery.

Native input-only traces show Buck punch tick 7 at frame 1107 becoming attack 0 / height 1510 at frame 1108; Chuck tick 7 at frame 1410 becomes attack 0 / height 1510 at 1411. This is the unchanged 1510 launch velocity and ordinary gravity/air control.

## Memory comparison

| Resource | Approved baseline | Candidate | Delta |
|---|---:|---:|---:|
| Actor capacity | 2 | 3 | +1 |
| `sizeof(mf_game)` | 828 B | 980 B | +152 B CPU |
| Corporate per-slot presentation state | 16 B | 24 B | +8 B CPU |
| Linked data/BSS end | `0x060e4214` | `0x060e4274` | +96 B including code/alignment/layout |
| Space below `0x060f0000` guard | 48,620 B | 48,524 B | -96 B |
| VDP1 definitions / texture payload | 177 / 371,072 B | 177 / 371,072 B | 0 |
| VDP1 allocatable payload headroom | 87,416 B | 87,416 B | 0 |
| Protected future sprite reserve | 49,152 B | 49,152 B | 0 |
| VDP2 reserved | 434,176 B | 434,176 B | 0 |
| Phase 2 facade resident cells | 106,496 B / 1664 tiles | same | 0 |
| SCSP high-water / free | 485,812 / 38,476 B | same | 0 |

No VDP1/VDP2/SCSP allocation, CRAM bank, engine limit, compiler pin or Docker base changes. The larger CPU actor arrays are necessary because the actual prior capacity was two. Three enemies add draw work; the current production renderer's 144 mixed CP/Ricky/leap fixtures, with both players and bat/flame/embers/impact, peaked at **45 sprite draws**. This is structural/emulator evidence, not real-hardware frame-time approval.

## Validation

- Native `stage-default`: `PATH=/workspace/mf-host-tools/usr/bin:$PATH bash tools/build-stage.sh --native`; pinned SDK setup ran for this checkout.
- `make check` and `make test`: **PASS**, including the frozen historical suites and current candidate tests.
- Current UBSan tests cover every startup/active/recovery tick of all three combo phases, both heroes, movement, hit/miss, already-landed damage, all three hit-mask bits, buffered A, held B, hit-stop, hurt/death/bat/torch guards, both ports, and all enemy slots attacking/taking damage/KO/retirement.
- At camera positions **0, 320, 640, 960**, solo maximum **2**, co-op maximum **3**. P2 joins mid-combat; P2 disconnects with three actors; no abrupt enemy despawn; replacements stay blocked at two. Corporate Punk and Ricky are exercised in every slot.
- **12,000 solo ticks** compare player/enemy/AI/spawn-RNG/score state byte-for-byte with approved Phase 2. No solo balance drift.
- Current production Phase 2 cache/world/checkpoint/endpoint, Ricky jump-chain, 3HP bat damage, flame contact/charge and punch-combo suites run under UBSan. FF+A runs the existing command-buffer cases; its obsolete OHKO-bat tail is excluded explicitly because the approved baseline already uses 3HP bat damage. Current approved damage tests remain intact.
- The old Phase 1 map fixture uses the pre-Phase-2 chunk format. It runs on its historical source; the current exact Phase 2 cache fixture validates every camera position in both directions. Historical source-preservation suites stay frozen; current candidate behavior has its own tests.
- Two fresh Yabause HLE boots of the production candidate have **zero state/image differences**, **zero runtime errors**, normal X skip/settling/clear/loading/audio-readiness, and **555 shared Level 2 simulation ticks / 545 matching Level 2 images**. See [cold-starts.json](cold-starts.json). The cold-start wrapper resolves the LTO runtime-phase symbol beside its own diagnostic instead of assuming adjacency to the shooter pool.
- Fire/Hit bank, native SCSP allocator/readiness and existing Level 2 audio/runtime regressions pass. This is not a listening-quality or hardware claim.
- Preservation validation compares every baseline file except the specific gameplay/HUD/Makefile changes. Neon Strip artwork, palettes, tilemaps, camera, Ricky controller/art, player damage, music/SFX, Level 2 and approved tags are unchanged.

## Native captures and playable files

All captures come from the production native BIN/CUE in a fresh Yabause HLE boot with physical controller inputs only; no RAM writes or save-state loading.

- [Three enemies in co-op (GIF)](three-enemies.gif) · [native PNG](three-enemies.png)
- [Buck punch → jump (GIF)](jump-cancel-buck.gif) · [punch](p1-punch.png) · [jump](p1-jump.png)
- [Chuck punch → jump (GIF)](jump-cancel-chuck.gif) · [punch](p2-punch.png) · [jump](p2-jump.png)
- [Input/state capture report](report.json) · [sprite memory audit](sprite-memory.csv)
- [Matching playable BIN/CUE archive](../../downloads/mullet-force-coop-three-enemies-jump-cancel.zip), with exact source identity, checksums and licenses. Extract both files together and open the CUE.

## Exact GitHub Actions manual settings

Workflow: **Manual Saturn playtest build** (`.github/workflows/build.yml`).

- **Use workflow from:** `balance/coop-three-enemies-jump-cancel`
- **profile:** `stage-default`
- **source_ref:** the full final candidate branch-head SHA (or `balance/coop-three-enemies-jump-cancel` to resolve its current head)

For the exact implementation/native package build, set `source_ref` to `0f5daa1b82de22fa2050d49673a8ddb4a2462d81`. `MF_PRESERVE_AUDIO=1` is already selected by the workflow/profile. One matching playable artifact is uploaded with one-day retention. No workflow or hosting changes were required.
