# Level 2 Fire / non-lethal Hit candidate

Parent, owner-approved Fire retrigger/Explosion-spacing source:
`6e5c8d9eb9b83e4cf3ebb278939b02b8787a0b1e`.
Branch `audio/level2-shot-hit-swap`. Existing preservation tags remain unchanged.

## Source and deterministic runtime import

New Shot.wav: SHA256
`1abc11ab39191e031c38b5ec1c27a919a01b2e667d53d4a44c549b0f87bcfe35`,
44100 Hz, stereo PCM16, 19066 frames (0.4323356 seconds).
`tools/import-level2-fire.py <wav>` averages L/R, rounds symmetric half ties away
from zero, and writes big-endian signed mono PCM16. No resampling, normalization,
compression, pitch shift or trim. All 19066 frames remain (38132 PCM bytes).
Peak after downmix is16807. The new bank retains the old Shot's pitch, envelope,
velocity/mixer tables; only PCM address/length differ. Two zero interpolation
guard frames and bank metadata bring WFIRE.TON to38224 bytes.

Per AGENTS.md, source WAV authoring masters stay private. The build needs none:
WFIRE.TON, WFIRE.MAP, their digest/provenance manifest, conversion/staging logic
and every other runtime asset are committed. The original WAV hash identifies
an optional repeat import. Native builds compile committed source and use these
runtime bytes; no delivered executable is substituted.

## Ownership and events

All eight driver controls were already assigned. The smallest addition is an
isolated MIDI channel on an existing gain-compatible control:

| Role | Control/channel | Bank/program | Gain |
|---|---|---|---:|
| Music | 0 / original score channels | unchanged |127|
| P1/P2 Flame | 1 / 0 and1 | unchanged |80|
| Fire A/B | 2/2 and3/3 | 2/0 |96|
| Non-lethal Hit | 2/8 | 0/1 (old Shot) |96|
| Explosions | 4/4 through7/7 | unchanged |100|

Channel8 has independent bank/program/key state. Sharing control2 shares gain
only; no Hit operation changes its gain or sends a control-wide stop. All Hit
Note Offs name exactly control2/channel8/key60. Fire stops remain on channel2 or3.
Music/Flame/Explosion controls, programs, gains and PCM remain unchanged.

The old Shot PCM remains byte-identical inside WDEATH.TON: 22403 mono44100-Hz
PCM16 frames,44806 bytes. No duplicate old sample is allocated.

Fire's approved free-first/oldest-active two-voice scheduler is byte-identical.
Every successfully allocated projectile still requests an attack; exhausted
projectile allocation is silent. Fire now selects bank2/program0 rather than
bank0/program1. No firing-rate, damage or projectile behavior changes.

Only surviving projectile damage increments `g.hits`; the existing turret HP
reduction/death/score logic runs first. Four-hit turrets emit Hit on their first
three impacts and Explosion on the fourth. Single-hit aerial enemies die and
emit no Hit. Flame damage never emits Hit. The runtime forwards the counter
once per simulated tick to `mf_ws_audio_hits`.

Hit has one voice, old34-tick natural retirement, and Hit-only restart on the
next impact. Rejected stops/starts retain state. At most one Hit attack starts
per VBlank; simultaneous impact events drain on subsequent VBlanks from an
eight-event bounded counter (newest excess dropped). This bounds release
transients without monopolizing the command queue. No non-Hit key is stopped.

The Explosion scheduler is byte-identical to the approved parent: five-VBlank
starts, eight pending events, newest excess dropped, no active Explosion stealing,
natural49-tick key retirement and polyphonic tails. Music start logic, readiness
0x041a, Flame handoff/release and every non-notification gameplay rule are frozen.

## Resource accounting and validation

SCSP before447588/high-water,76700/free; after485812/high-water,38476/free.
Additional38224 bytes are solely the new Fire bank. Old resources and addresses
remain fixed. WFIRE.MAP extends the unchanged music map with bank2 at447588;
new PCM is447676. Readiness now acknowledges all entries of the64-byte map.

Conservative score/SFX allowance:18 music +4 simultaneous Flame handoff voices
+2 Fire +4 Explosion +1 Hit =29 principal slots of32. Up to three short release
transients (two Fire, one Hit per VBlank) fit the remaining physical capacity;
there is no promise for future added voices beyond this frozen budget. Native
allocator instruction tests at29 occupied records select a free record for Hit
and Fire without fallback, despite their shared gain control. The native smoke
observed bank2 Fire at447676 and old Hit at180832, both at the expected native
attenuation189, with isolated channel8 assignments.

VDP1 remains33792 bytes/28 definitions/81 max commands. VDP2 remains65792 payload/
434176 reserved, CRAM32 bytes. Audio state adds20 CPU bytes; the damage-event
counter adds4 CPU bytes. No VRAM changes.

Tests retain allocation/attack equality, old scheduler timing/overflow/wrap,
readiness mutations and mixed music/dual-Flame stress; add native bank/allocator
checks, surviving/lethal/dead/miss event checks, and rapid combined Fire/Hit
isolation. Exact additive locks preserve all old locks/resources and parent
Fire/Explosion/readiness section hashes.

Release gate: fresh clean checkout of the final committed candidate, then
`bash tools/verify-canonical-build.sh`; record its source SHA and BIN checksum.
Optional controller-only native smoke uses tests/runtime/fire-hit-frontend.c
with the same read-only Yabause observer as run-recovery-emulator.sh. Subjective
WebRetro approval of the new Fire/Hit balance is still pending.

Manual Actions: workflow from main, profile stage-default, source_ref the exact
candidate delivery SHA. No Actions dispatch or new THE ONE tag is performed.
