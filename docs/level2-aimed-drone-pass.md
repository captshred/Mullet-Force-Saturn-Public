# Level 2 flame origin and snapshot-aimed drone fire

Branch: `feature/level2-aimed-drone-pass`.
Parent: confirmed playable `f94c7721ef0d846ee618d44b006040477d063328`
(`feature/level2-flame-tuning-pass2`).

## Ignition artwork and rendering

Four new **32x16 RGB555 origin frames**, `WFO0.BIN` through `WFO3.BIN`, replace
only the bottom sixteen pixels of the visible beam. Each begins with a stable
three-pixel-wide hot core at the unchanged emitter (player center X, center Y
minus 15). Rounded smoothstep shoulders bloom upward into the corresponding
21..25-pixel flame-body row. Slight internal edge motion distinguishes all four
phases while their emitter remains centered at texture X=16.

The top cap row exactly matches the adjoining body tile's bottom row, including
colors and transparency, in every phase. Existing body textures remain byte-for-byte
unchanged: 32x32, average visible width 23 pixels, organic constant-width profile,
no upper tip. The cap uses the same frame index as its player's body: one frame
per three simulation ticks, four phases, Chuck offset by one phase.

The renderer draws one cap ending at the emitter, then repeats the existing body
upward from the cap's top until it reaches or passes Y=0. No body is drawn behind
the narrower cap. Rows meet contiguously, without a gap or overlapping seam. The
existing VDP1 system clip trims whichever tile crosses the top. Both cap and body
use the original restored SGL path, Z=100, original player coordinates and banking.

| Player Y | Emitter Y | Cap top Y | Body commands | Total flame commands/player |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 1 | -15 | 0 | 1 |
| 32 | 17 | 1 | 1 | 2 |
| 47 | 32 | 16 | 1 | 2 |
| 64 | 49 | 33 | 2 | 3 |
| 128 | 113 | 97 | 4 | 5 |
| 200 | 185 | 169 | 6 | 7 |
| 223 | 208 | 192 | 6 | 7 |

This change is visual only. The beam collision block is pinned byte-for-byte to
the parent: from Y=0 through the emitter, half-width 11 pixels plus existing drone
half extents, one damage pulse on activation and every six held simulation ticks.
The origin's visual taper does not shrink that hitbox or change DPS. Focus still
requires 20 held ticks and uses 65% movement speed. Release, tap spread, diagonal
normalization, damage, scoring and death audio remain unchanged.

## Snapshot-aimed drone fire

Drone movement, spawn cadence and age-80 firing time remain unchanged. Immediately
after the drone's usual movement on its firing tick, its muzzle remains `(x,y+10)`.
The targeting policy samples the current hero positions exactly once:

1. Consider heroes with `active != 0`, `lives > 0`, and `respawn == 0`.
2. Compare exact squared 24.8 distances from that muzzle using 64-bit integers.
3. Choose the nearer hero. Exact ties select Buck/P1, through strict comparison
   in player-index order. Invulnerability does not disqualify a present hero.
4. If neither hero is eligible, emit no projectile. A disconnected controller
   does not remove its still-visible active hero from the existing simulation;
   that hero remains eligible. Respawning/absent and inactive heroes are ignored.
5. Normalize the chosen vector, store its X/Y velocity, and emit into the existing
   sixteen-slot hostile pool. A full pool safely drops the shot without overwriting
   any active projectile.

Let `dx,dy` be the integer 24.8 displacement and `d2=dx*dx+dy*dy`. The target speed
remains **768/256 = 3 pixels per simulation tick**. An integer shift/subtract square
root gives `L=floor(sqrt(d2 << 16))`; velocities are
`vx=trunc(dx*768*256/L)` and `vy=trunc(dy*768*256/L)`.
The extra eight fractional length bits prevent small diagonal vectors from becoming
faster. A zero displacement uses the deterministic fallback `(0,768)`.
There is no runtime floating-point math. Legal stage coordinates keep all products
and the precision shift safely inside 64-bit bounds.

Cardinal shots remain exactly 3 pixels/tick. Tests cover all octants and subpixel
vectors, requiring magnitude within **2/256 pixels/tick** of 3. Normalized diagonal
speed therefore remains approximately equal to vertical speed.

**Aiming occurs only at emission. Shots do not home.** Subsequent physics simply
adds the stored velocity to position. It never reads the target position or
recomputes direction. The retained owner field records the selected target index;
it does not guide the projectile. Bullets can still hit either living hero that
crosses their fixed trajectory.

`emit_hostile()` accepts a generic velocity. The drone's separate
`aimed_snapshot()` policy implements the conceptual `AIMED_SNAPSHOT` pattern.
Future fixed shots or fans can provide different velocities to the same emitter
and physics. No pattern registry, fan, burst, sweep or homing behavior is added.

Hostile cleanup now covers all directions: X outside `[44,275]`, Y outside
`[-8,248]` pixels, or the existing 120-tick TTL. These bounds include a small
margin beyond the gameplay field so fully departed sprites release their slots.
No extra projectile pool or per-frame allocation is introduced.

## Exact resources

| Resource | Parent | This pass | Change |
| --- | ---: | ---: | ---: |
| New origin frames | 0 | 4 x 32x16 RGB555 | +4 definitions |
| Origin texture payload | 0 B | 4,096 B | +4,096 B |
| Total VDP1 texture payload | 23,936 B | **28,032 B** | +4,096 B |
| Total VDP1 definitions | 14 | **18** | +4 |
| Worst flame commands/player | 7 | **7** | 0 |
| Worst two-player flame commands | 14 | **14** | 0 |
| Worst object commands, all pools | 72 | **72** | 0 |
| Player / hostile / drone pools | 32 / 16 / 8 | **32 / 16 / 8** | 0 |
| Simulation state | 1,420 B | **1,484 B** | +64 B |
| VDP2 reservation | 434,176 B | **434,176 B** | 0 |
| Background cells/map payload | 10,944 B | **10,944 B** | 0 |
| CRAM payload | 32 B | **32 B** | 0 |
| SCSP bank data | 31,788 B | **31,788 B** | 0 |
| SCSP reserved high-water | 180,652 B | **180,652 B** | 0 |
| `/ALEVEL2` logical file payload | 66,740 B / 20 files | **70,836 B / 24 files** | +4,096 B / 4 files |

Hostile projectiles now have their own 28-byte record: existing fields plus Y
velocity, while the 32 player-projectile records remain 24 bytes. Sixteen extra
four-byte Y velocities account for exactly +64 B. Texture-ID bookkeeping gains
16 B separately. Integer targeting uses temporary stack locals only at firing;
there is no persistent target/pattern allocation or new sound buffer.

The command maximum remains 2 players + 32 spread + 16 hostile + 8 drones or
explosions + 14 flame commands = 72. The cap replaces part of the tile run, so
worst-case command count does not grow. This stays inside the pinned SGL allocation
of 1,761 polygons and Jo's 255 texture definitions without enlarging any buffers.

Canonical death audio and SCSP loading are unchanged: SEQ 44 B, TON 31,744 B, MAP
40 B; lower driver/work reserve through 148864, sequence at 148864, tone at 148908,
end 180652 of 524288 B. The linked 26,610-byte driver remains in the lower reserve.
Native code-size and generated stack usage await compilation with the pinned SDK.

## Preservation and validation

`docs/aimed-drone-preservation.json` pins **all twenty parent stage payloads**,
unchanged game/main/input/dev-skip/audio/workflow sources, and the original beam
collision block. No approved hero, body tile, background, drone, spread, hostile
or explosion texture changes. Existing Level 1 locks and earlier flame/hero/audio
checks remain active. No source-preservation exception or baseline hash is relaxed;
this pass does not need a protected-source hash update.

The host suite covers the normal forty-kill Stage Clear, X shortcut/handoff,
full-profile Level 1 equivalence, banking, /ALEVEL2, restored SGL state, exact
canonical death SFX and stray-T erase. New tests cover:

- Four distinct compact origin phases, centered three-pixel hot emitter,
  monotonic smooth bloom, exact cap/body seam and unchanged body/collision bytes.
- Real renderer attachment and row-by-row full-height coverage at seven player
  heights and all animation phases; release removes cap/body; all pools and two
  beams submit at most 72 commands through the initialized SGL path.
- Real age-80 firing/muzzle, vertical/down-left/down-right shots, magnitude across
  16,641 subpixel vectors and 1,089 larger vectors, zero-distance fallback.
- Nearest living active nonrespawning target, exact ties, subpixel distance
  differences, no eligible target, and existing disconnected-hero presence.
- Unchanging velocity and exact linear position after hero movement, full-pool
  non-overwrite, generic non-aimed velocity emission, four-edge/TTL cleanup and
  repeated emission/cleanup stress.
- Exact 24-file ISO stage layout, missing/incorrect-length errors for every new
  cap, partial-load cleanup, unchanged parent assets and no gameplay file I/O.

`make test` passed with **214 PASS reports**. It also runs the actual aiming/simulation/weapon/flame/audio/runtime
regressions with UBSan and abort-on-error. The movement-boundary fixture suppresses
automatic spawns while checking movement alone; unlike the old down-only shots,
aimed bullets can now legitimately hit a hero waiting at the top.

Static checks: `python3 tools/validate-wingsuit.py`, `tools/validate-arcade-fx.py`,
`tools/validate-full-gameplay-sfx2.py`, `tools/validate-sfx2.py`,
`tools/check-public.py`, `tools/check-city-neon.py`,
`tools/check-gameplay-parallax.py`, `tools/check-city-cleanup.py` (each with python3).
Shell syntax, Python compilation and `git diff --check` are also checked.

Native compilation remains blocked: `tools/setup.sh` cannot connect to the configured
proxy on port 8080 to fetch the pinned SDK. No new BIN/CUE, WebRetro/emulator run,
audio listening, or real-Saturn validation is claimed. The user's confirmed playtest
is for the parent. ISO tests here use structural fixtures, not a new compiled disc.

## Exact manual Actions settings

Open **Manual Saturn playtest build** (`.github/workflows/build.yml`):

- **Use workflow from:** `feature/level2-aimed-drone-pass`
- **profile:** `stage-default`
- **source_ref:** full new commit SHA provided with delivery. The branch name also
  resolves to it until further commits.

The unchanged workflow is manual `workflow_dispatch` only. No Actions run is
triggered by this change. Download `mullet-force-stage-default-<full SHA>` and keep
its BIN/CUE together. BUILD-INFO must show that same SHA, `Level 2 wingsuit: 1`,
and `Dev Saturn X stage skip: 1`.

Local build when x86-64 Linux prerequisites and the pinned SDK are available:

```sh
bash tools/setup.sh
bash tools/build-stage.sh --native
make check
make test
```

Release controls: `MF_DEV_STAGE_SKIP=0 bash tools/build-stage.sh --native`.
Playtest normal forty-kill and X entry, both hero banks, cap/body seams while
moving/holding/releasing, nearest-player aiming and baiting after launch, diagonal
speed, all four bullet exits, unchanged death sounds, pause/restart and HUD.
