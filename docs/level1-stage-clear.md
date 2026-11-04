# Level 1 stage clear

THE ONE is the independently playable approved commit
`8d79a36f97dfd0b02de7d1b6b58e85b16fdc0b96` (arcade-impact-fx).
Only `feature/level1-stage-clear` enables the new gameplay through
`tools/build-level1-stage-clear.sh`. The ordinary arcade profile retains its
original gameplay and ABI; the new fields and logic are compiled out by default.

## Encounters

The simulation is 60 Hz. The previous respawn was 480 ticks (8 seconds), plus
the 30-tick death animation. A shared scheduler now fills free slots, with a
maximum of two enemies including dying enemies. It never replaces a live enemy.

| Shared defeats | Normal arrival interval | Chance of staggered pair when both slots free |
| --- | --- | --- |
| 0–9 | 90–150 ticks / 1.50–2.50 s | 25% |
| 10–19 | 66–120 ticks / 1.10–2.00 s | 40% |
| 20–29 | 45–90 ticks / 0.75–1.50 s | 50% |
| 30–39 | 30–66 ticks / 0.50–1.10 s | 65% |

The first arrival is at 60 active ticks. A pair's second arrival is 18–36 ticks
(0.30–0.60 s) later, subject to a free slot and safe placement. The normal timer
runs while fighting, so a freed slot can refill while the other enemy remains
alive. Death animation residency and placement retries can extend intervals.
There cannot be a third arrival while both slots are occupied.

Entrances sample camera-relative left/right boundaries, clamped to the world,
and top/bottom street boundaries. Four lanes are 168, 188, 209, and 229. Placement
maximizes distance from both living players, requires horizontal separation of
80 pixels or depth separation of 40 pixels, and a weighted separation of 110.
Another occupied slot must be at least 48 weighted pixels away. Unsafe placement
retries after 15 ticks. Existing 120-tick attack grace and AI windup remain.
These are host-verified fairness constraints; emulator/hardware feel is untested.

## Quota and transition

Only an existing lethal damage edge credits a Corporate Punk defeat, including
jab, kick, bat, torch and burn paths. Both players share the total. Despawn,
respawn, barrels and special-class enemies give no credit. At exactly 40, no
new damage or spawns are initiated, even for another lethal candidate in the
same frame. The original impact/SFX events are preserved for that frame.

`LEVEL1 -> SETTLING -> CLEAR -> LEVEL2_ENTRY` is explicit game state.
Settling lasts 60 non-hitstop simulation ticks; the existing 30-tick enemy death
animation, strike and airborne landing finish. Remaining enemies freeze and need
not be defeated. STAGE CLEAR displays for 120 ticks, then LEVEL 2 / COMING NEXT
remains visible. Pause stops both transition timers. HP, score, active coop
players, camera and resource residency persist. The placeholder deliberately
keeps the current scene loaded and has no shooter gameplay or reset operation.

## Resources and future stage banks

No runtime asset files, textures, sprite definitions, samples or allocation
calls change. Expected residency stays VDP1 452800/458488, definitions 255/255,
VDP2 434176/524288 and SCSP 432308/524288. Enabled `mf_game` adds five 32-bit
integers and one 32-bit RNG, 24 bytes; timing/lane tables add 64 bytes of constant
data. Native text/rodata/linker deltas require the pinned SH-2 build and are not
measured in this environment. Disabled ABI is unchanged.

The current application has no validated stage resource-bank lifecycle.
`animation_preview.c` caches sprite IDs, `last_resource`, loaded flags and tail
allocation information; Corporate Punk and player rendering retain those IDs.
VDP1 definitions include views sharing root storage, so freeing an individual
sprite is insufficient to prove reclaiming the texture tail. VDP2 street and
parallax also retain readiness flags and fixed memory-map ownership. SCSP/music
have a separate resident allocation plan.

Separate per-stage banks are a reasonable future design, but are NOT safe to
activate with the current loaders unchanged. Before implementing them, inspect
the pinned SDK's documented release APIs, quiesce every draw/callback, wait until
SGL/VDP1 have finished all referencing commands, and explicitly invalidate every
cached ID, view, loaded flag and allocator cursor. Retain a precisely budgeted
persistent bank, or unload/reinitialize the full stage-owned suffix in reverse
order if supported by the pinned allocator. Reload against preflighted texture,
definition, CRAM, VDP2, SCSP and work-RAM budgets, use generation-checked handles,
and test partial failures and stage re-entry. Do not invent a reset API or call
core initialization twice. A complete engine rebuild and hardware/emulator
validation are required before shipping any such lifecycle. This milestone
performs none of those operations.

## Build and verification

Actions -> Manual Saturn playtest build -> Run workflow, use workflow branch
`main`, source ref `feature/level1-stage-clear`, profile `level1-stage-clear`.
The workflow resolves the ref once to HEAD's exact SHA, records it in BUILD-INFO,
runs the allowlisted script, checks the disc, runs tests and packages matching
BIN/CUE, licenses and checksums with one-day retention. No push/PR trigger exists.
Use an exact commit SHA in source ref to reproduce a particular build.
`stage-default` is a stable interface whose checked-in tools/build-stage.sh can
change on future stage branches without altering the Actions input choices.

Local: bash tools/bootstrap.sh; bash tools/build-level1-stage-clear.sh --native;
make check; make test. Fresh setup failed here because the shell proxy refused
connections. No native BIN/CUE or emulator/hardware playtest is claimed.
The connector's decoded retrieval corrupted five binary files; blob hash checks
rejected them, so local all-asset/disc checks cannot pass. Remote commits retain
all approved asset objects directly from the approved Git tree.
