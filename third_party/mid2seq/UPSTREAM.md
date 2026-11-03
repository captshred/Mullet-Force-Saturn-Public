# mid2seq provenance and compatibility evaluation

Vendored BSD-3-Clause files from https://github.com/jfsantos/mid2seq at
`67072f9a99ba4abbb859ebebc6859396415628d6`: `tools/mid2seq.c`,
`tools/saturn_kit.py`, and LICENSE. No SCSP emulator/WASM or MAME-licensed files
are included. The existing Sega 2.10 driver and SGL 3.02j remain unchanged.

Verified by source inspection and independent emitted-data decoding:

- C converter accepts only SMF format 0. `tools/midi.py` merges format 1 and
  `tools/music.py` explicitly maps programs/channels and consumes RPN bend range.
- The upstream converter computes gate lengths, encodes large gates/deltas,
  program/CC events, and reduces pitch bend to the driver-native seven bits.
- Upstream unconditionally replaces the tempo map with two fixed-tempo entries.
  Our small local patch preserves segment durations/tempos, stable tie order,
  and rounds bends to nearest seven-bit value instead of truncating.
- Header reads are checked explicitly, including on fortified host toolchains;
  truncated headers fail instead of leaving uninitialized fields.
- Added optional `--loop` emitting paired native 0x82 markers around the normal
  stream, and tempo-loop pointer 8. Non-looping conversion stays available.
  Initialization and final all-notes/all-sound-off/bend resets are in the loop.
- `saturn_kit.py`'s PCM TON builder is reused unchanged. Custom generators and
  envelopes are original to MULLET FORCE, registered from `tools/music.py`.
  The source kit's 22050 Hz percussion would play twice as fast at unity SCSP
  pitch: our generation explicitly uses 44100 Hz. No SF2 conversion is used.
- FM mode consumes multiple hardware slots per note and is unnecessary for this
  song. All generated voices here use one PCM layer. DSP mixer/send fields are
  explicitly zeroed for dry playback; no DSP program is installed.
- MIDI RPN sets six-semitone sensitivity; TON voice headers use bend range 6.
  SEQ seven-bit bend precision loses at most 4.6875 cents at that range with
  nearest rounding (except positive full-scale saturation; not reached here).
- Compared ABI with the pinned SGL sound functions and the native SEQ/TON sample
  in Frogbull/SaturnRingLib (`Samples/Sound - SEQ`). The map layout uses the
  same boot/work/DSP reservations, but ONLY our own generated data banks.
  No commercial sequence, tone, PCM, BIOS, DSP program or other sample data
  from that repository is distributed.
- The pinned `SDDRVS.DAT` is byte-identical to `SDDRVS.TSK` plus a final FF
  sentinel. Initialization uses the TSK program length, 26,610 bytes.

Format cross-checks used `mistydemeo/seq2mid`'s `seqformat.txt`/`decode0.c`:
SEQ tempo entries describe durations at the current tempo; loop markers occur
in pairs; E0 events hold the MIDI bend MSB. Those files are inspection references,
not bundled dependencies. Converter output is independently decoded and compared
against all source note times, durations, velocities, and rounded bends.

This establishes data/API compatibility, not verified Saturn audio playback.
Native boot, musical timbre, tuning, balance and pause audibility still require
emulator or hardware listening tests. No new 68000 sound driver was written.

A linked-SDK disassembly check confirmed that SGL's automatic slSequenceOn
allocator consults the 68000's control-port status and searches ports 1..7.
Multiple calls before status acknowledgement can select the same port. Runtime
therefore uses the existing SDK LIBSND SND_StartSeq interface with fixed ports
0..3, while retaining SGL/SND driver initialization. All playback commands use
LIBSND after the initial SGL flush, and per-port pause/continue retry masks keep
transport state synchronized. This binary/API inspection is not audio playback.
