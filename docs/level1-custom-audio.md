# Drop Zone: Level 1 custom-audio candidate

Baseline: `the-one-phase3a-definitive`, peeled commit
`0242cbb0e92959b27e83aaf7d0ae9c75e135f3a7`. This branch does not replace or
retag THE ONE. Playtest approval is pending.

Private GP, SD3 MIDI/reference WAV and original instrument WAVs remain outside
Git and build downloads. `tools/import-level1-music.py PRIVATE_SOURCE_DIR` is an
explicit authoring command; public builds load only committed runtime assets.
It requires NumPy/SciPy. The pinned SDK, compiler and Docker image are unchanged.

## Approved interpretation

Guitar roots are C3/MIDI48; bass is C2/MIDI36. The GP controls the 583-quarter-note
range. Drum attacks before tick279840 retain their original ticks and velocities;
185 later attacks and the empty MIDI end tail are excluded. The effective tempo
is365854 microseconds/quarter at480 PPQN. No internal sections are shifted or
quantized. The sources' differing meter-change positions therefore remain a
musical review point: cropping alone does not repair internal arrangement differences.

The author approved this source-note consolidation:

- 36 kick;38/39/40 snare.
- 41/43 low tom;45/47 mid tom;48 high tom.
- 49/50/55/57 crash;52 china;53/59 ride.
- 60/64 open hi-hat, with64 a shorter articulation.
- 50 uses a short muted crash gate. Closed hat is available in the bank; no
  closed-hat source events occur in this performance.

Every supplied instrument is represented, including the closed hat. No additional
recordings or synthesized replacements are added. All three cymbals are retained.

## Native instruments and sequencing

The bank contains13 one-layer PCM voices. Source stereo is downmixed and
bandlimited-resampled. Guitar/bass preserve their attacks and use phase/context
searched sustain loops; the last32 frames crossfade into the loop boundary.
Cyclic interpolation guards follow loop data. Muted guitar remains unlooped.
PCM16 is retained for open guitar/bass/kick; other voices use native signed PCM8.
Root compensation handles the44.1kHz SCSP clock at11.025/22.05kHz sample rates.
See `assets/music/level1-custom-report.json` for exact sample sizes, roots and loops.

GP references/ties are expanded before sequencing. Palm-muted notes choose their
own voice. Twelve melodic pitch lanes isolate independently bent strings. GPIF
bend curves use their original positions, sampled every12 source ticks and
rounded to native seven-bit bends. Vibrato and slide trajectories remain pitch
controls. TON bend range is12 semitones; rounding error is up to9.375 cents.

Technical approximations: HOPO uses a softer retrigger; pinch harmonics use the
fret-derived harmonic partial of the same supplied guitar tone; ordinary slide
outs use a ten-semitone sweep, and pick slides use a pitch sweep instead of scraped
string noise. These limitations require audible review, rather than a claim of
perfect GP/RSE equivalence.

The direct gated-SEQ encoder preserves simultaneous duplicate drum attacks and
handles source zero-length gates without requiring MIDI edits. Drum gates follow
runtime PCM decay, independent of source note-offs. Two tails per instrument and
eight drum voices overall are allowed. On pressure, older cymbal/hat tails retire
before kick/snare/toms. A closed-hat route chokes open hats. Native loops clear notes
and pitch state and replay initialization.

Runtime cymbal tails are0.8s; open hat0.55s (note64 capped at0.16s), snare0.45s,
closed hat0.25s. These are audible memory compromises. Other finite instruments
retain their available natural decay, with a12ms ending fade. Original files are
not modified. The rising attack of the supplied muted sample is retained.

Music volume is100/127. Existing SFX PCM, sequence/channel volume and gain remain
unchanged. Source-dependent PCM scaling leaves headroom, and per-family TON
attenuation balances cymbals, rhythm, bass and drums. Sequence priorities are now
music8/SFX31 in Level1. No Level2 playback settings change.

## Resource and validation policy

The actual Level1 map reserves332104 bytes before music. New SEQ is50224 bytes;
TON is132148 bytes; sound-RAM high-water514476/524288, leaving9812 bytes.
The event simulation peaks at17 held musical voices, including at most8 drum
voices. Allowing50ms melodic release reaches a higher physical demand; RR31 and
the native allocator's released-voice retirement are required under pressure.
Ten slots are conservatively reserved for existing SFX and retirement. This is
not a measured Saturn slot trace or a guarantee of no stealing at saturation.

`make check` validates current audio/ISO and the exact baseline scope lock, then
runs the unchanged historical source/art/runtime checks in an archived approved tree.
`make test` adds focused sequencing/tie/PCM tests and runs the approved regression
suite unchanged in that archived tree. Every current staged payload, the executable source fingerprint and the current
disc are independently checked;
no historical audio hashes are relaxed globally. Level2 assets and all gameplay,
SFX and graphics files are frozen against the exact baseline.

Build the complete approved profile with `bash tools/build-source-complete.sh`.
Native data checks do not establish audible playback. Emulator/hardware checks
must cover tuning, loop seams, quiet/rapid notes, internal alignment, cymbal tails,
clipping, pause/resume, concurrent SFX and stage transitions.

## Observed emulator smoke

The pinned Yabause HLE test ran15500 frames, started Level1 music at frame1804,
exercised pause/resume and two-player SFX, and observed the opening chord return
at frame14461/14462 after the song loop. Every instrument used by the retained
performance was observed in the native SCSP mixer; the unused closed hat remains
available in the bank. Observed native peaks were17 music slots and18 total slots
in this input scenario. PCM peak8384/32768, with zero clipped captured samples.
Open guitar and bass both showed native sustain phase wraps.

These frame-sampled observations do not prove every attack was received, establish
maximum gameplay SFX stress, or provide human listening/real-Saturn approval.
See `docs/level1-custom-emulator.json`. Reproduce with
`bash tools/run-level1-audio-emulator.sh` after building. Private authoring media
are not needed. Captured runtime PCM/slot traces remain in ignored `build/`.
