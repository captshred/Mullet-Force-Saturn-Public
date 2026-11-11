# Corporate Punk AI 3.0 — experimental Level 1 tuning

Branch `feature/level1-punk-ai-v3`, based exactly on AI 2.0 commit
`712dbd8e6cb5db4ac3555bed77cb160ec586ee29`. The remote AI 2.0 head was verified
before branching. No approved branch/tag is modified or merged. This preserves
the owner-approved E008 diagnostic development baseline; it does not establish
that E008 was permanently repaired.

## Root causes

There is no player-idle prerequisite. AI 2.0 already initiated legal attacks,
but retained 36/48 ticks of post-attack recovery, up to 42 ticks of hurt plus
hurt-recovery, and a return-only tick after recovery expired. These kept pressure
low even after normal windup dropped to 18 ticks.

The old pursuit was already diagonal whenever both axis thresholds were exceeded.
It independently moved X by 220 and Y by 150 fixed units, stopping horizontal
movement within 40px and depth movement within 4px. With typically smaller depth
distance, Y settled well before X. Identical pursuit rules then funneled both
slots toward the same lane. There was no offset route, preparation or burst.

## Attack and reaction tuning

All values below are 60 Hz simulation ticks; existing impact hit-stop freezes
simulation. Windups remain interruptible. Every pattern, rush and fifth-punch
counter uses the same legal attack gate, checked before pursuit/preparation.
Recovery expiry can evaluate that gate immediately. Spawn grace remains 120;
no random idle delays, movement-only attacks or stun immunity were added.

| Consecutive landed punches on this enemy | Hurt | Hurt recovery | Attack windup |
| --- | ---: | ---: | ---: |
| 0–2 | 12 | 8 | 14 |
| 3–4 | 8 | 4 | 14 |
| 5+ | 6 | 2 | 10 |

Post-attack recovery is 20/26 ticks for slots 0/1; the six active collision ticks
remain unchanged. Actual uninterrupted in-range commitment intervals are
**39/45 ticks (0.65/0.75s)** normally and **35/41 (0.58/0.68s)** for counters,
verified by simulation. Interruption, target movement, spawn grace and hit-stop
can extend those intervals. The existing HQ strike/ready/idle poses are reused
for the compressed recovery: strike on its first tick, ready while timer>12,
then idle. No artwork or loader changes.

AI 2.0 pressure is retained: five distinct landed punches open an opportunity,
not guaranteed damage. Pressure saturates at five and expires 180 ticks after
the last punch. Connected kick/bat clears only the affected slot, while misses
do not. Existing hit masks prevent duplicate counts across overlap frames.
Player damage/recoil code is unchanged: damage 12, hurt 12, initial knockback
650/256px/tick decaying by 3/4, attack/torch/dash/pending-command cancellation,
60 ticks protection, and no automatic knockdown. Multiple commitments remain
possible, with shared invulnerability preventing synchronized double damage.

## Movement patterns and assignment

Walking caps are 300/256px horizontally and 220/256px in depth per tick
(1.172/0.859px), versus 220/150 fixed units in AI 2.0. Depth velocity is scaled
by the approach vector, capped at 220, so enemies move on both axes without
racing to exact Y alignment first. Playfield limits remain X26..614, Y168..229.

- **Brawler:** directly closes using the proportional depth approach. No rush
  preparation; legal attacks always take priority.
- **Flanker:** pursues a depth waypoint offset by 24px, then closes diagonally
  inside 76px horizontal distance. If depth is still offset by more than 9px,
  it prepares a diagonal rush before closing.
- **Ambusher:** holds a 24px offset approach, transitions inside 120px, then
  briefly prepares and rushes when there is a valid diagonal to travel.
- **Opportunist:** captures the opposite of the target's facing for a rear
  waypoint. It aims 72px behind normally, 56px when the player is attacking or
  another enemy is winding up/active against that target. Once 40px behind
  (24px when engaged), it closes, optionally with a prepared diagonal burst.
  A legal attack is never postponed merely to complete a rear route.

A dedicated per-slot LCG assigns patterns and lane signs on successful spawn;
it never consumes the approved stage spawn RNG. A simultaneous pair cannot
have identical assigned types and initially prefers opposite depth offsets.
A deterministic 10,000-spawn sample yielded **2,519 Brawlers (25.19%), 2,472
Flankers (24.72%), 2,497 Ambushers (24.97%), 2,512 Opportunists (25.12%)**.
This is a measured sample, not a fixed quota for each playthrough.

Offsets flip toward usable space near top/bottom bounds. Longer approaches
(>160px away) may switch lane once at a seeded 40–64 pursuit ticks. After 144
ordinary pursuit ticks the enemy abandons the offset waypoint and closes
directly, preventing endless orbiting. Optional opposite 6px depth aims reduce
stacking within 18px X/10px Y; they never postpone a legal attack. Coincident
player/enemy roots receive a bounded movement step to avoid a zero-facing
contact deadlock. There is no body collision/pathfinder or teleportation.

## Prepared rushes

Flankers/opportunists prepare for six ticks; ambushers for 8–10. Preparation
uses the existing ready pose through the windup state, distinguished internally
from a damaging punch windup. It cannot cause damage. A legal opening during
preparation starts a fresh complete punch windup.

Launch captures the current X/Y direction. The burst then runs in that fixed,
nonhoming direction for a planned **10–18 movement ticks**, at **5/3 walking
caps: 500 horizontal / 366 depth fixed units** (1.953/1.430px/tick). Bounds apply
after every step. A legal opening may end a burst early to start a full windup;
arrival never deals damage by itself. Hurt cancels both preparation and burst
and cannot be bypassed. Hit-stop/pause freeze their clocks. No new movement
sound or sound dispatch site was added.

## Validation and preservation

Passed pinned native source build, `make check`, `make test`, and the focused
complete-profile UBSan/warnings-as-errors gameplay suite. It covers immediate
legal attacks including recovery expiry, genuine hit-stun and rush cancellation,
diagonal motion, both depth offsets, all four patterns, exact burst speed and
preparation/duration, fixed launch direction, full post-rush telegraphs and
last-ready-tick interruption, rear approaches, corner/coincident convergence,
pressure counts/resets/expiry, player recoil/protection, and frozen clocks.

All tested stationary pattern/lane scenarios reached a punch commitment within
134 ticks from a 200px horizontal approach. A 50,000-tick repeated simulation
with two moving targets produced identical states on both runs, no negative
clocks and no out-of-bounds enemies. A separate 1,800-tick up/down run for each
pattern uses actual player movement speed and records more than ten legal
attack opportunities per pattern; this verifies opportunities, not unavoidable
hits. It is not emulator evidence. Distribution checks cover 10,000 spawns.

Current FF+A buffering, fast bat, combos, repeat jabs, dash, combat, co-op, torch,
aerial bat and stage-clear suites pass. Existing stage-spawn results remain
1,130 singles / 870 staggered pairs, lane counts 1,391/92/5/512, with the same
40-kill quota and Level 2 transition rules. HQ presentation regression confirms
existing shared uploads and unchanged simulation during rendering.

The preservation gate pins AI 2.0, checks every parent file outside eight scoped
AI/test files, and explicitly freezes shared game.c regions for player commands,
movement, recovery/damage, torch/audio dispatch, targeting/spawn scheduling and
stage transitions. The archived AI 2.0 gate executes its original preservation
locks/regressions; actual AI 3.0 gameplay is tested separately. Experimental
disc resources and newly compiled executable are validated through that chain.
All Level 2 code, startup diagnostics, music/Fire/Flame/SFX scheduling, Level 1
audio, artwork, assets/manifests, player input and workflow files remain exact.

Inherited optional skips remain: historical dual-boot allocation comparison
without its staged build, and archived native-driver/allocator checks without
their driver fixture. No unresolved test failures. No emulator/controller or
physical Saturn validation is claimed for AI 3.0.

## Files and cost

Modified: `src/game.c`, `src/game.h`, `src/combat_config.h`,
`src/corporate_animation.c`, `tests/punk_ai_test.c`,
`tests/corporate_hq_test.c`, `tools/test-punk-ai.py`,
`tools/validate-punk-ai.py`. Added: `tests/punk_ai_v3_test.c` and this report.
No Makefile, workflow, asset or SDK/compiler pin changes.

Matched native AI 2.0/3.0 builds: executable **243,296 → 245,904 bytes (+2,608)**;
linked BSS **0x663a4 → 0x663f4 (+80)**. Added per-game AI state is **72 bytes**;
the additional eight BSS bytes are linker alignment. Full-profile mf_game is
748 bytes. Player/enemy render struct layouts remain unchanged. No additional
VDP1/VDP2/CRAM/SCSP allocation, texture definition, disc read or heap allocation.
The two-slot update has bounded integer work, including one variable integer
division per ordinary walking enemy. No searches, unbounded loops or per-frame
random assignment. Hardware cycle/frame-time performance is not measured.

## Playtest limits and build instructions

These checks establish deterministic behavior and preservation, not feel or
hardware timing. The ready pose signals both preparation and punching, so the
visual distinction is subtle. Fixed-direction bursts can be dodged and precise
jabs can still interrupt counters; a six-HP punk may die before using fifth-hit
eligibility. Rear routes can be abandoned near walls or moving targets. There
is no physical enemy collision, so separation reduces rather than eliminates
stacking. Aggression may need controller tuning, especially ten-tick counters
and simultaneous telegraphs. Horizontal kiting remains possible; there is no
promise of guaranteed damage against constant movement.

Local: `bash tools/setup.sh`, `bash tools/build-stage.sh --native`, `make check`,
`make test`. On this cloud host prefix PATH with
`/workspace/mf-host-tools/usr/bin` for the previously installed genisoimage.

After push: **Actions → Manual Saturn playtest build → Run workflow**. Select
workflow branch `feature/level1-punk-ai-v3`, profile **stage-default**, and
`source_ref` equal to the full AI 3.0 commit SHA reported with delivery
(`git rev-parse HEAD`). Download `mullet-force-stage-default-<SHA>` within its
one-day retention; keep the matching BIN, CUE and checksums together and open
the CUE. Do not select an older baseline tag or the Level-1-only build profile.
No Actions dispatch or baseline merge is performed by this task.
