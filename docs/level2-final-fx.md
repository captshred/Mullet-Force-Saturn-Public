# Level2 final SFX velocity boost

Approved POOWAH executable: `a38c39259304b2af8980e16e192304f6d2ecad83`.
Its delivery commit `aa15e10bc0efee0b512f068b04e41b8485c79466` contains the
approved BIN with SHA256 `34792b3dfcfac9fb49c51ba18a3ed57765380b544b92a4145ebebd55e8dd5ffe`.
Branch: `audio/level2-final-mix-balance`. This is an SFX-only adjustment.

## Exact runtime change

Only five note-on velocity arguments in wingsuit_audio.c change110->127:
Fire (both successful player-shot channels), Hit (control2/channel8), four
Explosion controls, both Flame Attack channels and both Flame Loop channels.
The prior integer nearest rounding with halves upward gives110*1.15=126.5->127.
Each accepted event gets this value once; no PCM/instrument/control-volume
amplification or additional scaling is applied. Tap and held/focused paths are
covered through the same existing routines. Note-offs remain velocity0.

Both music settings remain108. Master volume15, SFX control gains, priorities,
queue budgets, free-first/oldest Shot replacement, explosion spacing and
suppression, attack/loop handoff, Hit routing and all cleanup remain unchanged.
Every PCM/SEQ/TON/MAP file is byte-identical to the approved POOWAH build.
Music note velocities, pitch-bends/slides, tempo, gates and loop data are exact.
Level1 code, POOWAH protection and all Level1 gains/velocities are unchanged.

Drone/hostile bullet launch has no MIDI sound event in this baseline. There is
no launch velocity to raise, and no new trigger is added. Existing audible
impact/death effects are covered. WDEATH.SEQ's legacy notes are not invoked by
current gameplay; it remains byte-identical. All live Level2 effects use the
five direct-MIDI call sites above; only music uses StartSeq on control0.

## Measured response

Matched11500-frame real-driver captures use identical heavy gameplay requests:
both Flames held, shots/explosions every5ticks, impacts every7ticks, complete
Wristbreaker loop plus prefix. All8578 SFX starts match per frame, owner/channel,
key and PCM address. Same-frame driver processing order/physical slot choices
are not asserted identical. No scheduling or allocation algorithm is changed.

Actual native SCSP gain multipliers, not assumed linear MIDI loudness:

| SFX | Before | After | Amplitude ratio |
|---|---:|---:|---:|
|Fire|189|206|1.08995|
|Hit|189|206|1.08995|
|Explosion|225|245|1.08889|
|Flame Attack|95|103|1.08421|
|Flame Loop|95|103|1.08421|

All five paths respond; no velocity-insensitive exception or compensating gain
change exists. The +15% velocity request does not imply15% linear amplitude.
Music's native gain-value set is unchanged. Matched full-loop music-only stem
RMS ratio under stress is1.00005267 (+0.0053%, effectively unchanged); the
performance/control gain is not adjusted. Minor sample timing/mix differences
are not interpreted as a music-gain change.

No missing/reordered music note-ons, forced music key-offs, cross-owner music
steals or clipped mixed samples occur in either stress capture. Both Flame
Loop voices remain active for all11137 captured frames from their note-on to
capture end in both builds. Detailed
counts, active ECNT slot peaks and mixed peaks are in level2-final-fx-native.json.
These slot peaks are VBlank-sampled, not audio-cycle maxima.

The first3000 frames of the actual game capture's Level1 audio are byte-identical
to the approved POOWAH executable's matched capture, including completed POOWAH
plays. The game subsequently enters Level2 successfully; the exact committed
executable capture is documented by the final delivery verification.

## Scope and tests

Production source differs only at those five numeric velocity arguments.
Validation enforces that exact substitution and rejects every other baseline
change outside build validation entry points and the Level2 test mock header.
The mock header removes duplicate SndSeqStat declarations already provided by
the shared mock; it has no game behavior. Current recovered-transport tests run
with UBSan and cover readiness mutations, accepted-shot/allocation equality,
queue overflow, retirement retries, exact spacing, mixed holds, focus handoff,
Hit behavior and clock wrap at the new velocity. The working POOWAH regression
suite and current POOWAH transport are also retained.

Sound RAM is unchanged: Level1 uses521304 bytes with2984 free; Level2 uses506660
bytes with17628 free. No samples, instruments, sequences or RAM allocations are
added. The known pre-existing intermittent E108 issue remains unresolved and
was not refactored or claimed fixed. Hardware approval remains pending.

No merge or definitive tag is created. All existing THE ONE tags are preserved.
Promotion to the suggested the-one-poowah-final-audio-definitive tag requires
the user's explicit approval of this new experimental build.

Rebuild locally: `bash tools/build-source-complete.sh`, `make check`, `make test`.
Actions: **Manual Saturn playtest build**, workflow branch
`audio/level2-final-mix-balance`, existing profile `level1-ugh-protected-sfx`,
source_ref the exact executable SHA in the delivery manifest. That profile builds
the complete current source and committed audio; it does not regenerate UGH or
replace POOWAH. SDK/compiler pins and1-day artifact retention are unchanged.
This delivery is built locally; no Actions run is claimed.
