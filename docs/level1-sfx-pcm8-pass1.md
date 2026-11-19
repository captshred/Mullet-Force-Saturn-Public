# Level 1 signed PCM8 SFX trial

Experimental branch `audio/level1-sfx-pcm8-pass1` starts at hardware-approved
`342595360d8c0d82377b1b0a44171cef0d5ef341`
(`the-one-e108-fixed-definitive`). The parent commit retains the original
PCM16 bank and map for rollback.

| FX program / song | Sound | PCM16 payload | PCM8 payload | Packed bytes saved | Duration |
|---|---|---:|---:|---:|---:|
| 0 | Nonlethal impact, including ordinary jab hits | 16,088 B | 8,044 B | 8,044 B | 0.36481 s |
| 2 | Inorganic destruction explosion | 31,680 B | 15,840 B | 15,840 B | 0.71837 s |
| 7 | Bat swing | 33,466 B | 16,733 B | 16,732 B | 0.75887 s |

All three retain 22,050 Hz mono, the original frames and key/root tuning.
The separate jab-initiation whoosh (program 5) retains PCM16. The PCMS bit
is set on programs 0, 2 and 7. FX.SEQ is byte-identical, and the new TON
retains all envelopes, gains, flags other than PCMS, and frame-based LSA/LEA.
The other SFX have identical payloads and retained adjacent bytes, with
bank-relative start addresses updated where needed.

## Verified Level 1 layout

The reserved prefix and FX.SEQ stay in place. Addresses below are half-open
offsets from SH-2 sound RAM base `0x25A00000`.

| Range | Contents | Bytes |
|---|---|---:|
| `0x00000–0x24580` | Driver/work, transfer, DSP and PCM reservations | 148,864 |
| `0x24580–0x246F0` | FX.SEQ | 368 |
| `0x246F0–0x4B4BC` | FX.TON | 159,180 |
| `0x4B4BC–0x5517C` | STAGE.SEQ | 40,128 |
| `0x5517C–0x755B0` | STAGE.TON | 132,148 |
| `0x755B0–0x80000` | Free tail | 43,600 |

The reserved/mapped span is **480,688 of 524,288 bytes**, down from 521,304.
The compacted bank saves **40,616 bytes** after four-byte alignment, with
no inter-bank gap or overlap. CUSTOM.MAP remains a 56-byte file using the
same SCSP driver/work area. Level 2 keeps **506,660 mapped and 17,628 free**.
STAGE.SEQ and STAGE.TON are relocated byte-for-byte. The Level 2 folders,
POOWAH and all other PCM, both music banks, sound driver and SDK pin, game
and rendering code, priorities, controls, suppression, and E108 startup and
recovery logic are preserved.

## PCM measurements

Each signed 16-bit sample was divided by 256 and rounded to nearest,
ties-to-even. Conversion used no dither, resampling, normalization, gain
change or envelope shaping. PCM8 was then expanded by 256 for comparison
on the original 16-bit scale. Attack RMS is the 20 ms window beginning at
the original waveform's first crossing of −30 dB relative to its peak.

| Sound | Peak before → after | RMS before → after | Attack RMS change | Signal/error RMS | Clipped / rail samples |
|---|---:|---:|---:|---:|---:|
| Nonlethal impact | 13,107 → 13,056 | 2641.792 → 2643.188 | −0.00324 dB | 32.86 dB | 0 / 0 |
| Inorganic explosion | 13,107 → 13,056 | 5191.019 → 5192.378 | +0.00094 dB | 36.98 dB | 0 / 0 |
| Bat swing | 12,451 → 12,544 | 2523.001 → 2525.085 | +0.05810 dB | 30.86 dB | 0 / 0 |

Threshold crossings were unchanged at frames 124, 305 and 900,
respectively. Whole-effect RMS changed by less than 0.008 dB for each sound.
Peak changed by at most 0.065 dB. Quantization error was at most 128 counts
on the signed 16-bit scale. Quiet tails, especially the bat swing, may reveal
quantization even with closely matched levels. These measurements establish
the level and timing differences. Perceived punch and any tail roughness
remain for hardware listening.

The deterministic repacker is `tools/level1-sfx-pcm8-pass1.py`. Measurements
and per-sample hashes are under `level1_sfx_pcm8_pass1` in
`assets/music/report.json`. Earlier report sections retain their historical
POOWAH provenance and addresses.

## Native validation and emulator comparison

- Native `stage-default` discs for the baseline and trial each contained 413
  files. Only `FX.TON`, `CUSTOM.MAP` and the linked `0.BIN` differed.
  Both executables contain the identical 26,610-byte SDK sound driver.
- Matched 8,000-frame Yabause HLE combat captures had identical ordered
  Level 1 music and SFX starts after accounting for relocated addresses
  (2,263 music and 465 SFX starts, including 102 nonlethal impacts, one
  explosion and 56 bat swings). Note key, owner and attenuation matched.
  The captured music stem was byte-identical. All 20 POOWAH plays reached
  the natural sample end with no early key-off. The final stereo mix peaked at
  17,767 before and 17,761 after on the 16-bit scale, with zero rail samples.
- A second 8,000-frame capture included pause and transition. All three
  POOWAH plays completed, the Level 2 music began at frame 3,347 in both
  builds, and all 2,849 observed Level 2 music starts matched. The final stereo
  mix was byte-identical from frame 3,500 through the end.
- A separate real-driver diagnostic exercised isolated one-shots and
  competing effects during POOWAH protection. The 54 SFX and 706 music
  starts matched in order, tuning and attenuation over the common capture
  interval. The first three converted one-shots matched in VBlank timing
  relative to the differing emulator boot offsets. A few other events
  varied by one captured VBlank. All 12 POOWAH plays in each run reached
  their natural end with no early key-off.
- Six independent cold processes and three warm resets reached both levels
  and completed 180 additional Level 2 frames under input with zero
  reported startup errors. These use the pinned Yabause HLE probe.
- Rendering tests exercise the unchanged game paths. Sampled screenshots
  matched at 10 of 13 combat frames and 11 of 13 pause/transition frames.
  Differences were at two shared boot/gallery frames and one localized
  combat-frame region. All sampled Level 2 screenshots in the transition
  capture matched. Physical Saturn listening and startup verification remain
  pending.

## Build and rollback

In GitHub Actions, select **Manual Saturn playtest build**, choose
`audio/level1-sfx-pcm8-pass1` as the workflow branch, select
`stage-default`, and enter the experimental commit SHA as `source_ref`.
Download the playable artifact and keep the BIN and CUE together.
The same profile builds locally with
`bash tools/build-stage.sh --native && make check && make test`.

To return to the original audio, run the same profile from
`the-one-e108-fixed-definitive`. No new tag or merged baseline is needed.
