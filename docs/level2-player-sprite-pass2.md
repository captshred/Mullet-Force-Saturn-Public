# Level 2 player sprite pass 2

Branch: `feature/level2-player-sprite-pass2`.
Parent: `feature/level2-combat-pass1` at
`82e72285dbe82eca1eea6e880fbc90b73bee4c35`.
No protected branch or earlier combat branch is modified. No Actions run was
launched. This pass has host validation; no new Saturn/WebRetro playtest is
claimed.

## Stray T root cause

The normal-play path wrote 18 spaces over the 19-character game-over prompt
`1P START TO RESTART`. Its final T remained at text column 28, row 16, including
when paused after restarting. This matches the isolated letter's location over
the playfield in the supplied screenshot. It was stale NBG0 HUD text, not a
background tile, uninitialized string, diagnostic marker or sprite texel.

The renderer now writes the same fixed-width 19-character field for both states
with `jo_print()` and equal-width prompt/clear constants. A compile-time
size assertion prevents the original width mismatch from returning. The restart prompt remains available during
game over. The normal HUD, P2 join prompt and PAUSED/GAME OVER labels are intact.
The host text-grid regression renders game over, restarts through the real
simulation's Start path, and checks every cell through the old trailing T. It
then renders pause and confirms both the empty prompt field and legitimate HUD.

## Screenshot-guided art

The previous sprites had a long central hair column obscuring the torso and
legs. At the supplied playfield scale, that competed with the human silhouette.
The new 32x32 sprites have a separate small head and neck, defined shoulders,
exposed hands, folded wingsuit panels, a visible chest/harness/belt, and two
separate thighs and boots. The mullet trails behind the neck to mid-back rather
than covering the whole lower body.

Buck keeps a broad, bright silver suit with warm hair and red seams. Chuck is
leaner, black/navy with cool rim lighting, golden-brown hair and cyan seams.
The native pixel footprints remain 32x32, with no change to collision geometry,
render anchors or gameplay position. No oversized replacement or side-view turn
is used. Drone, player/hostile bullets, explosion and background art are exactly
the combat-pass-1 payloads.

Each hero has center, left-bank and right-bank assets. Banking lowers the wing
on the turning side, narrows/raises the opposite wing, shifts the torso slightly
within the same canvas and sweeps the hair outward. The two sides are separately
drawn using pose geometry and asymmetric lighting/seams; neither is a bitmap
mirror of the other. The generator emits all six native player poses, and a
nearest-neighbor review strip in `work/` for inspection. Review exports and
private art masters are not committed.

## Selection and loading

Gameplay simulation files `src/wingsuit.c` and `src/wingsuit.h` are unchanged.
The runtime records each player's X before a simulation step, then selects a
pose from actual displacement and that controller's horizontal direction.
Vertical-only, opposed left+right input, no motion at a clamp, pause,
disconnection, respawn/death and restart select center. Left/right diagonals
select the corresponding bank. Each player chooses independently. Focus/tap
weapons, speeds and timing are unchanged.

Only two integer presentation states are added. Existing texture IDs 0 through
5 retain their roles; left/right Buck use 6/7 and left/right Chuck use 8/9. One
pose is drawn per player through the same corrected Jo/SGL path. There is no
per-frame upload, new simulation state machine, dynamic allocation or extra
object draw per player.

All four new 2,048-byte textures are appended to the stage-owned bank and loaded
from `/ALEVEL2`, bringing its file count from nine to thirteen (15 directory
records including dot entries, still far below 256). The exact directory-order
and payload validation now checks all thirteen. The stage helper stages and
cleans the complete thirteen-file bank, including reused build trees. All new
poses participate in missing/short-file failure tests and bank cleanup.
VDP1 quiescence, SGL initialization, VDP2 scheduling and directory restoration
retain their existing behavior.

## Resource accounting

| Resource | Pass 2 | Change from combat pass 1 |
| --- | ---: | ---: |
| VDP1 textures | 15,744 bytes | +8,192 |
| Texture definitions | 10 | +4 |
| Player poses | Six 32x32 RGB555 textures | Four new banking poses |
| VDP2 reservation | 434,176 bytes | 0 |
| VDP2 cell/map payload | 10,944 bytes / 43 tiles | 0 |
| Stage CRAM payload | 32 bytes | 0 |
| SCSP loaded resources | 0; sound CPU halted | 0 |
| Player/hostile shots and enemy pools | 32 / 16 / 8 | 0 |
| Maximum shooter object draw commands | 58 | 0 |
| Shooter simulation state | 1,408 bytes | 0 |

Presentation state adds eight bytes for two bank selections; the texture-ID
array grows by sixteen bytes. Constant pose/load metadata also grows slightly.
The largest temporary asset read remains the 8,192-byte map. These are exact
payload/pool/field counts, not linked RAM/stack/frame-time measurements.

## Validation

The complete host `make test` passes with 188 PASS reports, including the
unchanged weapon/movement and 100,000-tick stress regressions. Runtime tests
exercise all six poses, independent left/right movement, vertical/opposed input,
bounds, diagonal focus movement, pause/disconnect centering, the actual restart
HUD clear, all thirteen asset reads and failures, and SGL draw-state restoration.
Runtime UBSan, approved art/audio/source preservation, stage-clear tests and
exact ISO/staging fixtures pass.

Byte comparisons against the parent confirm that Level 1, combat simulation,
background, drone/bullets/explosion, stage transition, build/workflow and
source-preservation locks remain unchanged. No preservation exception or hash
bypass was added. Resource validators were updated for the four explicitly
requested player textures and the enlarged stage bank.

Native setup/build still fails because the configured SDK proxy is unreachable.
A new native BIN/CUE, actual CRT readability, banking feel and the cleared HUD
on Saturn/WebRetro remain to be verified. Host text/render mocks do not establish
hardware pixel output.

## Exact manual build

On an x86-64 Linux checkout with working SDK/package networking:

```sh
git switch feature/level2-player-sprite-pass2
bash tools/bootstrap.sh
make clean
bash tools/build-level2-wingsuit.sh --native
make check
make test
```

Keep `build/mullet-force.bin` and `build/mullet-force.cue` together; open the CUE.
For a manually requested Actions build, use **Manual Saturn playtest build**,
workflow branch `main`, profile `stage-default`, and source_ref set to this
branch or the exact delivered commit. No workflow edit or automatic run is
needed. Verify both controllers' center/left/right poses, vertical movement,
focus/tap combat, the 40-KO transition and game-over/restart/pause with no stray T.
