# Corporate Punk AI 2.0 — experimental tuning

Branch: `feature/level1-punk-ai-v2`. Approved parent:
`a97aedf614ad9077eb2349f435aaea70ca394811`
(`diagnostics/level2-e008-startup`). The owner explicitly approved this development
baseline after six successful playtests. This supersedes its older approval
warning for baseline selection; it does not establish a permanent E008 repair.
No baseline branch/tag is modified or merged.

## Why punks appeared passive

There was no player-idle predicate. Every landed jab restarted 18 ticks of enemy
hurt followed by 24 ticks of recovery. Repeat jabs arrived before those 42 ticks
elapsed, so the enemy could never reach an attack decision. Original windup was
24 ticks, and a shared-target gate prohibited the second slot from committing
while the first wound up or attacked. Player collisions resolve before enemy AI,
so accurate attacks already interrupt enemy windups without armor exceptions.

## Implemented behavior

All values are fixed 60 Hz simulation ticks. Existing three-tick impact hit-stop
freezes simulation and therefore adds wall-clock time to these intervals.

| Landed consecutive punches on this enemy | Hurt | Hurt recovery | Next eligible windup |
| --- | ---: | ---: | ---: |
| 1–2 | 18 | 24 | 18 |
| 3–4 | 12 | 8 | 18 |
| 5 onward | 6 | 2 | 10 |

Pressure saturates at five, per enemy, shared between cooperating players.
Collision's existing per-attack target mask increments pressure exactly once per
landed physical punch, including the third combo punch. Repeated overlapping
frames do not count. Counter eligibility never bypasses hurt, recovery, spawn
grace, target selection, range, facing or the visible windup. A subsequent
accurate jab can interrupt it; a deterministic 13-tick repeat-jab test exercises
that window. There is no instant retaliatory damage or invincible counter state.

Connected jump kicks and bat attacks clear only the struck enemy's pressure and
expiry. Misses do not clear pressure. Bat damage/instant running-bat defeat remain
unchanged. Pressure expires 180 simulation ticks after the last landed punch,
also while recovering or pursuing, and clears on defeat/absence/successful spawn.
Torch does not build or renew punch pressure; it ages naturally. No random AI
choices, new allocations or new targeting/flanking logic are introduced.

Normal uninterrupted in-range attack commitments repeat every 60/72 ticks for
slots 0/1 (1.0/1.2 seconds). Counter windups yield 52/64 ticks (0.87/1.07 seconds).
These are opportunities, not guaranteed hits; recovery, interruption, movement,
spawn grace and hit-stop can delay them. Existing movement (220 horizontal and
150 depth fixed units/tick), 44px/9px decision range, collision boxes, attack
active duration six, post-attack recovery 36/48, and spawn grace 120 are retained.
Both existing slots may commit even against the same player. Shared player
invulnerability and per-enemy/per-player hit masks prevent simultaneous damage.

The existing player impact path already meets the request: 12 ticks hurt,
650/256 px initial horizontal knockback decaying by 3/4 per tick, no automatic
knockdown, attack/bat/torch/dash and pending command interruption, damage 12, and
60 ticks post-hit invulnerability. It is reused unchanged, with 48 protected
control ticks remaining after hurt. Health/revival rules and player animation,
attack timings, movement speeds and FF+A command recognition are unchanged.

## Preservation and verification

Modified existing files: `src/game.c`, `src/game.h`, `src/combat_config.h`,
`Makefile`, `tests/combat_test.c`, `tests/coop_test.c`.
Added: this report, `tests/punk_ai_test.c`, `tools/test-punk-ai.py`,
`tools/validate-punk-ai.py`. Existing combat/co-op assertions change only the
intended 18-tick normal telegraph and two simultaneous commitments.

The scope validator compares every original approved file against the pinned
parent, allowing only those six modifications. Thus all Level 2 code/diagnostics,
complete audio/assets/manifests/workflows/input, artwork and stage progression
are byte-for-byte preserved. Original preservation locks remain untouched and
execute against the archived approved source, with the experimental disc linked
for resource/executable consistency checks. Original baseline regression suites
run there too; this does not assert experimental AI equals baseline behavior.
The new runner separately compiles and tests actual experimental gameplay with
UBSan and warnings as errors: AI, stage-clear, buffered FF+A, punch combo, repeat
jab, dash, game, combat, co-op, bat, aerial bat and torch.

Commands: `bash tools/setup.sh`, `bash tools/build-stage.sh --native`,
`make check`, `make test`. On this Debian cloud host, the existing
`tools/setup-cloud.sh` supplies missing genisoimage; prepend
`/workspace/mf-host-tools/usr/bin` to PATH. Neither compiler pin nor engine modules
change. Native source build produces matching `build/mullet-force.bin` and `.cue`.

Focused AI coverage includes both actors/facings, attacks against an actively
attacking player, one count per punch, both thresholds, interruptible counters,
connected/missed kick and bat, expiration, grace/range/recovery gates, independent
slots, player attack cancellation, protected recovery and two commitments.
Existing suites cover input buffering, 40-kill transitions and Level 2/audio.
Final native build, `make check`, `make test`, and the additional complete-profile
AI/stage-clear/FF+A regression run all passed. No unresolved test failures were
introduced or inherited. The remaining historical skips are listed below.
The baseline suites report optional skipped historical native-driver/allocator
checks where their archived fixture lacks the driver, and a dual-boot allocator
comparison without that historical staged build. These are inherited skips;
current pinned-SDK source compilation and current audio/startup mocks run.
The initial pre-setup test and missing-genisoimage packaging attempts were setup
failures, resolved before final validation, not gameplay regressions.

## Memory and limitations

Two integers per enemy add 16 bytes to `mf_game` and linked BSS. Player/enemy
render structs are unchanged. Matched pinned native builds measure executable
243,008 -> 243,296 bytes (+288) and BSS 0x66394 -> 0x663a4 (+16).
No extra sprite, palette, sound bank, VDP1/VDP2/SCSP allocation, streaming or disc
I/O. CPU work is bounded integer comparisons/decrements on two existing slots;
no hardware cycle or frame-time measurement is claimed.

This remains tuning for playtest. Five hits leave a full-health six-HP punk with
one HP; counters may therefore be uncommon during precise six-hit kills. Rapid
accurate jabs may intentionally continue interrupting all counters. Simultaneous
telegraphs and a ten-tick counter may feel demanding; player protection prevents
immediate repeated damage but difficulty needs controller-driven assessment.
No emulator or physical Saturn gameplay validation was performed for this branch.

## Build on GitHub Actions

After the experimental branch is pushed, open **Actions → Manual Saturn playtest
build → Run workflow**. Select workflow branch `feature/level1-punk-ai-v2`,
profile `stage-default`, and set `source_ref` to the full experimental commit SHA
reported with delivery (`git rev-parse HEAD`), not a baseline tag. Do not use the
older `level1-stage-clear` profile, which omits the preserved Level 2 build path.
The unchanged workflow resolves the SHA, builds, runs `make check`/`make test`,
and uploads `mullet-force-stage-default-<full SHA>` for one day. Download its
matching BIN/CUE/checksum files together and open the CUE. No workflow dispatch
or merge is performed by this implementation task.
