# Level1 UGH protection and SFX velocity refinement

Starting executable: `744053ba851c9da6b8953708f125313f177b7dcb`.
Starting delivery: `4f37a19dcea7767daa6177706b0aab4c6d1909ad`, whose playable
BIN SHA256 is `5a1f3b6f60a28a23830aabd54e12696f00cd6ee37924251ec5c408848aee81a5`.
The prior combat changes and all approved slide/pause improvements are retained.
New experimental branch: `audio/level1-ugh-protected-sfx`. No definitive tag changes.

## Cause and protection

The old death used the same combat control as subsequent player effects. A
later hit called the existing scoped SND_StopSeq on that control. A native
baseline capture reproduces ARGH stopping one frontend frame after note-on,
at PCM phase183.75 of12274, at driver PC0x554a (scoped sequence stop). This is
sequence replacement, not evidence of SCSP voice stealing or a music cleanup.

UGH uses FX song/program8 on otherwise unused Level1 logical control7.
This does not reserve a physical SCSP slot: each accepted play allocates one
normal voice at the existing SFX priority31 and volume112. No sound-driver
code, SCSP reset, global All Notes Off or instrument gain is changed.

From the first human-death request through confirmed completion and retirement,
new Level1 SFX requests are discarded. Already pending unstarted combat effects
are cleared. Simultaneous and overlapping deaths coalesce into the current
play; they do not restart it or build a backlog. A fresh death after protection
ends may start a new play. Already sounding effects are not forcibly stopped
by protection. Their normal pause/release/stop rules remain intact; an already
running hiss may continue its own sequence loop. Commands accepted before the
death request can reach the native driver in the same capture frame as UGH.
No new competing request is accepted while protection is active.

Protection waits for the real SDK sequence status to show PLAY and later STOP,
with a sample-derived59-VBlank minimum from observed PLAY. An initial stale
STOP cannot unlock it. The score's gate covers the recording plus50ms.
Only after full completion does a scoped StopSeq(7) retire the cached control;
one real VBlank is allowed before reuse/teardown. There is no short timeout
that can unlock and truncate an active recording. Normal fresh effects resume
on the next eligible update; no stale burst is replayed.

Control7 is not part of the ordinary Level1 SFX pause group, so UGH finishes
while paused; music continues normally. Gameplay processing and all collision,
AI, damage, hit-stop and animation code are unchanged. The only main-loop
change waits for this audio lifecycle before Level2 takes ownership of sound
RAM. It does not gate active Level1 gameplay or freeze the world for a sound.

## Samples, routing and velocities

UGH source is stereo44100Hz PCM16,42899 frames/0.97276644s. User-approved
conversion averages channels, bandlimited resamples to11025Hz and encodes
signed PCM8. No normalization, gain, fades, trimming, compression or time
stretch is applied. The original WAV remains private.

The runtime sample is10725 bytes, nominal0.97278912s. Its root compensation,
attack/decay/sustain/release, pan, TL and velocity110 match the previous death
instrument. Only waveform/length changes. ARGH's12274 PCM bytes are removed
from the active bank. The pre-ARGH original death remains byte-exact, once,
41824 bytes/20912 frames at44100Hz; jump kick and cross punch share program6.

| FX song | Use | Before velocity | After |
|---|---|---:|---:|
|0|Ordinary nonlethal impact/hurt|110|127|
|1|General jump|110|127|
|2|Inorganic destruction/explosion|110|127|
|3|Torch ignition|110|127|
|4|Torch hiss|110|127|
|5|Jab initiation|110|127|
|6|Cross/jump-kick impact and existing player-death mapping|110|127|
|7|Bat effect|110|127|
|8|Human enemy death, UGH|110|110|

The importer always derives velocities from the verified prior executable,
using integer nearest rounding with halves upward: min(127,(115*v+50)//100).
Thus110*1.15=126.5 becomes127. Re-running cannot double-boost. All existing
note timing/gates and channel/program events in songs0..7 are exact. No music
or Level2 velocity is changed. PCM and instrument TL in programs0..7 are exact.
Native per-voice gain multipliers increase378->412 for all eight affected
songs (about9% amplitude/~0.75dB from this driver's curve), while UGH remains378.
There are no unresponsive-velocity exceptions and no compensating PCM gain.

## RAM and voices

Level1:515192/524288 sound-RAM bytes used;9096 free. This saves1552 bytes over
the ARGH build, including alignment/sequence changes. Level2's separate map is
unchanged:506660 used,17628 free. No unrelated PCM is removed or degraded.
Old shared impact PCM SHA256:
`47f5e17f0f874572e4390a87b6414ddfa6b05c34dddce54093081fe5c1d0ecdd`.
UGH PCM SHA256:
`bbc3b1f306740c307a321e287020dcf31ff3da212d97fc1306925e550d3bda2f`.

Peak observed active native slots at VBlank sampling:19 in full-loop mixed SFX
stress,17 in gameplay combat,23 in the transition captures. These counts use
native SCSP ECNT<2097151, including release phases, not cached driver EG flags
or stale envelope-output values. They are sampled peaks, not audio-cycle peak
claims. One dynamically allocated voice is needed for UGH; no physical slot is
permanently reserved. No UGH slot is reused or keyed off before natural LEA.

## Verification

- Actual production transport tests cover SDK rejection retries, initial stale
  STOP, full duration floor, PLAY that remains active beyond the minimum,
  overlapping deaths, punch/kick/bat/world/jump/ignition requests, pause,
  acknowledged post-completion retirement and fresh effects without backlog.
- Existing collision tests, paused gameplay and the protected prior regression
  suites run through make test. Current game.c/game.h are byte-identical to the
  prior working executable; only the audio handoff guard changes main.c.
-16000-frame real-driver capture:16/16 UGH plays reach natural PCM end, including
  repeated competing requests and pause; complete4907-note Drop Zone loop plus
  prefix; no missing/reordered music note-ons, forced music offs or clipping.
-14000-frame full-loop mixed-request stress:140 completed UGH plays; one final
  play is still active when capture ends. No premature UGH off, music cut,
  reordered/missing music note-on or clipped output. Mixed peak23198/32768.
-8000-frame gameplay combat:20/20 UGH plays complete; no clipping/music cut.
-8000-frame normal and early-handoff captures complete; three UGH plays each
  reach LEA, with2847 and2887 ordered Wristbreaker music note-ons respectively.
  Early skip request2930 occurs before the last UGH's observed natural end2934.
  Final executable source and artifact identity are recorded in the delivery JSON.

One earlier prototype's longer emulator capture stalled near frame7845 after
entering Level2; the starting executable completed the same capture. The
prototype had not explicitly retired its dedicated completed control. Scoped
post-completion retirement was added, and both normal and early-handoff runs
then completed. The exact cause of the single earlier stall was not proven;
this is not a claim to have fixed E108 or all cold starts. The known pre-existing
intermittent Level2 startup E108 remains unresolved and was not investigated.

All results above are emulator/host verification, not hardware approval.

## Rebuild

Use the existing pinned SDK556d081146211b6a1cfa6591d70f9487d406758b.
Run `bash tools/build-source-complete.sh`, `make check`, `make test`.
GitHub Actions: **Manual Saturn playtest build**, workflow ref
`audio/level1-ugh-protected-sfx`, profile `level1-ugh-protected-sfx`, source_ref
set to the exact executable SHA in `ugh-delivery.json`. Retention remains1 day.
Local native builds are reported separately from Actions runs.
Diagnostic captures can be reproduced with `bash tools/run-ugh-playback.sh`.
