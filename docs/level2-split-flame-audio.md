# Level 2 split Flame audio

Branch: `fix/level2-split-flame-audio`.
Parent: diagnostic `b0bd392faec051785c33d794a15efb49805da6e7`.

The old single-file Flame architecture is retired. Flame now uses a supplied
Attack one-shot and a separate whole-sample hardware-loop tone. This is a source,
bank and runtime implementation, **not a confirmed WebRetro/hardware fix**. The
required acceptance run is an audible 5–10-second hold with shots/explosions,
followed by release, reactivation and independent two-player holds.

## Approved source conversion and seam

Both uploaded WAVs matched their supplied full-file SHA256, stereo PCM16 format
and 44,100-Hz rate:

| Source | Frames | SHA256 |
| --- | ---: | --- |
| Flame attack.wav | 27,975 | `bfc55dc8ae2e4fed1362cf6ff60402ad42d61d018f704818010baac9c5615866` |
| Flame loop.wav | 13,256 | `222fd540adb224c11186ac07188957a086c0bc211b93e60916773283425274a5` |

Conversion uses the existing deterministic symmetric nearest-integer `(L+R)/2`,
ties away from zero. Runtime PCM is signed mono PCM16 big-endian. No resampling,
gain, normalization, EQ or channel discard is applied. Attack retains all 27,975
frames, **55,950 bytes**. The private ZIP/WAVs are not committed or needed to build.

The suggested loop boundary was independently recalculated. Searching start trims
0..256 and end trims 0..512, require endpoint error <=8 signed-16 counts, incoming/
outgoing slope difference <=8, and matching slope directions; then minimize total
trim. The sole candidate meeting those tight criteria is start **114**, end **310**.
The source interval `[114,12946)` leaves **12,832 frames / 25,664 bytes**, lasting
0.290975057 seconds. No crossfade is needed or applied.

| Seam measurement | Raw mono file | Selected mono loop |
| --- | ---: | ---: |
| First sample | -2,503 | 6,669 |
| Last sample | -15,028 | 6,674 |
| Wrap jump, first minus last | 12,525 | **-5** |
| Incoming final slope | -448 | **+482** |
| Outgoing first slope | -545 | **+487** |
| Slope difference | -97 | **+5** |

This removes 424 frames (about 3.20%) and preserves the supplied sustain material.
The numerical seam check is not a listening claim. The importer records search
bounds, thresholds, raw/selected metrics and source/converted hashes. A separate
private-source verification recomputed both downmixes and the exact slice without
calling the importer; it matched the committed PCM. Rebuilding from the ZIP is
idempotent. Public tests pin the converted hashes without requiring private files.

## Native Saturn tone and LEA contract

There are four one-layer tone definitions: explosion 0, Shot 1, Attack 2, Loop 3.
The complete original mixer/velocity/PEG/PLFO tables remain. Actual big-endian tone
bytes, rather than metadata alone, are decoded by `tools/validate-flame-tone.py`.

| Field | Attack | Loop |
| --- | ---: | ---: |
| Tone program / MIDI key | 2 / 60 | 3 / 61 |
| Base note / fine tune | 60 / 0 | 61 / 0 |
| SCSP PCM start, byte address | 225,640 (`0x37168`) | 281,592 (`0x44bf8`) |
| PCM format / source | signed PCM16 / DRAM | signed PCM16 / DRAM |
| LPCTL | `00`, loop off | **`01`, normal forward loop** |
| LSA, sample offset | 0 | **0** |
| LEA, exclusive sample boundary | 27,975 | **12,832** |
| AR / D1R / D2R / RR | 31 / 0 / 0 / 31 | 31 / 0 / 0 / 31 |
| DL / TL / direct routing | 0 / 0 / 7 | 0 / 0 / 7 |

Different MIDI keys with matching base notes keep both samples at native 44.1 kHz
while allowing a tiny overlap without Note Off for Attack also stopping Loop.
The Attack ends naturally at its one-shot boundary. Loop's flat envelope keeps
its level until explicit release; it has no finite sequence gate.

The pinned Sega driver writes the packed control/SA and LSA/LEA/EG words directly
to SCSP at instructions `0x38e2..0x3906`. It does not convert bytes to samples or
subtract one from LEA. The SCSP normal-loop boundary is **N**, with playable sample
indices `[0,N)`; using `N-1` would shorten the period. Sega's hardware manual also
requires the waveform value at SA+LEA to match SA+LSA. The bank therefore stores
**two cyclic lookahead samples (4 bytes)** after Loop's 12,832 playable frames:
the first two loop samples repeated. At LEA the stored value is exactly the LSA
value, including interpolation lookahead. These guards are not additional loop
frames. Alignment padding/guards are included in the bank budget.

References used for the actual format/boundary audit:

- [Sega Tone Editor binary format, ST-235-030795, pp.54–56](https://antime.kapsi.fi/sega/files/ST-235-030795.pdf)
- [Sega SCSP loop controls, sample units and endpoint matching](https://www.infochunk.com/saturn/segahtml_en/hard/scsp/hon/p04_21.htm)
- [MAME 0.280 SCSP normal-loop implementation](https://github.com/mamedev/mame/blob/mame0280/src/devices/sound/scsp.cpp): wraps on reaching LEA and carries fractional overshoot.

The byte audit checks the actual pinned 2.10 driver image and its hash when the
SDK/cached image is available; missing binaries explicitly produce SKIP. A cursor
model demonstrates one-shot termination and 34 sustain wraps over ten seconds.
Neither the model nor instruction inspection runs a Saturn or proves audibility.

## Attack to Loop and release

Audio timing uses the existing hardware-VBlank clock, independently of catch-up
simulation ticks. Focus still starts at the twentieth continuous held game tick.

1. A valid focus edge sends Attack Note On once, on that player's persistent control.
2. On a later VBlank, preselect Loop program 3. Program Change leaves the already
   sounding Attack note intact.
3. **38 VBlanks after accepted Attack activation**, send Loop Note On exactly once.
4. Attack naturally ends about **45 samples / 1.020408 ms** later. Its held key is
   retired on the next real VBlank, without addressing Loop's different key.
5. SCSP repeats Loop indefinitely. SH-2 issues no periodic Loop Note On or ignition.
6. Release sends Loop Note Off first, then Attack Note Off if still outstanding.
   It restores Attack program 2 and observes the existing real-VBlank reuse guard.
7. The next activation starts Attack again from sample zero.

Nominal timing is `38/60 = 0.633333333 s` versus Attack's `27975/44100 =
0.634353741 s`. This deliberately schedules the small overlap requested instead
of a 39-tick gap. SDK rejection preserves pending state and retries; it does not
pretend a tone started. Scheduling/driver latency and the audible handoff require
the manual playtest. Release wins over a handoff occurring on the same tick.

Controls remain **0–1 persistent flames, 2–3 shots, 4–7 explosions**. No new control
is required. Shots can steal only an older shot; explosion overflow queues. Neither
path intentionally sends Note Off, stops or replaces a flame control. P1/P2 use
separate control/channel namespaces and state. Overlap briefly requires two slots
per transitioning flame: at most ten principal voices with all eight controls
active, below 32 SCSP slots; guarded short release tails also remain within budget.
Explosion sample, parameters and volume are unchanged.

## Initial audio readiness

The prior loader returned success after request submission. It did not confirm
that the restarted CPU had consumed startup requests or that the active map and
persistent-control setup were ready. Successful `SND_RET_SET` reports submission;
it is not proof that the driver processed it. The exact cause of the user's delayed
audible startup was not captured, but that missing readiness condition is repaired.

The E108 initialization call order remains byte-pinned: sound off, padded-word-map
SND_Init, map request, slInitSound/DMA wait, dry DSP clear, SEQ/TON uploads, mode
byte zero, CPU restart, initial flush/DMA wait, then SND DSP/CDDA/total-volume calls.
Playback remains SND-only. No new SGL command architecture or unsupported SDK API
is introduced.

During **existing Level 2 title VBlanks**, a bounded nonblocking handshake now:

- Observes the pinned driver's timer heartbeat word at sound-RAM `0x8838` advance.
- Waits for its eight 16-byte command blocks at `0x700` to drain.
- Resubmits map 0 after live CPU progress; waits for consumption and checks active
  SEQ/TON descriptors against the already uploaded, transfer-complete map at `0xa000`.
- Submits DSP stop, muted CDDA and total volume 15 in order, waiting for each batch
  to be consumed.
- Prepares both flame controls' volume/bank/Attack program and confirms the setup
  batch drained before `mf_ws_audio_ready()` permits stage input/gameplay.

Driver instructions for the heartbeat, block scan/acknowledgment and cached voice
layout are pinned by tests. This code reads those fields; all requests still use
Sega's existing SND functions. It never issues a destructive hardware-check command.
There is no long sleep or fixed success delay. The existing title normally absorbs
setup; the first valid game Shot/Flame request can then submit immediately. A
120-VBlank watchdog produces a specific E108 startup-stage/ack/map failure if
progress stops, instead of silently starting a mute stage. It preserves actual
SND rejection status, queued command byte or differing map byte where available.
The watchdog is a failure bound, not a success wait.

## Useful diagnostics and preservation

Live flame diagnostics now follow the selected Attack or Loop layer, key, PCM
address, LPCTL, LSA and LEA. They retain requested/active/stopped/mismatch/releasing
states and inspect the driver's cached live EG with a full-refresh grace period.
They do not assume the old single-tone layout, select the shared SCSP monitor,
write driver voice state, or restart a stopped note. Development builds retain
the compact fault-only overlay; release builds omit it. Existing E108 and sequence
status reporting remain.

The two banks' 36-byte explosion/Shot tone parameters remain exact after normalizing
only their relocated sample addresses. Their PCM and the entire 84-byte SEQ are
unchanged. Twenty-two of twenty-four disc payloads remain exact; only TON and its
MAP size/hash change. All artwork, background, aiming/non-homing fire, centered
single tap, full-height flame/collision/DPS, twenty-tick focus/65% movement, X skip,
forty-kill clear, Level 1 and resource handoff are preserved.

Original preservation locks are unchanged and chained through
`level2-split-flame-lock.json`, which permits exactly four implementation sources
and five stage bank/metadata files. Additional exact pins retain the original
initialization call sequence, SND one-shot pool, unchanged Level 2 payloads,
Level 1 source/canonical FX, workflows and build settings. No preservation check
is broadly exempted. Tests still verify exact `/ALEVEL2` ISO placement/content.

## Exact resources

| Resource | Bytes / count |
| --- | ---: |
| Attack PCM | **55,950 / 27,975 frames** |
| Loop PCM | **25,664 / 12,832 frames** |
| Loop cyclic guard | 4 bytes / 2 lookahead samples |
| Canonical explosion PCM | 31,680 |
| Shot PCM | 44,806 |
| WDEATH.TON | **158,312**, including all headers, tables, guards and padding |
| WDEATH.SEQ | **84**, unchanged, two songs |
| SCSP bank payload, SEQ + TON | **158,396** |
| SCSP reserve before SEQ | 148,864 |
| SCSP reserved high-water | **307,260 / 524,288** |
| SCSP contiguous free | **217,028** |
| Change from diagnostic parent | **820 bytes less SCSP data** |
| Tone definitions / controls | **4 / 8** |
| `/ALEVEL2` logical payload | **197,444 bytes / 24 files** |
| VDP1 texture bytes / definitions / maximum commands | **28,032 / 18 / 72**, unchanged |
| VDP2 reservation / background payload / CRAM payload | **434,176 / 10,944 / 32**, unchanged |

Samples are stored once; no per-attack file reads, PCM uploads or allocations are
added. Fixed audio state adds 48 work-RAM bytes relative to the diagnostic parent
with 32-bit ints. Linked native code/stack and actual frame performance remain
unmeasured without the pinned compiler.

## Validation and manual build

Host tests cover exact actual tone words/PCM, mode/address/units/endian/envelope
mutation rejection, zero-LSA whole-sample guards, source-hash/downmix/trim matching,
bank regeneration idempotence, single Attack and Loop starts over ten-second
mixed-SFX holds, transition at tick 38, release/reactivation/P1/P2 independence,
release at handoff, rejected handoff retry, real-clock wrap, delayed heartbeat,
unconsumed MAP timeout, immediate first valid use and title readiness gating.
Simulation/audio/runtime also run with UBSan. These are host/structural checks.

`make test` passed with **229 PASS reports**, including the updated audio/runtime
UBSan runs. Static validators passed for wingsuit, split Level 2 audio, arcade FX,
full gameplay SFX2, SFX2, public payloads, city neon, parallax and city cleanup.
Python/shell syntax and whitespace checks passed.

The SDK setup attempt failed connecting to the configured proxy on port 8080.
No new native BIN/CUE, WebRetro playtest, real-Saturn test or listening result is
claimed. The implementation must remain **emulator-unverified** until the user
confirms 5–10 seconds of continuously audible Flame with Shot/Explosion SFX.

Manual **Saturn playtest build** settings:

- **Use workflow from: `main`**
- **Profile: `stage-default`**
- **Source ref: exact new split-flame commit SHA supplied in delivery**

No Actions run is triggered. Keep the artifact's matching BIN/CUE together; verify
BUILD-INFO's source SHA, Level 2 wingsuit 1, preserved audio 1 and development X
stage skip 1. Test both players, first entry/first shot, repeated long holds,
release/pause/death/restart, simultaneous SFX and the numerical seam by listening.
Local build when SDK access is available: `bash tools/build-stage.sh --native`,
then `make check` and `make test`. Disable development diagnostics/skip with
`MF_DEV_STAGE_SKIP=0 bash tools/build-stage.sh --native`.
