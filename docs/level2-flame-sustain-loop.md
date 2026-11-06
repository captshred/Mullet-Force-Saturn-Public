# Level 2 flame sustain investigation and diagnostic build

Historical report. The Flame architecture and resource figures are superseded by
[level2-split-flame-audio.md](level2-split-flame-audio.md).

Branch: `fix/level2-flame-sustain-loop`.
Parent: confirmed WebRetro-loading audio repair
`2cae6ea6e496be85ecaa3253081a251e0a6ac9cc`.

**The audible sustain failure is not yet repaired or reproduced here.** The user's
WebRetro result establishes that the visual flame continues while sound stops.
The committed tone audit did not identify an incorrect LPCTL, LSA, LEA, sample
format, sample address or decaying envelope. This change supplies a focused live
voice diagnostic for the next run, instead of changing valid fields speculatively
or claiming a host test proves the runtime issue solved.

## Actual tone and pinned-driver audit

`tools/validate-flame-tone.py` decodes the actual bank bytes independently of the
importer and JSON. It follows the bank's voice table to program 2 at offset 128,
then the single 32-byte layer at offset 132. Native words are big-endian.

| Field | Actual encoding | Interpretation |
| --- | --- | --- |
| Packed control/SA | voice bytes 6–9: `00 21 2b 6c` | bank-relative SA 76,652 bytes; LPCTL bits 6:5 = `01` |
| SCSP control/SA after relocation | `00 23 71 40` | absolute sound-RAM SA 225,600 (`0x37140`) |
| PCM8B / SSCTL | 0 / 0 | signed PCM16, external waveform RAM |
| LSA | voice bytes 10–11: `6d 4d` | 27,981 samples from SA |
| LEA | voice bytes 12–13: `a1 17` | 41,239 samples from SA |
| Envelope words | `001f 001f` | AR31, D1R0, D2R0, RR31, DL0, KRS0, EGHOLD0, LPSLNK0 |
| Tuning/output | base note 60, fine 0, TL0, DISDL7 | native 44.1 kHz at note 60; full direct routing |

LSA/LEA count samples, not bytes; SA counts bytes. The 16-bit LEA is unsigned;
41,239 fits the hardware register. The inherited explosion envelope has zero
Decay1/Decay2 rates; the audit provides no evidence that it fades this held note.
EGHOLD is not required to make those zero decay rates infinite. Enabling it without
evidence would not explain a missing hardware loop.

Pinned driver SHA256:
`68890ee4a49fd0c341bc3f0a48643e4db4b175df0b0d7dacfeb88306340052b6`.
Instruction inspection at `0x38e2..0x3906` shows that the driver adds the bank base
to the packed control/SA longword, writes it to SCSP, and copies LSA/LEA and both
EG words verbatim. These opcodes and the diagnostic work layout are tested against
the actual pinned image when available; absent images explicitly report SKIP.
The external disassembler used for inspection stays in uncommitted `work/`.

Primary references:

- [Sega Tone Editor file-format addendum, ST-235-030795, pp.54–56](https://antime.kapsi.fi/sega/files/ST-235-030795.pdf)
- [Sega SCSP loop controls and address units](https://www.infochunk.com/saturn/segahtml_en/hard/scsp/hon/p04_21.htm)
- [Sega SCSP envelope behavior](https://www.infochunk.com/saturn/segahtml_en/hard/scsp/hon/p04_22.htm)

The existing one-tone architecture is retained: one Note On starts frame zero;
the waveform reaches LSA after about 0.6345 seconds and first wraps at LEA after
about 0.9351 seconds. SCSP normal looping should repeat `[27981,41239)` until Note
Off. There is no second tone, host-timed attack/sustain handoff, periodic replay,
restart-on-error, or ignition retrigger added. The live cause of silence remains
unknown until the failing state is observed.

## Read-only runtime diagnostic

`mf_ws_audio_flame_diagnostics(player)` exposes independent P1/P2 records:
requested focus, elapsed hardware VBlanks, matching slot mask, active-EG slot mask,
actual SCSP control word/SA/LSA/LEA and cached driver EG flags. State distinguishes:

- OFF: no held note.
- REQUESTED: focus requested but Note On is pending, or driver observation pending.
- ATTACK: acknowledged note, live cached EG and matching loop registers, age 12–38.
- SUSTAIN: the same checks after 39 VBlanks at the existing 60-Hz timing.
- STOPPED: an acknowledged held note has no matching live cached EG after grace.
- MISMATCH: the owned slot has a wrong SA, PCM/source format, LPCTL, LSA or LEA.
- RELEASING: Note Off is pending while focus is no longer requested.

ATTACK/SUSTAIN are **elapsed-time estimates with driver activity**, not hardware
cursor measurements or proof of audible output. Sequence-play mode is not used
as a proxy for a direct-MIDI note's lifetime.

Ownership checks use driver 2.10 slot records at sound-RAM `0x8000 + 64*slot`:
channel/note at +2, control number at +6, layer pointer at +8, and cached EG/held
flags at +0x3a. SCSP registers are read only for matching owned layers. The cache
activity mask 6 is taken from the actual timer instructions at `0x17e4..0x1812`.
Changing ownership/cache records are ignored for that observation. The driver
refreshes one slot per 192-sample interrupt, about 139ms for all 32; a 12-VBlank
grace allows a full refresh before reporting an unexpected stop.

The diagnostic **does not write** SCSP registers, shared monitor selection, driver
work, requests, PCM or commands. In particular it does not race the 68K's shared
`0x100408` monitor selector. It never recovers by retriggering the flame.

Development builds (`MF_DEV_STAGE_SKIP=1`, the existing stage-default profile)
show one small line only on a detected fault, for example:

```text
FLAME P1 STOP LP1 EG08
```

`STOP` means the requested held note lost cached live EG activity; `TONE` means
register configuration differs from the intended loop. `LP` is the actual loop
mode and `EG` is the raw low byte of cached driver flags. The line clears when
no fault is present. Release builds compile the overlay out; the internal state
remains available. Existing E108 and sequence error reporting remain intact.

For the next WebRetro run, hold A for several seconds and record whether this
line appears, its complete text, which player is affected, whether it happens
before/at/after the first approximately 0.935-second wrap, and whether a stationary
hold without explosions behaves the same. If audio stops with no fault line,
the cached EG/register checks still see a valid held voice; cursor/output-level
inspection would then be needed. That outcome must not be called a successful loop.

## Preservation and resources

All 24 `/ALEVEL2` payloads and metadata remain byte-for-byte unchanged. Flame
remains **41,239 frames / 82,478 PCM bytes**, including the exact **128-frame seam**.
Shot remains **22,403 frames / 44,806 bytes**; both are signed PCM16 mono, 44.1 kHz.
The canonical explosion and its volume are unchanged. The whole TON remains
**159,132 bytes**. Its approved sustain is substantial audio, not silence
(PCM RMS approximately 7,933 versus 7,394 in the attack, on the signed-16 scale).

Controls remain **0–1 flames, 2–3 shots, 4–7 explosions**. Neither shot nor explosion
code intentionally stops or replaces flame controls. Independent P1/P2 release,
single centered tap shot, aiming, visual flame/collision/DPS, focus timing/movement,
X skip, player art, Level 1, handoff, `/ALEVEL2` and renderer are preserved.
The exact E108 initializer and SND request/pool code are hash-pinned unchanged,
except clearing the newly added diagnostic state during initialization.

SCSP high-water remains **308,080 / 524,288 bytes**, free **216,208 bytes**. VDP1
remains **28,032 bytes / 18 textures / 72 maximum commands**. Diagnostics add
**104 bytes of fixed state** with 32-bit ints, plus unmeasured native code/stack.
There are no gameplay allocations, PCM duplication, extra slots or file reads.

`level2-flame-sustain-source-lock.json` adds exact before/after exceptions for
only the two audio source/header files and runtime diagnostic display. Earlier
preservation locks remain intact and chained, including all payloads and Level 1.

## Validation and build status

The native decoder rejects disabled/wrong loop mode, swapped/incorrect addresses,
PCM format, SA and envelope mutations in the actual bank, independent of JSON.
A documented-register cursor model wraps 24 times over eight seconds; **this is
not emulator or audible-output evidence**. Host tests cover live/absent driver
EG, startup-cache grace, actual LPCTL mismatch, multiple-second holds without
retriggering, independent player ownership/release and development-only overlay.
Existing initialization failures, polyphony, gameplay, filesystem, rendering and
UBSan checks remain active.

`make test` passed with **227 PASS reports**, including UBSan and both development/
release overlay configurations. Static validators passed for wingsuit, Level 2
audio, arcade FX, full gameplay SFX2, SFX2, public payloads, city neon, parallax
and city cleanup. Python/shell syntax and whitespace checks passed.

SDK setup failed at the configured proxy on port 8080. No new native BIN/CUE,
WebRetro session, hardware test, SCSP listening or confirmed sustain repair is
claimed. The next useful validation is the user's diagnostic WebRetro build.

Manual Actions settings:

- **Use workflow from: `main`**
- **Profile: `stage-default`**
- **Source ref: exact new commit SHA supplied in delivery**

No Actions run is triggered. Existing branches are not updated. Local build when
the pinned SDK is available: `bash tools/build-stage.sh --native`, then `make check`
and `make test`. Disable development diagnostics/skip with
`MF_DEV_STAGE_SKIP=0 bash tools/build-stage.sh --native`.
