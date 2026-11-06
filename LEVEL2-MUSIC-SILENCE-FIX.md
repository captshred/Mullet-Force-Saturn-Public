[Download corrected complete BIN/CUE ZIP](downloads/mullet-force-level2-music-fix-952bccd.zip?raw=true)

Build commit: `952bccd917dae73f40d0519c80d2d5ee280efb68` (private authoring workspace).

ZIP SHA-256: `f2a77ae497b90051666b388de73694d9b162e6697b414765aae137efbac65531`.

This is an artifact-only delivery branch based on public approved commit `506d5f1`. It contains no private authoring ancestors. Download the ZIP to test the fix; building this branch's baseline source does not include the private authoring integration.

# Level 2 music silence: driver-verified native bank fix

Failing authoring source: `7a1de3bda065a3397de764ae5469793405f2aef4`.
Fix branch: `fix/level2-music-silence` (private authoring workspace).

## Root cause

The native tone-bank generator incorrectly wrote decimal **16** (`0x10`) to
voice-header byte 0 at `tools/build-level2-music.py:100` in the failing commit.
That byte is **packed playback-mode bits plus a bend-range code**, not a literal
semitone count. All eight voices therefore selected playback mode 1. The actual
pinned Sega driver rejects that mode before allocating a PCM voice.

The original validator at `tools/validate-level2-music.py:92` explicitly allowed
that same incorrect byte. Submission-only SDK mocks and event-equivalence checks
therefore passed even though the actual driver could not sound any music note.
This was an encoding mistake in this integration, not a composition failure.

Pinned `SDDRVS.TSK` SHA-256:
`68890ee4a49fd0c341bc3f0a48643e4db4b175df0b0d7dacfeb88306340052b6`.

Actual 68000 execution:

- `0x366A`: read voice-header byte 0.
- `0x366C`: mask playback-mode bits with `0x70`.
- `0x3674`: nonzero mode branches to `0x3C78` before slot allocation.
- `0x3C7A`: emit driver error **0x8A**, returning without SCSP key-on.
- `0x3480..0x351C`: interpret bend range through the low-nibble jump table.
  Code 6 gives six semitones. Code 13 gives **24**, not 13 or 16. This is also
  checked by running the real bend handler over every native wheel value.

## Startup and loading investigation

The stage-title/readiness gate calls `mf_ws_audio_music_begin()` at
`src/wingsuit_runtime.c:296`. That submits `SND_StartSeq(0,1,0,31)` at
`src/wingsuit_audio.c:357`: control 0, sequence bank 1, song 0. It then waits for
command drain and restores the independent channel-0 flame setup before gameplay.
These C paths are unchanged by this fix.

Music DMA loads are at `src/wingsuit_audio.c:100` and `:101`. The extended MAP
correctly assigns sequence bank 1 to 307260 and tone bank 1 to 376912. The files
are present in `/ALEVEL2`; final-disc checks compare their complete bytes.
The song contains all 4,403 notes and 14,891 native bend events. Its first notes
occur at tick 3840/960 PPQN, about 1.165 seconds after start, following the authored
opening rest. Controls, programs 0/2 and note velocities are nonzero and valid.
The driver accepts and advances this sequence with either header version.

The working Level 1 bank has usable rhythm-guitar and bass PCM. The failing Level
2 bank copied exactly the same PCM but changed its voice-header bytes to `0x10`.
No SFX initialization, DMA overwrite, invalid song/bank ID, volume mute, missing
sample or subsequent driver reset was required to reproduce the failure.

## Smallest reliable correction

1. Restore `WMUSIC.TON` to the exact working `STAGE.TON` bytes: PCM playback mode
   0 and bend-range code 6. Relative to the silent bank, only eight header bytes
   change, `0x10` to `0x06`. No samples, envelopes or instruments are replaced.
2. Rescale native SEQ pitch-wheel payloads from the source MIDI's 16-semitone
   range to the supported six-semitone range. All authored excursions (-3 to +4
   semitones) fit without clipping. Only 9,686 bend value bytes change; every note,
   gate, velocity, channel, program, controller, tempo, loop and event time stays
   exactly the same. Maximum bend quantization error improves from 11.9140625
   to **4.296875 cents**. The original 14-bit MIDI/curves remain untouched.
3. Correct the authoring generator for future native exports and strengthen
   validation to reject invalid PCM modes. The original GP parser/conversion
   was **not rerun**. GP, reference MIDI and articulation JSON are hash-identical.

`tools/level2_native_bank.py` defines the native wheel transform. The native-only
patch used the existing MIDI reference, not regenerated music. All historical
locks stay intact; a separate silence-fix lock records the exact changes and
frozen gameplay, driver, SFX, authoring and event data.

## Driver experiments and regressions

`tools/probe-level2-music-driver.py` executes the pinned sound-driver binary with
Musashi commit `313ebf1bd9f4d0d93341eb5ce21fd8a119e9dbdd`. It runs the actual
StartSeq bank/song lookup, sequence decoder, SFX channel-0 setup, queued MIDI
commands, note-on allocator and SCSP register writes. The SCSP registers are
RAM-backed; this is **CPU-level driver testing, not synthesized audio**.

| Diagnostic | Header 0x10 | Correct PCM header 0x06 |
|---|---|---|
| Complete Level 2 SEQ in Level 2 path | First note rejected, 0x8A, no key-on | PCM voice allocated, SCSP key-on |
| Known-working Level 1 SEQ in same path | First note rejected, 0x8A, no key-on | PCM voice allocated, SCSP key-on |
| Minimal rhythm-guitar note, program 0 | 0x8A, no key-on | PCM voice allocated, SCSP key-on |
| Minimal bass note, program 2 | 0x8A, no key-on | PCM voice allocated, SCSP key-on |

The failing header is reconstructed only in test memory. Diagnostic control
sequences never replace the delivered Level 2 composition. A further 256 real
bend-handler checks verify all 128 SEQ wheel values for codes 6 and 13, including
the non-linear code-13 trap. The JSON result receipt is included in the playtest.

The normal `make test` path adds `tools/test-level2-music-bank.py`: real driver
opcode guards, mutation of the exact erroneous mode, exact known-working PCM
bank equality, unchanged SEQ non-bend content, all three tracks/4,403 notes, and
frozen source/private-asset checks. Existing startup command retry/drain,
readiness watchdog, DMA/map, gameplay, renderer, SFX and disc tests remain active.
`tools/validate-level2-music.py` independently checks the source MIDI curves
against the rescaled native bends and preserves their timing and isolation.

To repeat the CPU experiments, clone Musashi outside the public source assets,
check out the pinned revision above, then run:

```
python3 tools/probe-level2-music-driver.py --musashi-root /path/to/Musashi --report work/driver-results.json
```

## Resource usage and limits

Resource sizes and addresses are unchanged: SEQ 69,652 bytes, TON 70,676 bytes
(including 70,320 bytes of the original PCM), MAP 56 bytes, sound-RAM high-water
447,588 of 524,288 bytes; **76,700 bytes free**. Existing SFX end at 307,260.
Peak held music polyphony is 9; conservative music release-tail budget 18 plus
10 SFX slots totals **28/32**, leaving four beyond that estimate. No voices,
notes or sound effects were deleted. Level 1 and gameplay/SFX sources and banks
remain byte-identical; the consumed-command readiness fix remains intact.

Native compilation, complete disc validation, event/asset invariants and gameplay
regressions are separate from audible verification. The old build's silence is
confirmed by the user's real test and reproduced at the driver's mode-rejection
branch. The corrected bank reaches real driver allocation/key-on in the CPU
experiments. **No audible playback of the corrected build on a Saturn emulator
or physical Saturn is claimed.** Please test the delivered BIN/CUE with both
players' weapons, pause/resume and a full song loop before approving audibility.

Only the playable BIN/CUE, reports and runtime verification results are public.
GP, MIDI, articulation JSON, authoring scripts/bundle and private source commit
remain in the private workspace; no private-authoring ancestor is pushed to the
public delivery branch.
