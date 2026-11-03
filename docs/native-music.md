> Current torch SFX bank, shared hiss port and expanded RAM/voice budget:
> [charged torch update](torch-update.md). Music gain/data remain unchanged.

> Current audio balance and co-op mix limits: [co-op update](coop-update.md).
> The implementation history below describes the original native music integration.

# Drop Zone — native Saturn sequenced stage music

## Source inspection

The unchanged uploaded MIDI is `assets/music/drop-zone.mid` (48,706 bytes).
It is SMF format 1, six tracks, PPQN 480, 279,840 ticks / **213.292299 seconds**.
Track/channel numbers below are human-facing; GM programs are **zero-based**.

| Track | MIDI channel | Name / GM program | Notes | Bends |
|---|---|---|---:|---:|
| 0 | — | Drop Zone conductor | 0 | 0 |
| 1 | 1 | Distortion Guitar / 30 | 2,025 | 598 |
| 2 | 3 | Distortion Guitar / 30 | 2,023 | 598 |
| 3 | 5 | Electric Bass / 36 (GM Slap Bass 1) | 865 | 10 |
| 4 | 7 | Overdriven Guitar / 29 | 100 | 0 |
| 5 | 9 | Overdriven Guitar / 29 | 107 | 0 |

**Channel 9 is melodic. There is no channel-10 percussion in this MIDI.**
There are 5,120 paired notes, no unmatched offs, no unclosed notes and no
same-key overlapping notes. Maximum held-note polyphony is **11**.

One tempo event at tick 0: 365,853 microseconds/quarter, **164.000295 BPM**;
there are no later tempo changes. Meter is 4/4 at tick 0, 3/4 at 151,680 and
4/4 again at 153,120. Meter metadata does not change the absolute note clock.

There are **1,206 pitch bends**: channels 1/3 each range 0..+2047, channel 5
0..+682, measured relative to MIDI center 8192. Every used channel has RPN
101=0, 100=0, Data Entry 6=6: a **six-semitone** bend sensitivity, not the
usual default two semitones. There is no sustain pedal, aftertouch or SysEx.
Full track/event/controller statistics are in `assets/music/midi-report.json`;
the generation/voice/memory report is `assets/music/report.json`.

## Converter and driver choice

The game keeps the pinned Jo Engine/SGL 3.02j SDK and Sega **SDDRVS 2.10**
68000 sound driver. The driver reads native SEQ gates/control events and plays
TON sample instruments on the **SCSP**. SH-2 code only initializes banks and
sends transport/SFX commands. No SH-2 oscillator mixer, new sound driver,
full-song WAV, CD-DA track or pre-rendered song is used.

We evaluated `jfsantos/mid2seq` at
`67072f9a99ba4abbb859ebebc6859396415628d6`, then vendored its BSD-licensed C
converter and Python TON builder with attribution. Its C converter is format-0
only and collapses tempo maps. Our format-1 normalizer and small converter
patch preserve tempo segments, stable same-tick initialization, and round bends
to the native seven-bit representation. Paired 0x82 markers implement native
sequence looping; tempo-loop offset 8 restarts the entire tempo map.
See `third_party/mid2seq/UPSTREAM.md` for the evaluation and limitations.

The score places its initial chords before program changes at the same tick.
Normalization puts same-tick program/RPN setup first so those notes use the
explicit intended instruments. Absolute tick positions are unchanged.

## Editable mapping and original instruments

`assets/music/config.json` is the editable mapping, bank and mix configuration.

| Source | TON voice | Original instrument |
|---|---:|---|
| Channels 1/3, program 30 | 0 | Crunch rhythm: shaped, saturated harmonic PCM cycle |
| Channels 7/9, program 29 | 1 | Sustaining harmonic lead PCM cycle |
| Channel 5, program 36 | 2 | Punchy low-harmonic bass PCM cycle |
| Drum notes 35/36 | 3 | Swept-sine/noise kick |
| Drum notes 38/40 | 4 | Noise/tone snare |
| Drum notes 42/44 | 5 | Short metallic/noise closed hi-hat |
| Drum note 46 | 6 | Longer metallic/noise open hi-hat |
| Drum notes 49/51/57 | 7 | Metallic/noise cymbal |

The five requested drum sounds are available in the bank but this song does
not play them. No extra orchestration or drum part was added to the source.
Future percussion on channel 10 is routed separately to channels 10..14,
voice/root 60 per drum. Alternative GM kicks/snares/cymbals use the corresponding
starter sound; simultaneous same-key drum-route collisions are rejected for
explicit remapping, never silently truncated. There is no automatic hi-hat choke.

No instrument bank was supplied or downloaded. `tools/music.py` creates the
waveforms and deterministic seeded percussion, then calls the upstream TON
builder. Percussion is generated at the SCSP's 44,100 Hz unity clock; this
avoids the upstream kit's 22,050 Hz drum-rate mismatch. Melodic cycles use A2,
401 samples (109.975 Hz, about -0.39 cents from equal temperament).

Note-on times, durations and velocities survive conversion exactly. Native SEQ
stores only seven-bit bends: nearest rounding loses at most **4.6875 cents** at
six-semitone sensitivity for this file. Release velocity has no gated-SEQ field
and is omitted (source offs use 64). Names, key/meter notation stay in the source
and reports. Source RPN bend range is consumed into TON headers. Other unsupported
events are listed in the generated report. Unmapped programs/drums, open or
same-key-overlapping notes, zero gates, sustain requiring gate baking, changing
bend ranges and excessive polyphony fail conversion instead of producing stuck
notes. No unsupported sound controls occur in this source.

## Sound RAM and voice budget

The map preserves the compatible SGL boot/work/DSP reservations. All audible
banks are generated originals; no commercial example banks or samples are used.
All DMA sources stay allocated until `slDMAWait`, and files/addresses are aligned.

| Sound RAM start | Contents | Bytes |
|---|---|---:|
| 0x00000 | Existing 26,610-byte driver plus boot/stack/work reserve | 45,056 |
| 0x0B000 | Transfer/work reserve | 4,096 |
| 0x0C000 | DSP RAM reserve, silent/unused | 65,600 |
| 0x1C040 | DSP program reserve, silent/unused | 1,344 |
| 0x1C580 | PCM/work reserve for future use | 32,768 |
| 0x24580 | Three non-looping SFX sequences (bank 0) | 124 |
| 0x246F0 | Original gameplay SFX tone bank (bank 0) | 34,556 |
| 0x2CFDC | Drop Zone stage sequence (bank 1) | 29,528 |
| 0x37040 | Music/percussion bank (bank 1) | 70,676 |

Complete reserved/payload areas: **283,748 / 524,288 bytes**. Highest occupied
address is 296,020, leaving a contiguous tail of 228,268 bytes; total unmapped
space, including gaps, is 240,540 bytes. No PCM streaming is active.

Each music note uses one PCM layer/SCSP slot, not multi-slot FM. All envelopes
have finite, fast RR=31 releases. A conservative 50ms release window gives a
peak of **22 music slots**, under the configured 24-slot music budget. Three
SFX kinds have one active sequence each; allowing three additional interrupted
SFX release tails totals at most 28 slots for this song, leaving four of 32 as
headroom. SFX priority 31 exceeds music priority 8, with the existing driver
handling note release and allocation. Long-release changes require rebudgeting.
The loop explicitly clears notes and bend state before replaying initialization.

## Runtime behavior and reproduction

Music begins with Start. It loops entirely in the Sega driver. Start pause and
resume call the SDK's native SND_PauseSeq/SND_ContSeq for fixed control ports
0..3 (music, punch, jump, impact), including SFX. A partial-command mask retries
only rejected ports and handles a changed pause request without duplicate starts.
No second SH-2 song clock advances while paused. Effects use the same driver as finite, non-looping
sequences and fixed port ownership. Runtime commands exclusively use the pinned SDK
LIBSND interface after SGL initialization/flush. This avoids SGL auto-allocation
reusing one not-yet-acknowledged free control port for simultaneous effects.
Music volume is 82/127; SFX 112/127, with
per-channel pan/volume and per-instrument attenuation editable in the JSON.
The centralized `linear_mix` configuration now scales generated music PCM by
1.50 and every gameplay SFX by 0.75 before a shared 0.90 headroom multiplier.
Final PCM gains relative to the preceding build are 1.35 and 0.675: the requested
music-to-SFX ratio changes by exactly 2x. The unchanged driver sequence levels
are not misrepresented as linear-amplitude controls. Without headroom the music
bank's 22,575 peak would reach 33,862.5 and exceed signed PCM16; the actual final
peak is 30,476. Effects peak at 13,063. No sample is clamped. Bank metadata,
sample tuning, note times/gates/velocities, voice counts and byte sizes are
unchanged. Buck, enemy and barrel sounds share the same three scaled SFX programs.
This is a data-validated starting mix; combined hardware output has not been
listening-tested. See `assets/music/report.json` for exact measurements.

`make native` (or Docker `make`) runs `tools/music.py` before compiling, including
compiling the vendored converter with host C. Python 3 standard library and a
host C compiler are sufficient; no mido, SoundFont, DAW or audio renderer is a
build dependency. `make check` independently decodes every emitted note/bend,
checks tempo/loop/TON/MAP/voice budgets, and verifies all payloads inside the ISO.
`make test` includes converter fixtures for tempo changes, long gates/silence,
seven-bit bends, percussion routes, rejection cases, and mocked native transport.
The MIDI, JSON, original waveform scripts, converter sources, license, reports
and build integration are committed for future songs. Change the source path
and explicit channel/program mapping for the next MIDI, then rebuild.

Compilation, data validation and mocked command tests do **not** establish actual
audio playback. This task has not listened to this executable in an emulator or
on hardware. Verify native playback, loops, bends, timbres, note release, mix,
repeated pause/resume during held chords, concurrent punch/jump/impact effects
and absence of dropped/stuck notes in OpenEmu and on Saturn/SAROO before claiming
those results. C diagnostics show whether native banks initialized, not audibility.
