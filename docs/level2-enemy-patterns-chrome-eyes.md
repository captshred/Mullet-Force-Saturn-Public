# Level 2 enemy patterns and Chrome Eyes

Base: approved night palette `42307e1e4b8946443349bc443c8aeec31a267385`.
Branch: `feature/level2-enemy-patterns-chrome-eyes`.

Drone groups now select diagonal, staggered descent, crossing, curved approach,
and short lateral sweep patterns from a deterministic five-pattern shuffle bag.
Each occurs once per bag; boundary repeats are excluded. Diagonals alternate
sides. Three drones arrive 14 ticks apart. Their 24x24 art, one-hit destruction,
score, contact conventions and single age-80 aimed snapshot remain intact.
There are fewer drone emitters per minute than in the original 45-tick spawner.

Every fourth formation is a chain of 6–8 Chrome Eyes. Eight is the existing safe
pool ceiling; ten would exceed it. No pool increase and no simultaneous chains
or overlapping drone groups. Initial delay stays 60 ticks, drone formation
interval is 270 ticks, eye interval 340; busy slots/death effects defer spawning
by 15 ticks. Pause freezes paths; restart resets state and the fixed LCG seed.

Chrome Eye uses one shared, hand-authored 16x16 RGB555 texture: steel-blue shell,
dark outline/lens, cyan pupil and bright upper-left metallic reflection. It has
one static frame, no firing frame and no projectile emitter. The sprite is
embedded in `chrome_eye_data.h`, avoiding an additional CD file/read/heap load.
Its 512 bytes are copied once through the normal Jo texture registration API.
Existing explosions, scoring, hit effects and contact damage are reused.
Standard shots destroy each eye independently; smaller collision extents match
its smaller body. Existing drone collision extents remain unchanged.

Each member samples the same analytic path at an immutable 18-tick offset;
negative local time queues the tail above the top. Y advances 352/256 pixels per
tick, giving 24.75px vertical separation. X uses a 17-entry quarter-sine table
with integer linear interpolation, mirrored over a 1024-unit cycle. No floats,
trigonometry library, history buffer, allocation or player chasing. Destroyed
members never influence another member's age, index or origin.

| Eye variation | X amplitude | Phase units/tick |
|---|---:|---:|
| S-Snake | 66px | 5 |
| Wide Sweep | 86px | 3, starts at side extremum |
| Tight Weave | 36px | 10 |

Adjacent eye formations choose one of the other two variations, with seeded
left/right mirroring and 6–8 members. Origin is the current view center, frozen
at spawn. All paths fit within the 224px spawn viewport and the 320px world at
either camera extreme; later camera movement projects world coordinates through
the unchanged camera/clipping path. Y>256 despawns members even if later hidden
by camera movement. No formation can accumulate indefinitely.

| Resource | Approved night | Enemy pass |
|---|---:|---:|
| Enemy slots / player shots / hostile shots | 8 / 32 / 16 | unchanged |
| Mutable Level 2 state | 1,492 bytes | 1,672 bytes (+180) |
| VDP1 textures | 28,032 bytes | 28,544 bytes (+512) |
| VDP1 definitions | 18 | 19; Chrome Eye ID18 |
| Max sprite submissions / user clip | 72 / 1 | unchanged, 73 total |
| VDP2 payload / reservation | 65,792 / 434,176 bytes | unchanged |
| VDP2 unreserved headroom / CRAM payload | 90,112 / 32 bytes | unchanged |
| SCSP high-water / free | 307,260 / 217,028 bytes | unchanged |
| Level 2 CD files / payload | 26 / 252,292 bytes | unchanged |

The original ID0–17 mapping remains stable. The SDK definition/picture tables
remain statically sized at 255; no increase to table or command capacity. The
shared sprite adds no per-eye texture allocation or extra draw command relative
to an occupied drone slot. The lookup table adds 34 read-only CPU bytes in
addition to the embedded 512-byte sprite and generated code. No VDP2 or SCSP
allocation, audio source/bank, SDK/compiler pin or workflow changes.

Preservation uses an additive `level2-enemy-lock.json` from the exact approved
night parent; older locks are unchanged. All existing runtime asset bytes,
Level 1 modules, audio, transitions and workflow remain frozen. Existing
validators resolve only exact authorized enemy/source/test/budget changes.

## Validation and reproduction

Run `bash tools/setup.sh`, then (after host dependencies are available):

```
bash tools/build-stage.sh --native
make check
make test
python3 tools/validate-level2-enemies.py
python3 tools/validate-wingsuit.py --disc
python3 tools/preview-level2-enemies.py
```

On this rootless Debian environment, `bash tools/setup-cloud.sh` installs the
ISO tool under `/workspace/mf-host-tools`; prefix build/check with
`PATH=/workspace/mf-host-tools/usr/bin:$PATH`.

The pattern regression exercises all three eye paths at camera0/48/96,
continuity, exact delayed path identity, independent member removal, all five
drone patterns, no-repeat selection, one-hit destruction, no eye projectiles,
contact/invulnerability/respawn, pause/restart and 30,000 deterministic ticks.
Existing 100,000-tick gameplay stress, camera/coop, aiming, weapon/flame,
loader/CRAM/arena guards, full command-pool rendering and preservation tests
remain active. The real renderer mock now also requires Chrome Eye ID18 at its
correct 16x16 screen origin. UBSan is enabled for the new movement regression.

Host review outputs in `build/enemy-review/`: `chrome-eye-paths.gif`,
`chrome-eye-sequence.png`, `chrome-eye.png`, and `drone-paths.png`. These execute
the production C path functions and use native RGB555 sprite pixels. They are
explicitly host path/sprite reviews, not gameplay captures. No Saturn emulator
or hardware visual/performance verification was available. Structural command
and memory checks cannot establish actual frame rate or final on-console look.

Final automated results: native stage build passed and produced matching
`build/mullet-force.bin` / `build/mullet-force.cue`; `make check` passed;
`make test` passed with 245 PASS reports; explicit enemy preservation,
`validate-wingsuit.py --disc`, and preserved-audio checks passed. ISO validation
found the early ALEVEL2 directory and exact 26-file payload. `git diff --check`
passed. Native compilation retains the parent's existing `jo_print` const
qualifier warning; no SDK or unrelated HUD change was made.

## Manual GitHub Actions build

Open **Actions → Manual Saturn playtest build → Run workflow**. Use the workflow
from `main`, select profile **stage-default**, and set **source_ref** to this
branch or the delivered full commit SHA. Download the resulting playable
artifact, keep its BIN/CUE together, and open the CUE. This profile retains the
existing development X skip and real Level 1 Stage Clear handoff. Review the
camera extremes, five drone patterns, three eye paths, independent kills and
contact damage in the emulator. No Actions run is dispatched by this pass.
