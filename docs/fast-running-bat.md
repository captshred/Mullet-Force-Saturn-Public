# Fast horizontal running bat — review build

Parent: main `4e677436a3ab172bd26ddfd92cd79e2752636499` (approved waist-seam baseline).
Branch: `fix/fast-horizontal-running-bat`. No merge into main.

## Build and controls

```sh
bash tools/setup.sh
bash tools/build-fast-running-bat.sh --native
make check
make test
```

Omit `--native` for the pinned Docker build. The new Actions job
`fast-horizontal-running-bat` publishes `mullet-force-fast-horizontal-running-bat-<SHA>`.
Use its matching `build/mullet-force.bin` and `.cue` (MODE1/2048).
`BUILD-INFO.txt` must say `Fast horizontal running bat: 1` as well as the full HQ
waist/hurt/death/jump/torch/enemy/custom-SFX flags. Existing profile jobs and the
original wrapper remain historical controls with this feature disabled.

Controls unchanged: forward, release, forward and hold to dash; A during an
established dash deploys the running bat. Forward-forward+A on the second tap
still performs the planted bat. B jumps; airborne A is always the aerial kick.

## Exact implementation and timing

The baseline has no `src/combat_animation.c`: the actual HQ assembly is in
`src/animation_preview.c`. Its `mf_combat_prototype_draw()` overrides the legacy
`mf_bat_frame()` fallback in main. Baseline ground bat gameplay lasts 36 ticks,
active 12–17; HQ visual preparation covers 1–6, downstroke 7–11, horizontal contact
12–17 and existing guard 18–36. The generic legacy `mf_bat_frame()` also has long
holds (including frame5 at20–27), but changing it alone would not change the HQ
sequence or collision schedule.

The feature uses the existing `p->bat` integer as a discriminator: 1 planted,
2 running (`MF_BAT_RUNNING`); no struct layout or player/game ABI changes.

| Running phase | Attack counter | Actual resident artwork |
|---|---|---|
| Carry | 1–3 | Exact approved `run_parts[actor][last_run_phase]`, plus shared carry bat |
| Horizontal contact | 4–8 | Existing `seq_lower[actor]` + `seq_upper[actor][1]` |
| Quick recovery | 9–12 | Existing approved guard `polish_parts[actor][0]` |

Duration: **12 advancing simulation ticks (200 ms at60Hz)** rather than36.
Damage active: **4–7 inclusive**, beginning three advancing ticks after the A
input. The extra visual contact tick8 displays the last active-step result.
Existing hit-stop freezes simulation and can extend wall-clock playback;
this has not been shortened. The engine increments the attack counter after
hit evaluation, so the first rendered post-input counter is2. Do not confuse
trace post-step counters5–8 with collision counters4–7.

The running hitbox is fixed horizontally: facing-relative near6/far78, ground
depth ±8, height30–64. It intersects barrels and standing enemies at the visible
horizontal strike, without borrowing the planted bat's rising arc.
Planted bat duration36, active12–17, reach, rising hit volume, damage and its
approved shorter visual swing are unchanged. The eight-tick decaying momentum
slide, dash speed1.7×, input windows and four-frame run cycle are unchanged.

## Barrels, airborne attacks and sound

Running hits set intact barrel HP directly to0 and use the existing flash/spark,
knockback, CONNECT, broken counter and score path:10 impact +100 destruction per
barrel. Each per-target hit-mask bit and zero-HP guard prevent repeated damage,
scoring or destruction. Ordinary Corporate Punks retain the existing running
one-hit KO and250 score. Planted bat removes2 HP; jab removes1; torch unchanged.

The feature clears/blocks bat gestures throughout height/vz flight, including
simultaneous jump+A. Airborne A remains a kick. No airborne bat can be activated,
rendered or carried into landing. Historical source and resident legacy assets
are retained; **zero registrations are removed** because shared/fallback resource
ownership is unchanged. No gameplay CD reads or RAM-cartridge work was added.

The original WAV-derived bat whoosh event is emitted at deployment, and CONNECT
only on valid contacts. The removed late generic running swoosh cannot replay it.
Existing audio transport, player ports, source WAVs, FX and stage SEQ/TON are
unchanged; source and actual-disc payload checks remain enabled.

## Memory and preservation

No new or edited sprite/palette/texture files. No changes to Buck or Chuck's run,
waist fixes, walk, hurt/death, jump, torch, enemy artwork, scenery or music.

- VDP1 **446,304 /458,488 bytes**, **12,184 free**; delta0.
- **253 /255 definitions**, including existing shared views; delta0.
- No new palette, texture uploads or work-RAM state; same struct sizes.
- VDP2 allocation unchanged (385,152 reserved); no background edits.

Older artwork milestones intentionally lock gameplay source hashes. They now
call `preserved_source.preserved_bytes()` for those comparisons: the helper
checks the exact candidate SHA, verifies every reverse edit, reconstructs the
approved parent and checks its original SHA before existing historical locks
run. The explicit patch is [source-delta.json](../assets/fast-running-bat/source-delta.json).
No historical digest was updated; art/audio are never substituted. Active new
logic and draw mappings are separately tested. Feature-disabled regressions
still compare16,000 input ticks against the historical SFX baseline.

## Validation and visual limits

`tests/fast_bat_test.c`: both fighters/facings/all four run-entry phases, 12-tick
miss, first hit at4, three simultaneous barrels and two punks, one score/event
per target, two-player attacks, planted damage/timing, airborne kick/physics and
clean landing. `tests/fast_bat_bank_test.c`: actual loader/draw selection,
carry/contact/recovery IDs, mirrors, immutable state, no allocations and unchanged
planted sequence. Both are part of `make test`.

`tools/test-fast-bat-runtime.py` uses real libretro pad inputs and read-only
Yabause save-state traces. It records both fighters destroying a barrel and
punk, a further punk KO, left-facing fast swings, airborne kick instead of bat,
and a subsequent planted bat. It checks actual slot count/texture bytes, stable
VRAM, native contact pixels and one-time scores. No game-RAM writes.
See [runtime-report.json](fast-bat-captures/runtime-report.json).

Offline native/4× GIFs and both-direction contact sheets in
[assets/fast-running-bat](../assets/fast-running-bat/) are indexed-texture
reconstructions, not emulator captures. `*-actual-*` files in
[fast-bat-captures](fast-bat-captures/) are emulator video.

The restrained three-pose attack deliberately reuses existing artwork; there is
no newly drawn hand/torso in-between. The horizontal strike uses the approved
connected two-hand grip, then the bat is stowed on returning to guard. This fast
pose change and carry-to-planted stance transition need human visual approval.
No separate long follow-through or downstroke is played. Emulation is a native
Yabause/HLE test, not a new WebRetro or physical Saturn certification.

## Completed local review checks

Native build, `make check`, `make test` and the feature-enabled combat/co-op/torch
regressions passed. Feature tests also cover every active-window boundary,
held/repeated A during an existing swing, and pause/resume. The source-disabled
historical control tests remain in the same suite.

Fresh Yabause captures used implementation commit
`41e9760b2c618a33da072ec3058fccdb50796f53` and game-source fingerprint
`7f53d55636bf844328bc2ee60b1984270e4424b8ec717e763f8c38673c14cd02`.
The following review commit adds captures and test cases only; the runtime source
and texture mappings are unchanged. Runtime contact traces show exactly360 then
250 points per fighter, one broken barrel and two defeated punks. Left-facing
fast attacks, airborne kicks with no bat, and subsequent planted attacks passed.
The texture-definition/VRAM counters were checked directly in
save states (253 definitions,446304 bytes); no texture payload changed during play.
See the JSON for exact contact counters and native-pixel counts. Spawn
invulnerability blinking remains visible in Chuck's early gameplay GIF; it is
existing gameplay, not a missing sprite or attack frame.
