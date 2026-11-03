> Historical source report for b45528b. Current HQ integration: [hq-custom-sfx-integration.md](hq-custom-sfx-integration.md). Memory and runtime figures below describe the earlier source build.

# Custom combat SFX — latest gameplay, original PCM music

## Base and build

Branch `custom-combat-sfx` starts from **8c339aca6cefffeb9d15679d97bb8a26ffd262de**
(`hq-jump-animation-test`), the newest gameplay tip found during integration.
Its linear ancestry includes HQ jump/kick and torch poses, jab cohesion/repeat
input, attack sequencing, planted bat momentum, HQ combat poses, and the prior
running/dashing/aluminum-bat/stride/background upgrades. No older FM gameplay
or sprite files were copied over this baseline. Main and earlier branches remain.

```
make custom-native
make check
make test
```

Docker equivalent: `bash tools/build-custom-combat.sh`. The profile enables the
full HQ-jump gameplay configuration, not the historical default starter graphics.
`BUILD-INFO.txt` records every actual enabled setting and the source fingerprint.
**Original PCM Drop Zone is used, not the experimental FM bank.** MIDI, STAGE.SEQ,
STAGE.TON and music levels are byte-identical to the gameplay parent. All five
parts, note gates, velocities and bends remain. The build regenerates the SFX
bank deterministically from the committed WAVs; no external audio tool is needed.

## Supplied assets and conversion

The actual user-supplied `MF SFX1.zip` WAVs are preserved byte-for-byte in
`assets/sfx/custom-combat/`. Files are selected by name; Mac metadata is ignored.
No synthesized replacements, lossy encoding, compression or resampling are used.
Stereo files are averaged to mono; CONNECT was already mono. All use signed
PCM16 at **44,100 Hz**, the SCSP unity clock, with root/key 60 and one slot/note.
Only near-silent padding is trimmed (threshold max of one PCM16 count and 0.0001
of the mono peak), with 16-frame leading and 96-frame trailing fades to zero.
One-shot SEQ gates include the entire sample plus at least 16.7 ms of margin.

| File / purpose | Frames after trim | Duration | Final PCM16 peak | TON / song |
|---|---:|---:|---:|---:|
| Jab_1.wav / jab initiation | 17,844 | .404626 s | 11,468 | 5 |
| CONNECT_1.wav / confirmed player damage | 20,912 | .474195 s | 14,745 | 6 |
| bat woosh_1.wav / bat initiation | 22,978 | .521043 s | 12,451 | 7 |

`tools/custom_sfx.py` documents normalization, exact trimming and edge fades.
`assets/music/report.json` records source SHA-256, original channels/frames, all
conversion parameters, output hashes and resource sizes. The targets are .35,
.45 and .38 of signed PCM16 full scale respectively. Driver SFX volume remains
112 and the existing linear SFX multiplier remains .57375; music gain is unchanged.
Original jump, enemy-inflicted impact, ignition and shared hiss PCM/envelopes are
unchanged. Their original five TON voices are retained, including the now-unused
legacy punch whoosh, rather than discarding restoration/reference material.

## Events and interruptible playback

Game collision/attack code emits separate jab/bat/CONNECT bits for each actor.
These do not change input, timing, animation, hitboxes, physics, HP or scoring.
Fresh and deliberately buffered jabs emit on initiation. Bat whoosh emits once
on actual bat initiation, including running, planted and aerial bats; carrying
or running alone does not trigger it. Aerial kicks have no jab whoosh.
Confirmed melee damage to enemies or drums, direct torch damage and subsequent
burn damage emit CONNECT attributed to the responsible player. Misses, movement,
non-damaging contact and stale overlapping hitboxes do not. Existing hit masks
remain authoritative; multiple targets on one tick coalesce to one impact.
Further CONNECT requests within four VBlanks for that actor coalesce, without
changing damage or adding an attack/input cooldown. Legitimate new attacks reset
that audio coalescing guard. Burn ownership is audio-only bookkeeping.

Native control ports are fixed:

| Port | Owner |
|---:|---|
| 0 | Original PCM music |
| 1 | Shared existing torch ignition |
| 2 | Shared original jump |
| 3 | Shared original enemy-inflicted impact |
| 4 | Shared original torch hiss |
| 5 | Buck's jab / bat / CONNECT |
| 6 | Chuck's jab / bat / CONNECT |

A hit supersedes only its owner's current whoosh. The transport queues that
port's native StopSeq, retries rejected stops, then waits **one real VBlank**
for RR=31 release before starting CONNECT. Catch-up simulation steps at the same
VBlank cannot bypass the guard. The observed CONNECT starts one capture frame
after collision; the old whoosh is no longer active then. This avoids a hard
waveform cut or overlapping the full whoosh with impact. No direct sound-RAM
writes, replacement sound driver, SH-2 mixer or music-voice deletion is used.

On a same-tick initiation and hit, CONNECT takes precedence and no zero-duration
whoosh is queued. A free port starts a miss whoosh immediately, and it finishes
naturally. A rapid repeat that interrupts its own still-playing sample uses the
same one-VBlank handoff (about 16.7 ms); gameplay starts without delay. Another
player's unrelated sound continues independently. Pause/resume includes both
combat ports with per-command retries; canceled pending hits do not reappear on
resume. The pending state cannot start CONNECT before its StopSeq is accepted.

## Resources and allocation limitations

FX.TON **170,564 bytes**, FX.SEQ **328 bytes**, original music TON **70,676 bytes**,
SEQ **29,528 bytes**. All payloads and standard reservations fit in sound RAM:
**419,960 bytes mapped/reserved**, **420,000 / 524,288 high-water**, **104,288 bytes**
contiguous tail plus 40 gap bytes. No streaming or sample-quality reduction.

Peak held music notes: 11. The existing conservative 50 ms RR=31 release-window
budget is **22 music slots**. Six fixed SFX ports plus up to four legacy retirement
tails give a conservative combined **32 / 32 slots**, with no spare slot in that
bound. Combat transitions count as one voice per actor because replacement waits
for release; sampled emulator envelopes confirm the tested single-actor handoffs.
Shared legacy SFX use real-VBlank retrigger guards, ignition no longer bypasses
its six-tick guard, and hiss restarts wait three VBlanks after an acknowledged stop
to bound tails. Close ignition requests can coalesce; shared jump/enemy-impact
ports retain rate limiting. This is an audio allocation policy, not gameplay delay.

Music priority31 and SFX8 remain unchanged; music cannot be displaced by lower
priority effects. No musical part is muted. The bound depends on the fast-release
assumption; future envelope/gain/voice changes require rebudgeting. Hardware stress
testing remains necessary. Captured scenarios observed at most **11** active
non-silent SCSP envelopes, not the conservative maximum. Two different players'
whoosh and impact may legitimately overlap; only same-player handoffs suppress it.

All authored art/runtime TGA resources remain unchanged. With every current HQ
feature enabled, VDP1 usage remains **456,224 / 458,488 bytes** (2,264 free).
Historical preservation hash manifests are updated only for authorized audio code,
SFX outputs and nested manifests; `preservation-update.json` records those changes.
Original art and PCM music locks remain. Frozen 8c339ac game sources are retained
in `tests/combat_sfx_baseline/` for a 16,000-tick full-state comparison; only added
audio event bits and the appended sound-attribution field are excluded.

## Validation and delivery limits

Native build, `make check` and `make test` pass. Checks independently verify the
ISO/payloads, full original score, sample bounds/gates, RAM/slot budgets, supplied
WAV derivation, and unchanged original music/unrelated tone payloads. Host tests
cover both actors, misses, rapid/held inputs, actual double-forward/run+A bat
initiation, multi-target hits once, kicks/torch damage, command rejection, pause,
collision precedence, independent interruption and the real-VBlank guard.

Local Yabause core **8926b0c** (HLE BIOS, interpreter/software) exercised actual
controller inputs without game hooks or RAM writes. Six 1,400-frame scenarios
cover missed/rapid jabs, two-player jabs, confirmed jab hits, running bats and kicks.
Single-attacker jab and bat tests have **zero sampled whoosh/CONNECT overlap**;
all custom samples are observed in native slots. Global overlap in two-player
captures is expected and recorded explicitly. Peak captured output is **8,266**
on the PCM16 scale with **zero rail samples**. Native screenshots are from the
emulator, not composites. Detailed results are in `custom-combat-runtime.json`.

Optional reproduction: `tools/test-custom-sfx-runtime.py --help` with the pinned
local core and its headers; use `--single --scenario jab-hit` and `--single
--scenario bat` for overlap assertions. Raw SCSP trace decoding is pinned to
that core's little-endian save-state layout, not a portable hardware interface.

No subjective audio listening, OpenEmu, physical Saturn or SAROO playtest is
claimed. The short release and mix are data/capture-validated; perceived punch,
clicks and final balance still need listening on the user's playback setup.
Extract the downloadable ZIP, keep the matching BIN/CUE together, and open the
CUE. MODE1/2048 disc format and existing gameplay controls are preserved.
