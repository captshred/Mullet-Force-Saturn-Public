# Level 1 music mix pass 1

This experiment starts at `5cdafa491cad5f785001147e8af5092a62e90324`. It changes the Level 1 music tone bank and its allocation metadata. The sequence, PCM payloads, Medium open-guitar loop, muted guitar, Level 1 FX, Level 2 audio, E108 code, rendering, and gameplay data match the source commit byte for byte.

## Drum attenuation

| Program | Instrument | Tone TL before → after |
| --- | --- | --- |
| 3 | Kick | 2 → 4 |
| 4 | Snare | 4 → 6 |
| 5 | Closed hi-hat | 14 → 16 |
| 6 | Open hi-hat | 14 → 16 |
| 7 | Crash | 18 → 20 |
| 8 | Ride | 16 → 18 |
| 9 | China | 18 → 20 |
| 10 | High tom | 7 → 9 |
| 11 | Mid tom | 7 → 9 |
| 12 | Low tom | 7 → 9 |

The pinned driver resolves this to one effective attenuation step, nominally −0.75 dB or 8.3% lower amplitude. Adding one tone TL count in a separate probe attenuated the odd-base tom TLs while leaving even-base drum TLs unaffected. The two-count adjustment applies the same nominal reduction across the kit. Ordinary measured notes fell by 8.1–8.6% after gain rounding. The quietest measured snare hits retained their old effective gain. The closed hi-hat has a mapped tone but the score does not trigger it, so its change is verified from bank metadata.

## Bass

Bass CC7 and CC11 are both 127 before and after. Tone TL is 0 and the direct send is 7 in both builds. The existing PCM has a peak of 35.2% full scale with its original baked gain. The bank now selects a bass-only velocity curve. Captured native gain coefficients changed from 40 to 134, 52 to 173, and 112 to 318 across the three played velocity classes, equivalent to +10.50, +10.44, and +9.06 dB respectively. The velocity events, tuning, envelope, and PCM are identical.

## Validation

The Level 1 allocation grew by 12 bytes, from 477,988 to 478,000 of 524,288 bytes. The bass curve takes 10 bytes and the bank adds two alignment bytes. Free RAM is 46,288 bytes. The native `stage-default` build, `make check`, and `make test` passed.

Matched 15,200-frame Yabause combat runs produced 5,147 Level 1 music note-ons each, with identical ordered note identities. 4,838 note-ons landed in the same video frame and the other 309 were within one frame. The stored sequence, including note timing and pitch bends, is byte-identical. Both guitar gain traces matched on all same-frame note-on pairs. The combined audio peak was 20,514 before and 21,299 after out of 32,768. Neither run hit a digital clipping rail. Both runs reached 17 active SCSP slots out of 32, and music key-off counts and driver call sites matched. The combat runs had small differences in FX event counts and frame placement, so byte identity of the FX assets and logic is the preservation check. Listening and behavior on physical Saturn hardware remain unverified.

The [comparison WAV](audio-previews/level1-music-mix-pass1.wav) contains 14 seconds of the baseline music, one second of silence, and the same passage from the experimental build. Both excerpts use the same gain and omit combat FX.
