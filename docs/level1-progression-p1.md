# Level 1 progression P1

The complete Noah Saturn profile enables `MF_LEVEL1_PROGRESSION` in
`make/saturn.mk`. Historical gameplay profiles retain their existing rules.
The existing developer toolkit workflow selects the complete Noah profile.

## Encounter tuning

Edit the ordered `mf_encounters` table in
`src/level1_progression_config.h`. All coordinates are integer world pixels.
The camera limit is the maximum **left edge** while the encounter is locked;
the player limit is the maximum **fighter center**.

| Encounter | Activation X | Camera limit | Player limit | Restart X | KOs | Spawn delay (ticks) | Pair chance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Opening street | 26 | 1100 | 1279 | 100 | 6 | 90–150 | 25% |
| Intersection | 1280 | 1740 | 1919 | 1570 | 8 | 66–120 | 40% |
| Downhill street | 1920 | 2380 | 2559 | 1950 | 7 | 45–90 | 50% |
| Garage approach | 2560 | 2570 | 2757 | 2640 | 9 | 30–66 | 65% |

Each row defines its name, activation, camera and fighter limits, restart,
quota, spawn delay and jitter, staggered-pair chance, enemy mask, and event
dependency bits. Both Corporate Punk and Ricky are enabled in the initial
rows. The existing class schedule still selects among allowed types. A
paired spawn uses the shared 18–36 tick delay. Placement retries use the
existing 15-tick delay. Counts use player-credited KOs. Vehicle KOs free
slots for replacements. The spawner reserves enough room in the quota for
living enemies and stops when the quota is met. GO appears once dying
enemies retire and any required event finishes. It disappears when a living
fighter enters the next row or Bruce takes over.

Keep the rows in increasing activation order. The opening row starts at
`MF_WORLD_LEFT`. A locked fighter limit must precede the next activation
and be reachable inside the capped viewport. The configuration test checks
camera ordering, fighting space, restart bounds and event placement. The
developer-section tests also exercise the preset positions. When changing
boundaries, update the expected rows and quotas in
`tests/level1_progression_test.c` and run `make test`.

The vehicle trigger stays at X2240. The row covering it must use
`MF_ENCOUNTER_WAIT_VEHICLE` and restart at or before the trigger. Reaching
the downhill quota before the ambush leaves the gate locked until the car
passes are complete. Bruce's approach, lot return, arena lock, music and
bank handoff retain their existing coordinates and rules, including the
existing catch-up to the rear edge when Bruce enters. The last ordinary
gate ends before the arena entrance at X2758.

## Checkpoints and developer controls

The first living fighter to reach the next activation after a clear advances
the encounter. The existing camera tether continues to control visibility
for both players, and the existing floor milestones still govern
backtracking. Local progress survives joining, disconnecting and defeat.
After a disconnect, excess living enemies retire without KO credit on the
next advancing gameplay tick. Already dying enemies finish normally.

Section Select retains its existing landmarks. Opening and ION select the
opening encounter. Intersection selects the intersection. Downhill and
Vehicle select the downhill encounter. Garage selects the garage approach.
Bruce and the apron use their existing fixtures with the ordinary street
encounters already cleared.

Restart during an ordinary encounter uses the row's restart X and resets
that local fight, including the downhill ambush when replaying the downhill
checkpoint. Boss and apron Restart still use the developer section fixtures.
The pause-only Level 2 skip is unchanged. There is no persistent save state.

GO uses the existing text layer. P1 adds no assets or texture uploads and
does not change disc staging, the ISO guard, or VDP2 and SCSP allocations.
