# Level 1 guitar sustain auditions

Audition branch from `382b226b476b305c9ebab8e6d2ddbe763603d41b`,
the doubled-downhill commit on `feature/level1-phase3b-downhill-extension`.
It precedes visual polish `459f50e` and garage rebuild `97d07f4`. The
640-pixel downhill with its 1:5 grade, shipped audio assets, sequence and
runtime are preserved. This branch contains documentation and preview WAVs.

Both private masters matched the SHA-256 in
`assets/music/level1-custom-report.json`. Open is 89,373 frames and Mute
46,474 frames, both 44,100 Hz stereo PCM16. The private full-source
comparison puts the 2.027-second original Open first. The public comparison
starts with the shipped loop. The full original WAVs stay private.

## Listening order

| WAV | Order |
|---|---|
| open-loop-auditions.wav | Current, short, medium, long, recommended medium |
| muted-auditions.wav | Current PCM8, TPDF-dithered PCM8, source-derived PCM16 |
| score-sustained.wav | Current, short, medium, long |
| score-rapid.wav | Current, short, medium, long |
| score-palm-muted.wav | Current PCM8, TPDF-dithered PCM8, source-derived PCM16 |

Clips are separated by 400 ms of silence. Isolated open clips hold for
2.027 s each and end with a preview-only fade. The score demos render guitar
programs from the actual shipped Level 1 score. They retain note pitches, gates,
velocities, pan and pitch bends. They use linear sample interpolation at the
intended playback rate and frame-based looping, with a short approximate
release. SCSP resampler precision, hardware envelope, gain tables, mixer
and slot allocation are approximated or omitted. The WAVs use a shared gain,
play from a 44.1 kHz PCM16 container, and contain zero clipped samples.

Score windows at 480 PPQN are ticks 214080–217920 (held guitar),
236160–240000 (rapid open rhythm), and 154560–158400 (palm-muted rhythm).
The other music stems are omitted to expose the guitar comparisons.

## Open PCM16 at 22,050 Hz

The original importer capped its search at 280 ms and sought 4–12 pitch
cycles. The selected four-cycle loop left 152.653 ms of PCM and repeated
30.522 ms. The first waveform peak is at 13.24 ms, and the first 5 ms RMS
window above 90% of the strongest window starts at 59.86 ms. The layer
uses attack 31, decay rates 0, and release 31. The original attack plays
through, then the flat gated envelope makes the very short sustain repeat
easily audible.

The trials retain the source pick and 1.7× import gain. Boundary search
balances local phase correlation, RMS and slope. An eight-millisecond
raised-cosine blend affects the tail before LEA and approaches the cyclic
lead-in. Each pair below uses resampled frames and an exclusive end. The
packed estimate includes a four-byte cyclic guard and four-byte alignment.

| Variant | Start–end frames | Total PCM | Loop | Packed | Extra | Level 1 used | Free |
|---|---|---:|---:|---:|---:|---:|---:|
| Current | 2693–3366 | 152.653 ms | 30.522 ms | 6,736 B | 0 B | 462,844 B | 61,444 B |
| Short | 3300–6831 | 309.796 ms | 160.136 ms | 13,668 B | 6,932 B | 469,776 B | 54,512 B |
| Medium | 4344–10937 | 496.009 ms | 299.002 ms | 21,880 B | 15,144 B | 477,988 B | 46,300 B |
| Long | 4008–16662 | 755.646 ms | 573.878 ms | 33,328 B | 26,592 B | 489,436 B | 34,852 B |

Absolute seam steps on the normalized PCM scale are 0.1487 current,
0.0502 short, 0.0246 medium and 0.0108 long. The 3 ms seam RMS steps
(after/before) are +0.22, +0.81, +0.17 and −0.26 dB respectively. Estimated
pitch over medium sustain windows spans 131.01–131.33 Hz. Medium retains
about 775 Hz of spectral-centroid movement across its loop, versus
about 298 Hz in the short shipped repeat using the same windowing.
Loop periodicity at the root drops from 32.8 Hz to 3.34 Hz. The longer
repetition and preserved overtones are expected to reduce static buzzing.
Whether any remaining periodic swell is audible is for the audition.

Trial recommendation is medium first. Long has the smallest sample step
but a larger slope mismatch than medium and costs another 11,448 B. All
candidates preserve more than 20 KiB for lead/voice planning. Exact guard
frames, other seam metrics and estimator windows are reflected in
`measurements.json`.

## Muted one-shot

All variations use 11,025 Hz, 11,619 frames, the common import gain and
the original tail fade. The source-based undithered PCM8 reconstruction
matches the shipped sample exactly. The two PCM8 variations take 11,624 B
each. PCM16 takes 23,244 B, so its independent cost is 11,620 B and
its standalone Level 1 usage is 474,464 B, leaving 49,824 B. With the
medium open sample it leaves 34,680 B.

Relative to the same resampled floating-point source, full-sample RMS
error is −53.01 dBFS (current), −48.11 dBFS (dithered) and −101.09 dBFS
(PCM16). TPDF may decorrelate error but adds about 4.9 dB of measured
noise here. PCM16 reduces that error without changing bandwidth, gates or
attack timing. Keep the current PCM8 initially and reserve judgment for
the score audition. These are offline measurements, with hardware and
perceived quality still to be evaluated.

## Open PCM8 audition

- `open-loop-auditions-pcm8.wav` uses the same order as the original
  open comparison. Its WAV container stores unsigned PCM8, the standard
  offset representation of the signed PCM8 source samples.
- `open-long-pcm16-vs-pcm8.wav` alternates Long PCM16 and Long PCM8 twice.
  This matched comparison uses a PCM16 container for both versions.

Both render at 22,050 Hz with the original loop settings and gain. PCM8
uses nearest rounding without dither, resampling or normalization.
Long retains 16,662 frames with loop bounds [4008, 16662). Measured RMS
changes by −0.00023 dB and quantization error is 37.45 dB below signal RMS.
An eventual signed PCM8 bank version would use 16,668 B packed, saving
16,660 B relative to Long PCM16 and leaving 51,512 B of Level 1 sound RAM
free with the rest of the starting bank preserved. These files are for
offline audition.
