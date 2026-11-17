# Wristbreaker experimental custom audio refinement

Protected baseline: annotated `the-one-level1-audio-refined-definitive`, peeled executable source `17445b421bcafd8d5c974d624ddc2a34e768d725`. Development branch `audio/level2-wristbreaker-full-refinement` starts at that exact source, not its packaging commit. No definitive tag is created or moved and no baseline merge is performed. Owner hardware/listening approval remains required.

## Readiness and preservation

The supplied ZIP contains readable `Wristbreaker Drums.mid` and `Wristbreaker Drums.wav`. They remain private; public builds use committed native SEQ/TON/MAP resources only. The original GP is not reconverted. All Level1 assets, sequence, tone bank, gain, cleanup, music/SFX code, gameplay and graphics remain byte-identical to the approved source. Level2 gameplay, input, rendering, timing, SFX suppression and scheduling remain frozen. The sole C change is music control0 sequence level127→108; the address/size header follows the repacked banks. The current lock freezes every other approved tracked file.

## Guitar and bass

Native channel1/2 is the primary doubled rhythm pair; other channels carry split chord/pitch-control lanes. The complete hard-left guitar material contains1669 notes, and hard-right1670. Exact comparison of onset, gate, pitch, velocity, program and effective bend trajectory finds1372 redundant right-side notes:1086 in the primary pair and286 in split chord lanes. All298 differing right events and all1669 left events remain. Every other melodic event remains. All recovered hard-pan guitar lanes are centered64. There are no named GP tracks in the native file; no separate lead classification is invented, and every nonredundant lead/harmony/gesture is retained. Melodic held demand falls9→6 before adding the new drums.

The original native score uses guitar program0 and bass program2, with no program1 muted-guitar events or explicit palm-mute markers. Those distinctions cannot be inferred reliably from short gates; no new mutes are invented. All encoded pitches, durations, velocities, slides and bends remain exact. Original native bend range is6 semitones; Level1 uses12. The copied Level2 open/bass voice headers retain range6 so original bend values keep their original musical meaning. PCM, root, loops, envelopes, velocity tables and TL remain copied from approved Level1.

## SD3 drums and synchronization

MIDI format0,480 PPQN,2803 paired hits, no unmatched note-offs or unclosed notes. The effective tempo is291262 microseconds per quarter (approximately206 BPM), in4/4. Native960 PPQN permits exact2× onset conversion with no rounding, shift, quantization or independent timer. Existing native tempo/header/loop ticks remain unchanged. Guitar/bass first attacks at native3840 align with kick/snare at MIDI1920; the hat pickup begins at tick0. The564-quarter-note range ends at native541440 / MIDI270720:164.271768 nominal seconds. The reference WAV is stereo PCM16/44100Hz,164.271837 seconds. MIDI end-of-track865920 is an empty export tail; all2803 attacks fit the native score. Last attack270400 and source gate270649 fit the same range.

| Source note | Hits | Custom sample / articulation |
|---|---:|---|
| 60 | 86 | open_hat |
| 36 | 1229 | kick |
| 38 | 528 | snare |
| 52 | 73 | china |
| 55 | 27 | crash |
| 45 | 56 | mid_tom |
| 43 | 23 | low_tom |
| 49 | 4 | crash |
| 57 | 21 | crash |
| 39 | 22 | snare |
| 48 | 40 | high_tom |
| 41 | 10 | low_tom |
| 64 | 358 | open_hat (short tail) |
| 47 | 16 | mid_tom |
| 50 | 18 | crash (muted tail) |
| 51 | 96 | ride |
| 53 | 188 | ride |
| 59 | 8 | ride |

All assignments reuse the approved SD3 mapping; the owner explicitly approved new note51→Ride.wav. SD3 channels1 and10 are both read. Note50 retains the muted-crash tail and64 the short open-hat tail. The740 poly-pressure events address note36; the approved sample method uses note-on/velocity articulation and does not invent additional notes or pressure-driven sounds.

A native key-split kit uses39 distinct trigger keys with shared PCM. Aliases keep overlapping hits separate without duplicate sample storage or key-scoped note-offs stopping another tail. Every hit and velocity is retained. Ordinary one-shot gates allow50ms plus2% beyond PCM duration to absorb native gate rounding; playback ends naturally at sample LEA. Deliberate50/64 chokes are retained. Last-hit tails can ring over the unchanged loop boundary, and alias reuse is checked across that boundary. No sample is shortened to fit memory. Native captures verify ordinary samples have reached LEA before their gate closes.

## Bank reuse, memory and gain

One Level2 music bank copies approved open guitar, bass and the nine actually triggered drum samples. Untriggered muted guitar and closed hat PCM are not loaded. All used PCM and guard bytes, guitar/bass sustain loops, roots, envelopes, mixer/velocity tables and per-layer TL are preserved. Multiple drum key zones share a single PCM copy. Level1 is independently reloaded at stage boundaries exactly as before; its bank is not edited. The Level2 SFX bank is repacked to remove7200 bytes of unused padding while preserving every SFX sample/guard, pitch, gain, loop and envelope. Only sample addresses move; diagnostic constants and all maps follow them. The whole148864-byte lower driver/work/transfer/DSP/PCM reserve remains intact.

| Region | Start | Bytes | End |
|---|---:|---:|---:|
| Driver/work/transfer/DSP/PCM reserve | 0 | 148864 | 148864 |
| WDEATH.SEQ | 148864 | 84 | 148948 |
| WDEATH.TON | 148948 | 151112 | 300060 |
| WMUSIC.SEQ | 300060 | 52064 | 352124 |
| WMUSIC.TON | 352124 | 115844 | 467968 |
| WFIRE.TON | 467968 | 38224 | 506192 |

Sound-RAM high-water506192/524288; free18096. PCM is uncompressed approved runtime PCM8/PCM16. No streaming, duplicate PCM, private driver flags or unverified memory-reserve reclamation is introduced. Shared-work/DSP reservations remain unchanged.

Music-only gain: approved Level1 TON TL values, original authored CC7 ratio88/80 raised to127/115, and music sequence level108. Global master15 and every SFX gain/pitch remain exact. Level1 music levels remain exact. Stage2 whole-capture music-stem RMS rises527.43→3508.83 (+16.46dB). Approved Level1 combat-stem RMS at the identical observer/mixer settings is2805.04: Level2 is approximately1.94dB higher for these different musical passages. These are unnormalized RMS comparisons, not perceptual mastering or analog-hardware measurements.

## SFX ownership and measured playback

Level2 uses its own direct-MIDI SFX scheduler. Ordinary combat already avoids the Level1 terminal-SFX panic and showed0 forced music interruptions before and after. However14 music-loop CC123 events remained, and the unused legacy effect SEQ retained one. These now re-select their already selected bank1 or0 at the exact original timestamps. In baseline full-loop stress, the music-loop panic prematurely keyed off9 active SFX voices (all seven SFX controls represented). Refined stress has0 global forced music or SFX key-offs. No driver, allocator, ownership, effect gate, scheduling, suppression, priority or native command protocol changes are made.

Pinned Yabause8926b0c6c347f8c5c755911ddb0ac695420ffbf8 with HLE BIOS and read-only native KEYON/KEYOFF/owner/phase observations; original mixed PCM is never modified. Game before/after captures each14000 frames. Before/after real-driver stress11500 each; music-only11500. Every capture includes a full song loop plus a repeat prefix. Stress is a separate image using the real current driver/scheduler, both sustained flames, both Fire ports, Hit and all four Explosion controls with saturated queues; it is not the delivered game image.

| Measurement | Previous game | Refined game | Previous stress | Refined stress |
|---|---:|---:|---:|---:|
| Peak music slots | 9 | 22 | 9 | 22 |
| Peak SFX slots | 6 | 6 | 9 | 11 |
| Peak combined slots | 13 | 22 | 18 | 31 |
| Missing/reordered music note-ons | 0 | 0 | 0 | 0 |
| Global forced music key-offs | 0 | 0 | 0 | 0 |
| Cross-control music steals | 0 | 0 | 0 | 0 |
| Premature music gate-offs (>2 native-clock frames) | 0 | 0 | 0 | 0 |
| Ordinary drum tails cut | 0 | 0 | 0 | 0 |
| Mixed PCM peak | 15325 | 20285 | 18704 | 29858 |
| Clipped samples | 0 | 0 | 0 | 0 |

Snapshots count native envelope-phase records conservatively, including short release/retirement overlap. Extreme stress reaches31/32 slots (one observed slot of headroom); this is a measured bound for the exercised schedule, not a new hardware reservation. No actual music loss or clipping occurred. Music-only capture has0 SFX, peak19095, and0 cut ordinary tails. Full trace data and numeric results are in `docs/wristbreaker-playback.json` and `docs/wristbreaker-traces/`.

The first2200 frames of Level1 mixed PCM are bit-identical to the approved capture. All Level1 runtime/source files are byte-identical. Game-over→Start restart is visually confirmed with lives restored; stage entry, cold initialization, normal/rapid shooting, focused-fire/Flame intervals, multiple enemies and explosions are exercised through controller input. Game combat eventually reaches game over; the separate saturated native scheduler test continues SFX through the full score and loop. The final-source smoke/restart capture is separately identified in delivery metadata.

The bank layout changes CD-read duration, so the first Level2 music frame changes; the readiness/handshake, transition and music-start source protocol is identical. Native loop playback is9674 frames versus9677 in the approved source under this observer (the removed global cleanup consumes work). Nominal PPQN/tempo converted at60fps overestimates both builds’ native loop duration by approximately1.8%; all musical parts share the same native clock and no timing compensation/time stretching is applied. Gate timing checks use the measured native loop clock. This timing observation is an emulator result, not hardware tempo calibration.

## Build and verification

Run `bash tools/setup.sh`, then `bash tools/build-source-complete.sh`, `make check`, `make test`. Keep the pinned Jo Engine/compiler556d081146211b6a1cfa6591d70f9487d406758b and Docker base unchanged. Public builds read committed runtime data; optional `tools/refine-level2-wristbreaker.py PRIVATE_DRUM_MIDI` is an authoring import only. It never reads/reconverts source WAVs or GP.

`make check` checks the current ISO payloads/source fingerprint and exact allowed scope. `make test` adds musical/PCM/alias/ownership invariants and the unchanged approved regressions in archived baseline trees. Historical locks are retained with their original source. Current assets and current disc are independently checked. To reproduce native captures after a build: `bash tools/run-wristbreaker-playback.sh /path/to/approved/mullet-force.cue`. Raw runtime audio/stems and verbose snapshots stay under ignored build directories.

No Actions run or real-Saturn validation is claimed. The deliverable is an experimental BIN/CUE ZIP for owner playtesting. Previous definitive baselines remain untouched.

## Remaining diagnostic and saturation limitations

The preserved in-game cached-envelope monitor can display `SFX ... LOSS` warnings in this HLE capture. Native traces contradict the game warnings: Explosion control4/slot31 keeps the same owner/key/serial, advances sample phase continuously, and receives normal key-off49 frames after onset, exactly as in the approved build. All12 measured refined-game Explosion note-offs and all24 final-source smoke/restart Explosion note-offs retain49-frame leases. No active cross-owner reassignment occurs. The baseline also exposes cached EG8 while the native envelope is active. The asynchronous HLE monitor cache is not reliable as a waveform/loss measurement. See `docs/wristbreaker-hle-diagnostic-evidence.json`. No production diagnostic is weakened or silenced and no emulator monitor behavior is changed to obtain a pass. Hardware review should distinguish the diagnostic from actual audible interruption.

The deliberately overloaded scheduler stress also exposes an inherited same-control stop/start edge: the baseline has8 Explosion key-offs in their onset frame, and the refined run12, alongside896/895 normal49-frame endings respectively. These use the normal scoped key-off path, affect no music, and occur under continuous requests beyond normal accepted scheduling. The baseline additionally has4 Explosion global-panic terminations plus5 other SFX global-panic terminations at the song loop; all9 global-panic interruptions are eliminated. Normal controller-driven game and final-source restart captures have no zero-age Explosion endings. Existing SFX scheduling/suppression is explicitly protected by this task, so it is preserved; the inherited saturation edge is documented rather than silently changing its policy or claiming every overloaded SFX request plays in full.
