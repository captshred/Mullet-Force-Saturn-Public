# Level 2 audio runtime E108 repair

Historical report. The Flame architecture and resource figures are superseded by
[level2-split-flame-audio.md](level2-split-flame-audio.md).

Branch: `fix/level2-audio-runtime-e108`.
Parent: `feature/level2-audio-pass1` at
`4a42eea5ad2f3ee6aa768256e0d31988903f9570`.

The user's WebRetro run establishes that audio-pass1 aborts during initialization,
with `WDEATH BANK / AUDIO / EXPECT 1 GOT 0`. This repair is **emulator-unverified**:
host tests and instruction inspection do not establish a successful Saturn boot
or audible output. The old screen discarded the individual SDK result, so there
is no captured on-device raw status from that run.

## Cause and first failing operation

Audio-pass1 changed the proven `src/music.c` command path to SGL-only submission
and tested `slSoundRequest(...)` as a normalized zero-success C return. The first
such checked operation is `slSoundRequest("b", SND_MAP_CHG, 0)` (map change).
All three files have already passed reads/uploads before that expression. The
short-circuit expression returns failure before trying DSP/CDDA/volume when that
first result tests nonzero.

The actual pinned `LIBSGL.A` member `sglG15.o` was inspected rather than relying on
the previous host mock. Its success epilogue at SLPROG offset `0x5a` executes
`MOV R2,R0` (`6023`), returning the command-block pointer, **raw R0=0x25a00700**,
not a normalized zero. Its invalid-format path returns -2. Although `SL_DEF.H`
declares a `Sint8` return (the success pointer's low byte is zero), this binary
does not normalize/sign-extend that byte into the SH-2 return register. Treating
that return as an ordinary C zero-success result is unsafe at this ABI boundary.
The old mock returned a normalized integer zero and concealed the mismatch.
This identifies a code-level false-failure path at the first map request,
consistent with the observed generic E108; it is not an emulator trace of R0.

`tools/audit-level2-audio-sdk.py` interprets the real formatter instructions after
its external flush/handshake calls and pins the library section hashes. It checks
all four original startup requests and the invalid-format branch. The receipt is
`level2-audio-e108-sdk-audit.json`. It does not simulate external handshakes,
the sound CPU, or SCSP. Without the SDK archives it explicitly reports SKIP.

## Proven initialization and command ownership

Level 2 now follows Level 1's existing SND/SGL initialization pairing and order:

1. Read and size-check `WDEATH.MAP`.
2. `slSoundOffWait()`.
3. `SND_Init()` with the existing driver and a safely padded map.
4. `SND_ChgMap(0)`, preserving its actual `SndRet` result.
5. `slInitSound()`, `slDMAWait()`, and zero the same dry DSP reservation
   `[0xc000,0x1c580)` as Level 1.
6. Upload `WDEATH.SEQ` once, waiting before freeing the source.
7. Upload `WDEATH.TON` once, waiting before freeing the source.
8. Set driver byte `0x25a004e1` to zero as in Level 1, then `slSoundOnWait()`.
9. `slSndFlush()` followed by `slDMAWait()` for the initial handshake.
10. `SND_StopDsp()`.
11. `SND_SetCdDaLev(0,0)`.
12. `SND_SetTlVl(15)`.

Only after all returning operations succeed is audio marked ready. SND functions
submit **all playback commands** (`SND_SetSeqVl`, `SND_StartSeq`, `SND_StopSeq`,
`SND_CtrlDirMidi`). The scheduler checks `SND_RET_SET` (0) and retains rejected
requests for retry. No `slSoundRequest` calls or per-playback SGL queue flushes
remain. This is Level 1's established hybrid initialization, followed by SND-only
playback ownership, not concurrent SGL/SND command submission. Level 1 is unchanged.

## Actual map-size contract

The pinned `LIBSND.A` `snd_main.o` instructions at offsets `0xb0..0xc6` load
`SndIniDt.ara_sz` at structure offset 12, zero-extend it and **double it** before
copying. `SND_INI_ARA_SZ` therefore takes **16-bit words**. The 40-byte Level 2
map correctly uses **20 words**, now expressed as `MF_WS_MAP_BYTES/sizeof(Uint16)`.
`slInitSound` takes **40 bytes**. The audit verifies actual opcode bytes; the host
assertion is based on this binary contract, not the old test's assumption.

The SND copy rounds to `2*words + 4 - (2*words % 4)`: 20 words copies **44 bytes**.
The loader now supplies a four-byte-aligned **44-byte, zero-padded temporary map**
so this SDK read has valid backing. The on-disc map remains exactly 40 bytes. A
40-word argument would copy 84 bytes and would be wrong for this map. Level 1's
oversized size argument is not a reason to repeat it; its approved code is intact.
The whole initialization structure is consumed synchronously, with DMA waits
before temporary storage can expire.

## Permanent diagnostics

`mf_ws_audio_diagnostics()` exposes stage number/name, completed-stage bitmask,
`has_status`, expected value and unmodified actual result. Before every SDK stage,
the runtime writes `AUDIO nn <stage>` directly to text VRAM. This also identifies
the last reached operation if a **void** SDK wait/init call hangs. Void APIs are
not assigned invented success/failure codes; completion means the call returned.

The existing E108 screen retains per-file missing/length/read failures from
`read_asset()`. SDK status failures instead identify their exact operation, e.g.:

```text
LEVEL 2 LOAD FAILED E108
ASSET WDEATH BANK
CAUSE MAP CHANGE
EXPECT 0 GOT 1
DISC /ALEVEL2
```

The same reporting distinguishes DSP STOP, CDDA LEVEL and TOTAL VOLUME. MAP READ,
SEQ UPLOAD and TON UPLOAD have separate stage records; actual asset names and
lengths take precedence on the screen. Bounds/read errors still fail the load.
No failed load is skipped and no diagnostic sprite or gameplay workaround is added.

## Preserved data, behavior and resources

Every existing `/ALEVEL2` payload is byte-for-byte equal to the parent: **24 files,
198,264 bytes**. Shot remains signed 16-bit mono **44.1 kHz, 22,403 frames,
44,806 PCM bytes**. Flame remains signed 16-bit mono **44.1 kHz, 41,239 frames,
82,478 PCM bytes**, loop **[27981,41239)** and the exact existing **128-frame seam**.
The canonical Level 1 explosion PCM and native tone/sequence parameters remain.
No WAV conversion, bank regeneration or private ZIP is needed.

The eight-control scheduler remains: **0–1 flame, 2–3 shots, 4–7 explosions**.
Single centered tap projectiles, successful-allocation sound events, twentieth-tick
ignition, indefinite sustain, independent P1/P2 release, one explosion per death,
class isolation and shot-only oldest stealing retain their existing tests. So do
65% focus movement, full-height beam/collision, aiming/non-homing bullets, art,
banking, background, dev X skip, forty-kill handoff, `/ALEVEL2` and VDP1 restoration.

SCSP bank data remains **159,216 bytes**, reserved high-water **308,080 / 524,288**,
free contiguous sound RAM **216,208 bytes**. VDP1 remains **28,032 bytes / 18
textures / 72 maximum commands**. The map adds only four temporary padding bytes;
diagnostics use small fixed state and strings, with no gameplay allocation/I/O.
Native code/stack size remains unmeasured without the pinned compiler.

`level2-audio-e108-source-lock.json` permits exactly three implementation sources
with explicit parent/current hashes. `level2-audio-e108-preservation.json` pins all
24 payloads, both metadata files, gameplay, Level 1 source, workflow and original
bank lock. Older preservation locks remain intact and are chained through exact
before/after hashes; no check is broadly exempted or removed.

## Validation and manual build

`make test` passed with **217 PASS reports**. Static validators passed for wingsuit,
Level 2 audio, arcade FX, full gameplay SFX2, SFX2, public payloads, city neon,
parallax and city cleanup; Python/shell syntax and whitespace checks passed.

Host checks exercise twelve ordered stages, safe 44-byte map backing, all four
SDK status failures (including preservation of nonboolean code 7), no SGL command
submission, real-VBlank guards, eight-control mixes and every existing gameplay,
filesystem and renderer regression. Actual runtime error-screen tests verify the
stage and `EXPECT 0 GOT 1`. Simulation/audio/runtime also run under UBSan.
ISO structural fixtures verify exact directory and payload contents; they are not
a new compiled Saturn disc.

The native SDK setup attempt failed because the configured proxy on port 8080
could not be reached. No native BIN/CUE, emulator, hardware, audible mix or loop
listening result is claimed. The repaired build needs the user's WebRetro playtest:
first verify transition/startup, then both players' shots, ignition/sustain/release,
pause/death/restart, all simultaneous sound classes, and repeated explosions.

Use **Manual Saturn playtest build** (`.github/workflows/build.yml`):

- **Use workflow from: `main`**
- **Profile: `stage-default`**
- **Source ref: exact new repair commit SHA in the delivery**

Do not select the repair branch as the workflow source. Its exact SHA supplies
the checked-out game implementation. No Actions run is dispatched by this repair.
Keep the artifact's matching BIN/CUE together and verify BUILD-INFO's source SHA,
Level 2 wingsuit 1, preserved audio 1, and development Saturn X stage skip 1.
Local build when the pinned SDK is available: `bash tools/build-stage.sh --native`,
then `make check` and `make test`. Release skip is disabled with
`MF_DEV_STAGE_SKIP=0 bash tools/build-stage.sh --native`.
