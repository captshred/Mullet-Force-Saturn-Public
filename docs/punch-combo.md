# Jab → jab → cross review build

Branch `feature/jab-jab-cross-combo`, from validated fast-bat commit
`84f7ba38ea239119d98e86cfabe57daa1ca97679`. No main merge.

```sh
bash tools/setup.sh
bash tools/build-punch-combo.sh --native
make check
make test
```

Omit `--native` for Docker. The `jab-jab-cross-combo` Actions job publishes
`mullet-force-jab-jab-cross-combo-<SHA>` with matching BIN/CUE, identity/checksums,
art previews and runtime captures. `BUILD-INFO.txt` must say
`Jab jab cross combo: 1` and `Fast horizontal running bat: 1`.
The historical wrappers remain controls. No new gameplay controls.

## Input and combat

Each fighter has independent `next`, `phase`, `timeout` state (24 bytes total,
appended to `mf_game`; old prefix/player ABI remains unchanged). A valid grounded
punch initiation advances0→1→2→0 whether or not it hits. The third stage uses the
rear-arm cross. Holding A does not advance the sequence. The existing fresh-edge
six-tick input buffer is retained; presses too early expire normally.

| Action | Unchained duration | Earliest buffered next start | Hit-active counters |
|---|---:|---:|---:|
| First jab |24 ticks|12 elapsed ticks|6–10|
| Second jab |24 ticks|12 elapsed ticks|6–10|
| Rear cross |28 ticks|16 elapsed ticks|6–10|

At60Hz: jab400ms, cross467ms; buffered repeat intervals200ms/267ms. These are
advancing simulation ticks: existing hit-stop adds wall-clock time. Cross recovery
is four ticks longer. Earliest restart internal counter13 becomes17 after cross.
Single-pose cross is immediate through counter11 (including display of the last
hit step), shared recovery12–20, guard21–28. The game increments attack counters
after collision evaluation, as before. No new startup delay or windup.

Timeout is **45 advancing ticks since the last valid punch initiation** (750ms),
including attack duration. Pause and hit-stop freeze it. Hurt, death, jumping,
bat, active torch, disconnect/inactive player reset the chain; valid new grounded
jab after timeout starts at stage0. A jump request during an attack retains the
existing rules; this does not add a jump cancel. After cross the next stage is
immediately reset to jab; queued A can start it at existing buffer expiry rules.

All punches, including cross, use existing jab reach52, height30–58, depth±8,
active6–10, damage1, per-target hit mask, enemy reaction, scoring and knockback.
Existing Jab whoosh and CONNECT events/transport are reused once per event.
There is no finisher damage bonus. Bat, aerial kick, torch, dash, momentum,
hurt/death, enemies, camera, backgrounds and audio samples are unchanged.

## Artwork and packing

There is no `src/combat_animation.c`; actual HQ drawing is
`mf_combat_prototype_draw()` in `src/animation_preview.c`.

Existing jabs retain `seq_upper[actor][0]`, coordinated `jab_offsets` and shared
`seq_lower[actor]`, then the existing recovery/guard. Each cross uses one new
native indexed upper from [assets/punch-combo](../assets/punch-combo/), placed at
x40,y20 in the same160×112 combat canvas/root64,108, plus exact existing lower
pieces. Both feet/boots remain unchanged. The approved native head pixels are
reused with a two-pixel forward offset; the new rear arm crosses the chest and
the opposite glove retracts. Hardware horizontal mirroring handles left facing.
No old textures, palette entries or approved animations were overwritten.

A generated reference study supplied only the rotated arms/torso candidate;
conversion/reconstruction keeps existing head art and grounded legs, thresholds
alpha and quantizes to the existing indexed palette. It is a candidate for visual
approval, not a new approved design. The native pose should be reviewed for arm,
neck, jacket/vest and belt continuity. Source study, native transparencies,
contact sheets, rear-arm closeups and mirrors are retained. The four approved
running poses and every old asset remain byte-identical.

| Resource | Before | Combo build | Delta |
|---|---:|---:|---:|
| VDP1 texture bytes |446,304|453,344|+7,040|
| Free texture bytes |12,184|5,144|−7,040|
| Definitions |253/255|255/255|+2|
| New palettes |0|0|0|
| Extra combo state |0|24 bytes|+24|

Each new texture is80×44,3520 aligned bytes, one definition. Transparent margins
were trimmed from an initial96×48 proposal. Index0 is transparent;1–253 use the
existing shared palette; no new CRAM bank. Texture IDs are shared between
instances of the same fighter. Two actors are distinct art, not recolors.

We examined reuse first: legs, heads, guard, recovery and palette are reused.
There is no existing rear-hand empty-fist cross with the required rotation.
Reclaiming old unused follow-through strips would require changing bank ownership
and historical fallback consumers; none were removed. Two remaining definitions
are used with explicit preflight against255 and the real0x7fef8 end address.
No cache, RAM cartridge, per-frame uploads or CD reads. At255 definitions, further
new poses require deliberate repacking/reuse; bytes alone no longer suffice.

## Validation and previews

`tests/punch_combo_test.c` exercises both fighters/facings, buffered third punch,
12/12/16 repeat intervals, unchained28-tick cross, same active window/damage,
one whoosh/impact, independent players, timeout boundary, held A, pause and
hurt/death/jump/bat/torch interruption. `punch_combo_bank_test.c` checks actual
loader/preflight/IDs, correct fixed lower and upper/guard mappings, mirrors,
immutable game state, exact final bytes/slots and no per-frame uploads.

The prior source-hash preservation checks retain their original digests. The
explicit new [source delta](../assets/punch-combo/source-delta.json) is reversed
only after exact candidate-hash verification, then the fast-bat delta is reversed
as before. Active combo code is tested separately; no art/audio hash is relaxed.
`punch_combo_validation.py` checks exact texture dimensions, raw indices, binary
transparency, palette, SHA256 and the actual ISO's COMBO/XC0/XC1.TGA payloads.

`tools/test-punch-combo-runtime.py` uses real two-pad input, no game-memory writes,
and reads save-state combo transitions. It checks two simultaneous chains in each
facing direction, delayed reset,12/12/16 spacing, native cross rendering, stable
VRAM, **453344 bytes /255 definitions**. See
[runtime-report.json](punch-combo-captures/runtime-report.json).
`*-actual-*` GIFs in [punch-combo-captures](punch-combo-captures/) are emulator video;
`*-offline-*` art previews are reconstructed at native size and4× nearest neighbor.
Emulation is Yabause/libretro HLE with no cartridge. New WebRetro and physical
Saturn testing have not been performed.

## Remaining visual limits

Only one new contact upper per fighter is resident. Cross extension uses that
pose immediately, then reuses the approved recovery; there is no unique cross
in-between or animation bank. This intentionally preserves jab response and
budget, but transition smoothness and rear-hand readability need human playtest
approval. Initial P2 spawn invulnerability blinking remains in early captures.

## Completed implementation checks

Native build, `make check`, `make test`, and feature-enabled fast-bat, combat,
co-op and torch regressions passed. Implementation runtime captures use commit
`1e5c67a` (full SHA in the JSON) and the matching source fingerprint; the following
review commit adds captures/documentation/test commands only, with no game-source
or asset changes. Both two-pad Yabause scenarios observed stages0,1,2,0,1,2 with
12,12,16,12,12 start spacing and verified delayed restart to0. Exact visible native
cross pixels were matched for both actors in both facings, excluding documented
actor/target occlusions. Actual VRAM counters were453344 bytes and255 definitions,
with stable texture payloads throughout play. No newly generated audio.
