# Level1 mono rhythm, music gain and SFX panic isolation

Experimental branch from `the-one-level1-custom-audio-definitive`, annotated tag
object95e997f264bac2ba490a6bcd874a0bce5c74ebc5, peeled source commit
`a0982c738f78ac7a00bdbd248c1d5ebe299b6971`. Protected tags are not moved.

## Runtime-only refinement

The approved sequence has2025 left rhythm notes at pan35 and2023 right rhythm
notes at pan93. Both use approved open/muted guitar voices0/1. Exactly2017 right
notes match the left in timing, gate, pitch, velocity, sample selection and actual
pitch-control trajectory. Those notes are removed. Six nonidentical right notes
(including a different harmonic and a low-D harmony, plus differing mute/dynamic
articulations) remain as centered exceptions. The complete left part remains.
All rhythm events now pan64. Both lead parts retain their original pan48/80.
Bass and1804 drum events keep their exact gates, timing, pitches and velocities.
No GP/MIDI/WAV source is read or reconverted by this operation.

Maximum held music demand changes17->15; rhythm alone8->5. A conservative50ms
release window changes full music demand28->24. These are timeline measurements,
not a claim that a deleted track frees one slot. Native playback is measured
separately. Existing drum tail cap and all decay/loop/sample behavior are retained.

## Confirmed interruption cause

Every Level1 effect song ended with CC123. In the exact pinned SDDRVS2.10 binary,
the CC table at0x2fb8 maps controller123 to0x3172. Its routine starting0x317a loops
through all32 physical slots, clears their flags and writes hardware key-off.
It does not filter by sequence owner or channel. Read-only native emulator traces
show music control0 receiving these key-offs during ordinary SFX completion.
This is a global panic, not evidence of music voice stealing or intentional ducking.
The independent StopSeq path0x54d4 does filter owner and is retained unchanged.

All eight SFX terminal CC123 events are replaced with bank0 re-selection (CC32=0)
at exactly the same ticks, leaving file size, gates, notes, velocities, programs,
tempos and loop structure intact. Bank0 was already selected for those effects.
The16 music-loop cleanup CC123 events become bank1 re-selection, preventing a
music-loop panic from truncating SFX. All musical gates already end within the
loop boundary. The native driver, existing ports, priorities, retry/suppression
logic, effect scheduling and all SFX PCM/tone/gain data stay exact. No invented
reservation or allocator flags are used. Removing redundant rhythm demand adds
headroom while the cause is fixed directly at its sequence commands.

## Music-only gain

Music sequence level100->108; music-channel CC7 values112->127. Native per-voice
TON TL reductions are listed in `assets/music/level1-refinement-report.json`.
Rhythm gains3.0/3.375dB from TL, bass1.125dB, kick/snare/toms2.25dB, hats3dB,
ride/crash/china2.25dB, in addition to sequence/channel attenuation changes.
These controls are not falsely treated as linear amplitude multipliers.
Every PCM byte, root, loop, envelope, tuning, gate and velocity is preserved.
No global master or Level2 setting changes. SFX sequence volume remains112,
and FX.TON is byte-identical.

## Resources and scope

The music bank remains132148 bytes. Sequence reduction lowers Level1 sound-RAM
high-water to504380/524288, leaving19908 bytes. Native driver/work/DSP reservations
and both SFX addresses/sizes remain unchanged. All Level2 files, game/graphics
code and assets, stage transitions, SFX gain and source scheduling remain frozen
against the approved source commit. New tooling works from committed runtime
SEQ/TON data; private authoring sources are not needed or published.

`make check` validates the current disc/audio and exact scope, then runs the
unchanged approved validators in their original archived source trees. `make test`
adds focused runtime roundtrip/panic/preservation tests and retains all approved
regressions. Public build: `bash tools/build-source-complete.sh` (or workflow
from main, profile stage-default, source_ref the delivered commit).

Native emulator/HLE observations and human listening/hardware approval are
reported separately. No claim of actual Saturn hardware validation is made.

## Measured playback results

Pinned Yabause core8926b0c6c347f8c5c755911ddb0ac695420ffbf8, HLE BIOS, read-only
KEYON/KEYOFF/owner/68K-PC observation. Ordinary before/after combat each ran15500
frames (a complete score loop plus its repeat). Real driver-only stress ran15500
frames with all six approved SFX ports; it is not the delivered game image.

| Measurement | Approved baseline | Refinement | Six-port stress |
|---|---:|---:|---:|
| Global forced music key-offs |1842|0|0|
| Missing/reordered native music note-ons |0|0|0|
| Cross-control active music steals |0|0|0|
| Peak observed music slots |17|15|15|
| Peak observed SFX slots |3|3|6|
| Peak observed combined slots |19|17|20|
| Captured mixed PCM peak |10465|20649|20966|
| Clipped captured samples |0|0|0|

The old build received its note-ons, then its SFX panic prematurely released892
guitar voices,185 bass voices,257 kicks,153 snares and355 other drum/cymbal voices.
The sequencer did not restart or lose those note-on events. This explains the
reported audible gaps without assuming voice exhaustion.

The opening two seconds contain no SFX and use identical recording levels.
Music-stem RMS rises303.07->1745.70 (+15.21dB), peak1748->12146. Whole combat
music-stem RMS rises460.36->2805.04 (+15.70dB), including restored sustains.
All velocity data/dynamics remain intact. The first100ms of the same SFX capture
is bit-identical; SFX stem peak stays9658. Ordinary SFX counts on each exercised
control match exactly. Worst stress output20966/32768 leaves about3.9dB captured
headroom. These are measured emulator results, not a calibrated Saturn startup
sound comparison or a guarantee for every analog/hardware mix.

Conservative simultaneous-demand accounting:24 music voices with50ms releases,
six principal SFX ports, plus up to two legacy same-update stop/restart release
tails =32 slots. Combat replacement ports have a full-VBlank retirement guard;
hiss has a three-VBlank guard. No unsupported hardware reservations are asserted.
Actual native envelope-active snapshots peak at20 in the six-port test; all
expected source note-ons occur in order through a full loop and its repeat.

The Level1->Level2 test starts native Level2 music at frame2613 in both builds.
All ordered note/effect/gain parameters agree. Some post-transition events cross
one frame boundary (maximum difference1 frame), and PCM is not bit-identical.
An unchanged-baseline repeat is bit-identical. The Level2 code, resource bytes,
volumes, allocator and handoff policy remain completely frozen; no phase-alignment
hack or compensating Level2 timing change was introduced. Hardware/listening
review should include this handoff and sustained two-player Level2 effects.

See `docs/level1-refinement-playback.json` and the compressed timestamped KEYON/
KEYOFF traces in `docs/level1-refinement-traces/`. Trace fields include emulator
frame, action, physical slot,68K PC, owner, channel/key, note serial, PCM address,
envelope, attenuation and phase. All captures are runtime output; no original
GP/MIDI/WAV authoring media are included.

To reproduce after a native build, extract the approved BIN/CUE ZIP and run
`bash tools/run-level1-refinement-playback.sh /path/to/approved/mullet-force.cue`.
It builds the pinned read-only observer and separate native stress harness,
captures both builds, and writes `build/LEVEL1-REFINEMENT-PLAYBACK.json`.
Raw runtime PCM/stems and verbose traces stay under ignored `build/`.
The delivered experimental build still requires the owner's hardware playtest.

## Experimental delivery

Branch: `audio/level1-mono-volume-voice-fix`.
Executable source commit: `17445b421bcafd8d5c974d624ddc2a34e768d725`.
Download: `downloads/mullet-force-level1-mono-volume-voice-fix.zip`.
The later packaging commit changes delivery/validation metadata only; use the
embedded source commit above when identifying this tested executable.

Native build, `make check`, `make test`, focused audio/preservation tests and
full-loop combat/six-port stress/transition checks pass. The committed executable's
2300-frame smoke audio is bit-identical to the tested full capture prefix.
The validator also passed a cold shallow-checkout parent-fetch test.
Original private GP/MIDI/WAV files are excluded. No definitive tag is changed.

This is a locally built playtest ZIP; no Actions run is claimed. To reproduce,
use workflow from `main`, profile `stage-default`, source_ref `17445b421bcafd8d5c974d624ddc2a34e768d725`.
The ZIP includes BIN/CUE, checksums, licenses, results and allocation traces.
Owner hardware/listening approval remains required for this experimental build.
