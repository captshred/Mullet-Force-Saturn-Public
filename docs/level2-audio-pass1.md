# Level 2 audio, single shot and polyphony

Branch: `feature/level2-audio-pass1`.
Parent: confirmed playable `c721fa189043e66ee6292398ef3fcddbb692063a`
(`feature/level2-aimed-drone-pass`). Runtime banks are committed; the original
private `MF SFX lvl2.zip` and WAV authoring files are not needed by public builds.

## Single tap and event timing

Tap A now emits **one centered straight projectile**, with zero X velocity and
the original upward velocity of six pixels/tick, damage, cooldown and approved
sprite. It consumes one of the existing 32 player-shot slots instead of three.
Successful allocation sets one transient per-player shot-event bit; allocation
failure or cooldown does not generate a fake sound. Catch-up simulation ticks
queue their events once, independently of rendering. Typical projectile pressure
per deployment falls by two thirds; the pool and worst-case draw budget remain.

The initial press still emits that single shot when A will subsequently be held.
Flame still activates at exactly twenty continuous held ticks and uses 65%
movement speed. The rounded origin, constant-width full-height body, six-tick
collision/DPS, banking, snapshot-aimed non-homing drone shots and X development
skip remain unchanged.

## Approved weapon conversions

Both source files were checked against the supplied archive: stereo, 44,100 Hz,
signed 16-bit PCM, with the stated source frame counts. Conversion averages both
channels `(L+R)/2`, rounding symmetrically to the nearest integer, ties away from
zero. No resampling, normalization, channel discard, or bit-depth reduction is
performed. Runtime PCM is mono, signed 16-bit big-endian for SCSP.

| Sample | Rate / format | Frames | PCM bytes | PCM start in SCSP |
| --- | --- | ---: | ---: | ---: |
| Canonical Level 1 explosion | 22,050 Hz / 16-bit mono, unchanged | 15,840 | 31,680 | 149,112 (`0x24678`) |
| Shot.wav | **44,100 Hz / 16-bit mono** | **22,403** | **44,806** | 180,792 (`0x2c238`) |
| Flame.wav | **44,100 Hz / 16-bit mono** | **41,239** | **82,478** | 225,600 (`0x37140`) |

Shot duration is 0.508004535 seconds. Flame duration is 0.935124717 seconds.
The requested flame loop uses **LSA=27,981**, **LEA=41,239**, expressed as the
half-open source interval **[27981,41239)** at 44.1 kHz. Ignition/attack starts at
frame zero once; sustain begins at 0.634489796 seconds and lasts 13,258 frames
(0.300634921 seconds) per hardware loop.

Only the last **128 frames (2.902494 ms)** are seam-treated. A short linear tail
crossfade approaches the original 128 samples immediately before the loop start,
so the wrap ends with original frame 27,980 followed by 27,981. All earlier frames,
including the attack and loop start, remain unchanged. The wrap sample delta falls
from 17,094 to the original adjacent-sample delta of 1,452. The requested loop
boundaries are not moved. This is a technical seam check, not a listening claim.

`assets/wingsuit/audio.json` records source/converted hashes, peaks, exact sample
layout and conversion settings. The independent validator pins all three runtime
PCM hashes. `tools/level2_audio_assets.py <private zip>` reproduces the bank;
normal builds use the committed bank and `MF_PRESERVE_AUDIO=1`.

## Explosion audit and transport repair

The canonical Level 1 barrel/world-impact path is `src/music.c`'s
`MF_WORLD_IMPACT`, `assets/cd/FX.SEQ` song 2 and `assets/cd/FX.TON` voice 2.
Its PCM remains exact, SHA256:
`2eca5219e7a0255532d46c6c0a4835dee475781787334da46bfb451363e4fa6b`.
Its tuning, gain, envelope and sequence are also retained; only relocation and
program-number remapping to bank voice 0 change.

Two defects were identified in the old Level 2 implementation:

- The compact TON set velocity, PEG and PLFO header offsets to zero and omitted
  those tables. The new bank copies all four complete shared tables from the
  proven Level 1 bank and uses valid offsets: mixer 14, velocity 32, PEG 42,
  PLFO 52, voices 56/92/128. Sequence data is now four-byte aligned as well.
- Pinned SGL `slInitSound` enables the driver's latched timing handshake. The old
  loader then wrote zero to the mode byte and issued playback through the separate
  SND command path. This could leave commands outside SGL's synchronized queue.
  Level 2 now submits **all** initialization and playback commands with supported
  `slSoundRequest` formats and `slSndFlush`, keeping SGL's handshake intact.

The pinned `LIBSGL.A` initialization object was inspected, including its 0x80 mode
write; artifact hashes and references are in `level2-audio-sdk-audit.json`.
`SND_Init` is retained for initialization/status-pointer setup before SGL takes
transport ownership; `SND_GetSeqStat` performs read-only diagnostics. No SND
playback-command writer is mixed into the SGL queue. The map-size argument uses
words for SND initialization and bytes for SGL initialization, per their headers.

The three existing `WDEATH.*` filenames are retained for disc compatibility, but
now contain the entire Level 2 SFX bank. They load once from `/ALEVEL2` during the
stage-specific handoff after old resources are released. The canonical explosion
PCM, shot PCM and flame PCM each reside once in sound RAM. Gameplay issues small
SDK control commands; it never re-reads files or uploads sample PCM per attack.

Every actual drone destruction and player life loss queues one explosion event.
Lingering explosion animation does not create further events. All such events
use the same canonical voice, through independent explosion playback controls.
Missing/read/length errors retain per-asset E108 diagnostics; initialization failure
prevents stage startup. Runtime sequence errors additionally display their control
number and driver status, e.g. `AUDIO P4 STATUS 81`.

These code/data defects are repaired and structurally validated. Actual audible
SCSP output is still unverified here; the next WebRetro/Saturn run must confirm
that the repaired explosion path is heard. Host mocks alone cannot establish that.
Level 1's audio implementation and assets are unchanged.

## Attack, sustain and release

Each player's dedicated flame control is prepared during the existing Level 2
title VBlanks: volume, bank 0, then program 2. Focus activation therefore needs
just one MIDI Note On, at note 60, to start that player's sample from frame zero.
The TON forward loop repeats the sustain indefinitely while the note stays on.
There is no finite-gate expiry, loop-sequence restart, damage-pulse retrigger, or
per-frame sample restart. A thousand-tick hold test emits one Note On.

Release, loss of focus, life loss, respawn, game over, or pause requests Note Off
for that player's control. The original fastest RR31 release avoids a long tail;
control reuse waits for a real VBlank. A later focus activation starts ignition
again. Pause stops flames; unpausing with an active held focus restarts ignition.
The two players keep independent state while referencing the same Flame PCM.
Releasing Buck does not stop Chuck, and vice versa. SDK rejection keeps requests
pending for retry instead of falsely advancing playback state.

## Polyphony and SDK limits

Pinned `SEGA_SND.H`, `SL_DEF.H` and the Sega driver documentation were inspected.
The driver has **eight playback controls, 0..7**, and **32 physical SCSP slots**.
This pass explicitly allocates all eight:

| Class | Controls | Behavior |
| --- | --- | --- |
| P1 flame | 0 | Persistent, never stolen |
| P2 flame | 1 | Persistent, never stolen |
| Shots | 2, 3 | Two overlapping one-shots; oldest shot may be replaced |
| Explosions | 4, 5, 6, 7 | Four overlapping one-shots; extra events queue |

Flame stops have first priority, then flame state changes, then explosion requests,
then shots. At most eight commands are submitted per actual hardware VBlank, through
SGL's queue. Replacing a shot stops only a shot control and waits one VBlank before
reuse. Explosions and flames are never stolen by a new shot. Explosion overflow
queues rather than interrupting a previous explosion; exceptionally large bursts
can therefore delay some sounds. Class allocation, not the unsupported legacy
sequence-priority argument, provides isolation.

The shot reuse guard is 34 ticks; explosion reuse is 49 ticks, allowing their full
sample/sequence and release. Volume defaults are shot 96, flame 80, explosion 112
on the SDK's 0..127 scale; PCM itself is not attenuated or normalized. Up to eight
principal voices coexist, with brief guarded release tails still below the physical
32-slot budget. No global per-playback stop is used.

Tests cover P1 flame + P2 shot + explosion, both flames + explosion, and both shot
instances + explosion. These are scheduler/command-stream checks; actual mixed
loudness and audible behavior require the manual playtest.

Primary references for the supported APIs/limits and native format:

- [Sega driver command interface and timing protocol](https://www.infochunk.com/saturn/segahtml_en/sndt/prog/drve/sndcmd0.htm)
- [Sega MIDI direct-control command](https://www.infochunk.com/saturn/segahtml_en/sndt/prog/drve/sndcmd_.htm)
- [SGL slSoundRequest formats](https://docs.exodusemulator.com/Archives/SSDDV1R1E/refe/func6/func175.htm)
- [Sega native tone-table format](https://docs.exodusemulator.com/Archives/SSDDV25/segahtml/sndt/tool/tone/hon/p12_10.htm)

## Exact memory and disc resources

| SCSP region | Start | Bytes | End, exclusive |
| --- | ---: | ---: | ---: |
| Driver/work/transfer/DSP/PCM-work reserve | 0 | 148,864 | 148,864 |
| WDEATH.SEQ | 148,864 | 84 | 148,948 |
| WDEATH.TON, metadata and three shared samples | 148,948 | 159,132 | 308,080 |

The linked driver remains 26,610 bytes within the lower reserve. The 40-byte MAP
buffer is temporary work RAM, not another copy of PCM in SCSP. Bank data totals
**159,216 B**; conservative reserved high-water is **308,080 / 524,288 B**, leaving
**216,208 B** contiguous. All addresses and generated sizes are checked for
alignment, bounds and overlaps.

| Resource | Parent | This pass | Change |
| --- | ---: | ---: | ---: |
| VDP1 texture bytes / definitions | 28,032 B / 18 | **28,032 B / 18** | 0 |
| Worst VDP1 object commands | 72 | **72** | 0 |
| VDP2 reservation | 434,176 B | **434,176 B** | 0 |
| Background cells/map / CRAM payload | 10,944 B / 32 B | **10,944 B / 32 B** | 0 |
| SCSP bank data | 31,788 B | **159,216 B** | +127,428 B |
| SCSP reserved high-water | 180,652 B | **308,080 B** | +127,428 B |
| `/ALEVEL2` logical payload | 70,836 B / 24 files | **198,264 B / 24 files** | +127,428 B |
| Player / hostile / drone pools | 32 / 16 / 8 | **32 / 16 / 8** | 0 |
| Simulation state | 1,484 B | **1,488 B** | +4 B shot-event mask |
| Audio scheduler counters/state | 28 B | **164 B** | +136 B |

The largest stage-read buffer is now 159,132 B and is freed after upload; this is
smaller than the existing Level 1 FX.TON read of 182,912 B. Native code/stack and
allocator overhead cannot be measured until the pinned compiler is available.
No original WAV, high-resolution art or authoring archive is added to the public repo.

## Validation and preservation

`make test` passed with **215 PASS reports**; updated targeted tests also passed.
The actual simulation, aiming, single-shot weapon, flame, audio scheduler and
runtime loader/render tests run with UBSan and abort-on-error. Checks include:

- One centered upward projectile, no lateral velocity, one event per successful
  allocation, no fake event on pool exhaustion, unchanged pool/cooldown/damage.
- No flame audio at nineteen ticks, one ignition at twenty, indefinite hold without
  retrigger, exact loop metadata, pause/release/life-loss/respawn behavior, 2P isolation.
- One explosion per drone destruction or player life loss, no animation retrigger;
  simultaneous classes, oldest-shot-only stealing, ten-event explosion burst,
  rejection retries, real-VBlank guards and clock wrap.
- Exact stereo downmix/converted hashes, canonical explosion parameters/PCM,
  complete tables, nonoverlapping SCSP layout and deterministic header/map values.
- SGL-only playback requests and retained timing mode; initialization before playback,
  bank-only file reads/DMA, per-file missing/length failures, sequence diagnostics.
- Unchanged art, origin/body seams, full-height beam collision/DPS, aiming/non-homing,
  20-tick hold/65% movement, X handoff, forty-kill transition and Level 1 equivalence.

An independent private-ZIP check confirmed the exact Shot downmix and that Flame's
entire attack and all but the final 128 frames remain unchanged. Public tests pin
the converted hashes without requiring private WAVs.

`docs/level2-audio-bank-lock.json` permits exactly the three bank files and three
Level 2 audio source files to change through exact before/after hashes. Earlier
preservation checks still validate their original baselines and the scoped new
hashes. `level2-audio-preservation.json` adds exact pins for all **21 non-audio
parent payloads**, original game/main/input/dev-skip/music/workflow sources and
snapshot aiming. The existing beam-collision digest remains exact. No preservation
check is removed or broadly exempted.

Static validators passed: `tools/validate-wingsuit.py`,
`tools/validate-level2-audio.py`, `tools/validate-arcade-fx.py`,
`tools/validate-full-gameplay-sfx2.py`, `tools/validate-sfx2.py`,
`tools/check-public.py`, `tools/check-city-neon.py`,
`tools/check-gameplay-parallax.py`, `tools/check-city-cleanup.py` (each with python3),
plus shell/Python syntax and whitespace checks.

Native compilation remains blocked by the configured SDK proxy connection on
port 8080. No new BIN/CUE, emulator/WebRetro run, real-Saturn test or SCSP listening
validation is claimed. ISO tests use structural fixtures. The next manual run
must verify audible shot/flame/explosion output, the sustain seam, stop latency,
2P isolation and mixed loudness; host tests cannot prove those acoustic results.

## Exact manual Actions build settings

Use the established working procedure:

- **Use workflow from: `main`**
- **Profile: `stage-default`**
- **Source ref: exact new commit SHA provided in delivery**

Workflow: **Manual Saturn playtest build** (`.github/workflows/build.yml`). Its
checkout uses the source SHA, so the implementation comes from this feature commit
while the workflow itself is selected from `main`. No Actions run is dispatched.
Artifact: `mullet-force-stage-default-<full SHA>`; keep matching BIN/CUE together.
Verify BUILD-INFO records that exact SHA, Level 2 wingsuit 1, preserved audio 1,
and `Dev Saturn X stage skip: 1`.

Local build with the pinned SDK and x86-64 Linux prerequisites available:

```sh
bash tools/build-stage.sh --native
make check
make test
```

Release controls: `MF_DEV_STAGE_SKIP=0 bash tools/build-stage.sh --native`.
Playtest single taps and long holds for each player, all three simultaneous-SFX
combinations, repeated close drone explosions, both players losing lives, release
and pause mid-sustain, normal forty-kill/X entry, aiming/baiting and HUD/background.
