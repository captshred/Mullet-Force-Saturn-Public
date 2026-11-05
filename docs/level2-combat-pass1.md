# Level 2 combat and sprite pass 1

Development branch: `feature/level2-combat-pass1`.
Parent: the preserved `level2-playable-baseline` commit
`4c7ca6a0e0e9a69930a39f3416a12dd8a3391753`.
The player confirmed that baseline as playable. This new combat/art pass has
host validation only; it has not been played on Saturn or in an emulator here.
No GitHub Actions run has been launched.

## Weapon and movement tuning

Each controller has an independent, saturating shot-hold counter. The first shot
is immediate; it does not wait for hold classification. A tap fires a three-shot
fan. Continuing to hold A for 12 simulation ticks (0.20 seconds at 60 Hz) changes
to focused fire. Releasing A immediately returns to mobile movement. Press edges
latched between VBlanks can still produce a tap burst even if A is already up.

| State | Cardinal movement | Diagonal components | Attack |
| --- | ---: | ---: | --- |
| Normal / mobile tap | 640/256 = 2.5 px/tick | 452/256 each | Three-way fan on a fresh press |
| Focused hold | 531/256 = 2.07421875 px/tick | 375/256 each | Narrow two-shot stream every five ticks |

Focus uses an 83% multiplier with integer rounding (82.96875% of cardinal mobile
speed), a conservative 17% reduction. Both movement modes retain normalized
diagonals with the same small fixed-point rounding error as the baseline.
The normal/tap movement rate and player bounds are unchanged.

The mobile fan starts at X offsets -4, 0, +4 pixels. Its horizontal velocities
are -1, 0, +1 pixel per tick; all player shots travel upward at six pixels per
tick. Fresh taps have a minimum seven-tick repeat interval. Holding A does not
repeat wide fans: the initial fan changes to the sustained focus stream after
the hold threshold. Focus emits at X offsets -3 and +3 pixels with zero sideways
drift, concentrating more shots along the forward line. These are distinct
coverage and central-density behaviors; per-projectile damage is unchanged.

Both modes reuse the existing shot texture and fixed 32-slot player-shot pool.
Each burst is allocated atomically: if all two or three slots are unavailable,
the complete request is dropped without overwriting a live object or allocating
memory. Failed requests do not consume the firing cooldown. Horizontal cleanup
keeps spread sprites out of the side HUD; TTL and upper-screen cleanup remain.
Freed slots get a fresh velocity on reuse. Hostile shots keep zero horizontal
drift, and drone entry, movement, firing, scoring and damage behavior are intact.

Disconnecting cancels that player's hold state; pause freezes firing clocks.
Respawn and game-over restart clear the hold state and preserve the existing
join, lives and invulnerability behavior. There are no new bombs, upgrades,
pickups or audio systems.

## Sprite pass

The new runtime art remains native pixel art at the same dimensions:

- Buck: 32x32, brighter silver panels, shaded wing folds, harness/belt details,
  red trim and a broad silhouette. Three warm hair locks trail behind his head.
- Chuck: 32x32, leaner wing outline, black/navy panels with cool rim lighting,
  cyan trim and distinct golden-brown trailing hair.
- Corporate drone: 24x24, four detailed rotor rings, structural struts,
  chamfered metal plating, a red sensor and small hazard markings.
- Player shot: 8x8, white-hot core, warm tail and a light cyan edge.

The native RGB555 hero textures use 17 colors including transparency, versus
10 before; the drone uses 19 versus seven. The stronger silhouettes and larger
hair locks are intentional at the same small footprint. One strong facing-up
frame per hero is used; banking frames would add resources for limited benefit
in this pass. Enemy-shot and explosion art remain unchanged.

Only WBUCK.BIN, WCHUCK.BIN, WDRONE.BIN and WSHOT.BIN change, plus their exact
manifest hashes. Their byte lengths do not change. The generator reproduces the
committed runtime payloads and writes review exports only into `work/`.
No private art masters, image archives or review exports are committed.

## Resource accounting

These are exact payload/pool/struct counts, not new hardware telemetry.

| Resource | This pass | Delta from playable baseline |
| --- | ---: | ---: |
| VDP1 texture allocation | 7,552 bytes | 0 |
| Texture definitions | 6 | 0 |
| Buck / Chuck / explosion | 2,048 bytes each | 0 |
| Drone | 1,152 bytes | 0 |
| Player / hostile shot | 128 bytes each | 0 |
| VDP2 SDK + arena reservation | 434,176 bytes | 0 |
| Stage cell/map payload | 10,944 bytes, 43 tiles | 0 |
| Stage cell/map arena reservation | 172,032 bytes | 0 |
| Stage CRAM payload | 32 bytes | 0 |
| SCSP loaded stage resources | 0; sound CPU remains halted | 0 |
| Player shots / hostile shots / drone slots | 32 / 16 / 8 | 0 |
| Maximum shooter object draw commands | 58 | 0 |
| Shooter simulation struct | 1,408 bytes | +200 bytes |

The extra work RAM is two per-player hold counters (eight bytes) plus one
horizontal-velocity integer in each of the 48 pooled shot records (192 bytes).
The existing integer-only renderer and fixed pools are retained; there is no
per-frame allocation or asset upload. Overall linked RAM, stack high-water
marks and frame time await a native build/profile.

Stage-specific loading is unchanged: the same nine files are loaded from
`/ALEVEL2`, the root-directory limit repair remains intact, and the exact
known-good VDP1/SGL handoff code is byte-for-byte unchanged. The industrial
background payloads and scroll logic, Level 1 gameplay/art/audio, stage-clear
flow, native build configuration and workflow are also unchanged. No source
preservation hash exception or validator bypass was needed.

## Validation

The full `make test` exits 0 with 187 PASS reports. The focused weapon tests
cover exact mobile/focus speeds, the hold threshold, both diagonal speeds,
repeated taps, narrow-stream cadence and drift, independent two-player modes,
latched press edges, disconnect, atomic burst exhaustion, slot reuse,
horizontal/TTL cleanup, pause and restart. The existing 100,000-tick shooter
stress test remains enabled.

The weapon and real runtime/render tests pass UBSan. Existing stage-clear,
SFX2/art/audio/source preservation, RGB555 resource budgets, VDP1 initialization,
load-failure handling and ISO directory/content/staging tests pass. Of the 633
baseline asset blobs, 628 remain byte-for-byte unchanged; only the four listed
Level 2 sprites and their manifest differ. All Level 1, loader/SGL, background,
staging and build source checks against the playable parent pass.

Pinned SDK setup and the native build attempt both fail because the configured
shell proxy at port 8080 is unreachable. No new native BIN/CUE or emulator /
hardware validation is claimed. Native `make check` against a new complete disc,
CRT readability, actual controller feel and hardware frame timing remain open.
The baseline's confirmed playability does not establish those results for this
new tuning pass.

## Manual build

On a build-capable x86-64 Linux checkout of the delivered branch/commit:

```sh
git switch feature/level2-combat-pass1
bash tools/bootstrap.sh
make clean
bash tools/build-level2-wingsuit.sh --native
make check
make test
```

The output pair is `build/mullet-force.bin` and `build/mullet-force.cue`. Keep
both files together and open the CUE (MODE1/2048).

For an explicitly requested manual Actions build, open **Manual Saturn playtest
build**, use workflow branch `main`, select profile `stage-default`, and set
`source_ref` to this branch or the exact delivery SHA. The unchanged workflow
checks out that source, uses its stage wrapper, validates the disc and runs the
host suite, then packages one matching BIN/CUE artifact with one-day retention.
No workflow change or automatic trigger is added by this branch.

For playtesting, complete Level 1's 40-KO path, confirm transition and background,
compare mobile taps against a sustained hold on each controller, release focus
while moving diagonally, exercise two simultaneous streams, and check damage,
respawn and restart. Tune the constants in `src/wingsuit.h` only if controller
feel justifies it; preserve the baseline branch for comparison.
