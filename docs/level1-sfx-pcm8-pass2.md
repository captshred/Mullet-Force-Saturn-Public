# Level 1 signed PCM8 SFX trial, Pass 2

Parent: `43b788a02e37d9b3b962c2aaa735ba0b2afb0340`. The only new PCM conversion
is the jab-initiation/miss whoosh in Level 1 FX tone bank 0, program and song 5.
The original recording is `assets/sfx/custom-combat/Jab_1.wav` from the
historical MF SFX1 archive (source SHA-256
`3e0e0ca178667c6a28b29826e25df6586a2cfbf2506869ec9bb0d4085a4888dd`).
The conversion input is the exact signed big-endian PCM16 mono slice of
the parent `assets/cd/FX.TON`, at bank offset `0xBBD8`, SCSP offset
`0x302C8`. Its SHA-256 is
`18176fffa2f121c3ab986398116f464eb702a7a43879c6f3ee847fe6836ce6b4`.

| Format | Rate | Frames | Duration | Packed SCSP sample bytes |
|---|---:|---:|---:|---:|
| Pass 1 PCM16 | 44,100 Hz | 17,844 | 0.404626 s | 35,688 |
| Pass 2 signed PCM8 | 44,100 Hz | 17,844 | 0.404626 s | 17,844 |

The Pass 1 quantizer divides by 256 and rounds to nearest, ties to even,
with no resampling, dither, gain change or envelope shaping. PCMS is set
for program 5. Its start address, frame count, one-shot mode, pitch and
envelope stay fixed. FX.SEQ retains the same events, gates, pitch and
velocity. Gameplay code, priorities, collision precedence and per-player
routing are unchanged. Every other PCM slice keeps its bytes, including
Pass 1 effects and POOWAH. Later slices and both music files relocate.
All Level 2 audio, startup logic and the SDK pin stay byte-identical.

The actual packed saving is **17,844 B**. Both input and output sample
lengths are already four-byte-aligned. FX.TON shrank from 159,180 B to
141,336 B. The final layout is contiguous, uses **462,844 of 524,288 B**
and leaves **61,444 B free**.

| Region | Half-open SCSP offsets | Bytes |
|---|---|---:|
| Reserved driver/work/DSP/PCM and FX.SEQ | `00000–246F0` | 149,232 |
| FX.TON | `246F0–46F08` | 141,336 |
| STAGE.SEQ | `46F08–50BC8` | 40,128 |
| STAGE.TON | `50BC8–70FFC` | 132,148 |
| Free tail | `70FFC–80000` | 61,444 |

PCM comparison, with output expanded to the original 16-bit scale:
peak 11,468 → 11,520 (+0.039 dB), RMS 1495.960 → 1497.858 (+0.011 dB),
and first 20 ms attack RMS +0.229 dB. The fixed −30 dB threshold crossing
moves from frame 423 to 424 (one sample, about 23 µs). Signal-to-error RMS
is 27.69 dB. There are zero saturated or rail samples. The measurements
describe the isolated PCM. Hardware listening is pending.

In GitHub Actions, open **Manual Saturn playtest build**, select
`audio/level1-sfx-pcm8-pass2` as the workflow branch, choose `stage-default`,
and use the Pass 2 commit SHA as `source_ref`. Keep the downloaded BIN and
CUE together. Use the Pass 1 parent commit to restore the PCM16 whoosh.
