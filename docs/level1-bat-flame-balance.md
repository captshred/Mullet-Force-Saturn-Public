# Level 1 bat damage and flame contact stun

Development branch: `balance/level1-bat-flame-stun`.
Parent: `the-one-ricky` / `0116ad226c29f26ecc584002c2633d2393e8f0e0`.
This candidate requires owner hardware/playtesting approval; no baseline tag moves.

Bat hits now subtract exactly 3 HP from enemies, including Ricky and Corporate
Punk. The running-bat instant-KO override is removed. The existing per-swing
hit mask, collision boxes, input, animation, knockback and sound dispatch remain.
Drum damage and all non-bat enemy damage formulas remain unchanged.

Every enemy update tests the existing flame collision volume before attack or
hurt AI. Actual contact cancels the current attack and holds the enemy idle,
including between damage ticks. Release, facing away, a lane miss or leaving
range restores normal AI on that update; a new attack must wind up normally.
The residual burn effect does not extend stun. Charging, flame damage cadence,
burn damage, scoring, death, effects and audio are unchanged. No new fields,
textures, palettes or audio resources are allocated. Level 2 is unchanged.

## Validation

`bash tools/setup.sh`, `bash tools/build-stage.sh --native`, `make check`,
`make test`. The pinned SDK/compiler and Yabause core remain unchanged.

`tests/ricky/balance.c` runs under UBSan through the existing Ricky test runner.
It checks both players, both slots and all enemy classes: adjacent bat collision
calls, two distinct 3-HP hits, ground/running/aerial bat paths, windup/active
interruptions, contact between damage ticks, release with residual burn,
recontact, misses, exact charge threshold, co-op flame overlap, unchanged damage
cadence, and death/one-time defeat accounting during sustained contact.

The historical Phase 5 suite still runs on its archived source. The direct
30,000-tick CP preservation replay now excludes A input because bat/flame
outcomes intentionally differ; it compares non-attacking player movement and
enemy AI. The decoded renderer/texture/palette comparison remains unchanged.
This replay does not claim unchanged combat outcomes.

Two separate fresh production Yabause HLE boots run through the existing
`tools/test-ricky-playable-runtime.py` harness, with the same candidate BIN/CUE
and `build/game.elf` supplied for both phases. The development X input triggers
normal stage settling/clear/loading. This checks repeatability and healthy
Level 2 entry, not hardware compatibility or a natural 40-KO playthrough.

## GitHub Actions manual build

Workflow: **Manual Saturn playtest build** (`.github/workflows/build.yml`).
Use workflow from branch: **balance/level1-bat-flame-stun**.
Profile: **stage-default**. Source ref: the full published candidate commit SHA
from the delivery report (never a later branch HEAD).
The workflow preserves audio and records the resolved SHA in BUILD-INFO.
Download `mullet-force-stage-default-<full SHA>`; retain its matching BIN/CUE
pair. Artifact retention is one day. No automatic dispatch or merge is needed.
