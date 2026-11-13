# Ricky flame flash and uninterrupted torch charge

Parent: user-playtested `balance/level1-bat-flame-stun`,
`7362def0071d1d6cffb91799c3f60064e1fef324`.
Candidate: `polish/level1-ricky-flash-torch-charge`.
Hardware/playtesting approval remains pending. No baseline tags move.

## Palette ownership and memory

The SDK reserves hardware palette 0. The seven allocated slots are:

| Slot | Owner in this candidate |
|---|---|
| 1 | Street/Level 2 background |
| 2 | Original Ricky colors (reclaimed dormant legacy Buck slot) |
| 3 | Ricky warm-red flash (reclaimed dormant legacy Chuck slot) |
| 4 | Corporate Punk/shared hero weapon |
| 5 | Corporate Punk warm-red flash |
| 6 | Flame/embers/charge cue |
| 7 | Gallery |

There is no unallocated SDK palette slot. Existing semantic renderer audits
established that the retired legacy Buck/Chuck palettes have no indexed draw
consumers. The direct comparison now checks that no unchanged indexed draw uses
either reclaimed slot. RGB555 player sprites ignore palette selection.

At boot, Ricky's base colors are copied into slot 2 as before; 255 colors for
slot 3 are derived with the exact existing Corporate Punk transformation:
`r=min(31,r+10)`, `g=min(31,g+3)`, `b=b/2`, with RGB555 bit 15 set.
Neither palette is modified by rendering or suffix reloads. Both are hashed by
the bank validator; mutation of either is rejected. `fire_flash` selects slot 3
instead of 2, using the same existing four-tick clock as Corporate Punk.
The explicit 25-pose API keeps its normal palette; gameplay draws select the
flash per actor. Transparent texture indices and all sprite payloads are intact.

Incremental CRAM allocation: **0 bytes**. The new color table occupies 510 bytes
of an already allocated 512-byte slot. Palette count, VDP1 texture count/bytes,
VDP2 allocation and audio payloads remain unchanged. One additional SH-2 pointer
(4 B of static CPU RAM) retains the burn palette for validation.

## Charging and visible fire

Both enemy hit paths preserve a living player's already-started charge, while
still clearing attacks/buffering and applying the original health loss,
invulnerability, hurt duration and knockback. Input continues the charge during
hurt while A remains physically held. The threshold remains 60 input ticks;
ignition can occur while hurt. No fresh attack or charge starts automatically
from the held button after a canceled active flame.

Rendering preserves the original hurt body and draws the flame independently,
including through invulnerability blink. Rendering and collision use the same
`mf_torch_active` eligibility (living active player, deployed fire, grounded).
The flame therefore remains visible whenever it can damage. A later incoming
hit still cancels deployed fire; only charging gains interruption protection.
Release, disconnect, death, airborne state, pause and the existing stage-clear
cancellation remain effective. Damage cadence, contact stun, 3-HP bat damage,
AI/spawning, all animations, audio and Level 2 are unchanged.

## Validation

- Native `stage-default` build, `make check`, `make test`, UBSan regressions.
- Hits at 20/45/59, reaching 60 while hurt, multiple hits, release, both ports,
  one ignition event, deployed-fire interruption, damage/knockback/health clocks,
  cancellation on death/disconnect/pause/stage transition/airborne state.
- Actual renderer fixtures check all 25 poses, independent and simultaneous
  enemy flash palettes, exact RGB555 colors, four-tick flash timing, unchanged
  hurt-body draws, visible flame during hurt/blink and no flame for inactive,
  dead or airborne actors.
- Existing 256-reload suite checks palette/prefix integrity, failure latching,
  stale handles and the unchanged 177 definitions / 371,072 texture bytes.
- Repeated production Yabause HLE cold starts exercise the normal stage-clear
  loading path through the existing development X input, with read-only state
  observations. The optional eight-bank-reload harness checks native palettes
  and persistent/enemy sprite pixels across nine generations, then Level 2.

The direct historical replay still excludes A input to compare unchanged
movement/AI; it does not claim unchanged rebalanced combat. Renderer comparisons
exclude only the two intentionally reclaimed palette contents and assert that
unchanged indexed draws never consume them. Hardware, natural 40-KO playthrough
and subjective visual/audio approval remain owner testing.

## Manual Saturn playtest build

Workflow: **Manual Saturn playtest build** (`.github/workflows/build.yml`).
Use workflow from: **polish/level1-ricky-flash-torch-charge**.
Profile: **stage-default**.
`source_ref`: the full final candidate SHA in the delivery report.
Download `mullet-force-stage-default-<full SHA>`; keep the matching BIN/CUE pair.
Artifact retention is one day. Do not merge or update THE ONE tags before approval.
