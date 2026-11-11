# Level 2 E108 — request notification repair and startup evidence

## Source and confidence

Branch: `fix/level2-e108-cold-start`, based exactly on the delivered AI 3.0
`0827a42ac863102102ea9dd693109f1483384bdb` (`feature/level1-punk-ai-v3`).
That AI 3.0 build's Level 2 audio/runtime sources and stage-default build script
are byte-identical to approved startup baseline
`a97aedf614ad9077eb2349f435aaea70ca394811`. AI 3.0 added 72 bytes of AI state,
80 linked BSS bytes and 2,608 executable bytes relative to AI 2.0. Those change
layout/execution timing, but no evidence establishes that they caused E108.
No AI/gameplay change is part of this repair.

The source of the most recently delivered build is established. The user's
actual failing BIN/BUILD-INFO and complete screenshot were not attached, so its
source SHA and exact on-device register values cannot independently be verified.
The error text is available; a request for the remaining rows/build identity is
pending. No emulator executable or Saturn BIOS was found in the available
workspace/tools. No actual hardware/emulator reproduction is claimed.

**Verified software defect:** the SGL/SND combination can leave queued requests
without the notification required by the running 68000. The targeted production
C reproducer yields the exact reported DRIVER READY / EXPECT 0 GOT 12 before
the repair, then succeeds with it. This is a concrete transport bug, not a
hypothetical timeout increase. **Confirming that the user's particular failure
used this path still requires its gate/flag trace and repeated device testing.**

## What E108 / EXPECT 0 GOT 12 means

`mf_ws_runtime_frame()` converts a negative `mf_ws_audio_ready()` into error 108.
`load()` also returns 108 for a synchronous audio-loader error. The runtime uses
`WDEATH BANK` as an umbrella audio-loader label, including music and staged Fire.
It does not, by itself, identify a broken WDEATH.TON file.

For the reported `CAUSE DRIVER READY`, the asynchronous bootstrap has not passed
BOOT_CPU. It requires BOTH a changed consumed-command cursor at sound RAM
0x041a and eight empty request ID bytes at 0x0700 + 16*i. After the unchanged
120-VBlank watchdog, `startup_timeout()` reports the first nonzero queue ID as
`expected=0, actual=ID`. Decimal **12 (hex 0C) is SND_StopDsp**. It is neither a
file length, a damage value, a bank number, nor an SDK return code.

The assets were uploaded before this asynchronous boundary. The text alone
cannot establish whether the CPU never started, the dispatcher is waiting for
a host notification, or command processing is stuck. The later Fire bank has
not been introduced at BOOT_CPU. Pressing A only paginates the frozen trace;
the failure path deliberately does not retry startup.

Historical E008 diagnostics only sampled startup state and added a failure
screen. They did not repair initialization or provide a retry. Current source
explicitly prints E108; the older E008 report is not assumed to have this cause.

## Pinned binary evidence and lost-notification mechanism

All evidence uses unchanged SDK revision
`556d081146211b6a1cfa6591d70f9487d406758b`, driver 2.10, 26,610 bytes,
SHA256 `68890ee4a49fd0c341bc3f0a48643e4db4b175df0b0d7dacfeb88306340052b6`.

- Driver 0x1848 samples configuration byte 0x04e1. If bit7 is set, it retains
  the command gate. Otherwise its own initialization replaces the gate with
  NOPs. This choice changes executable code once; clearing 0x04e1 later does
  not redo it.
- Retained gate 0x10da: `MOVE.B $04e0,D0; BPL $111e`. Without host request bit7,
  it skips the eight request blocks. At 0x1118 it clears that bit after a scan.
- SGL initializer `sglG00.o` starts the CPU internally, then sets configuration
  byte 0x04e1 to 0x80, publishes its DSP/map bootstrap requests and signals
  request byte 0x04e0 with 0x80. It waits for its map request before returning.
  The bootstrap can therefore leave the retained, notification-dependent mode.
- Our loader clears CONFIG 0x04e1 later and calls slSoundOnWait/slSndFlush,
  then submits SND_StopDsp/CDDA/volume. Pinned `LIBSND.A` StopDsp only writes its
  0C00 queue word; it does not set request byte 0x04e0. SND's queue allocator
  and the later direct SND publishers similarly rely on their configured mode.
- The earlier flush is not a persistent notification for future submissions.
  If the 68000 scans/clears its flag before these later requests are published,
  queued command 12 can remain forever, independent of a longer timeout. If an
  earlier wake overlaps publication, consumption can succeed. A warm restart
  changes that interleaving; it does not prove a different root cause.

The request-mode choice, missing publication notification, and scan/clear race
are verified in the pinned bytes and modeled by the new regression. The user's
reported cold/warm difference is consistent with them, not a measured failure
rate or proof of the exact failing interleaving.

## Small repair

`notify_commands()` signals only an existing nonempty queue by setting bit7 of
the public host request byte 0x04e0, preserving its other bits. It runs after the
initial bootstrap submissions and before/after each existing audio service.
Repeated notification is necessary because the driver can clear the flag after
passing a newly published earlier slot. No request is duplicated, cleared,
reordered or synthesized; no driver code is patched by the SH-2.

The original audio scheduler body, MIDI formatting, pool allocation/retirement,
Fire/Flame handoff, music start, event spacing, gains and rejection retries stay
exact. The wrapper provides notification only. There is no arbitrary delay,
longer timeout, extra SGL flush, fake cursor increment, queue clearing, relaxed
map check or suppressed E108. The same strict cursor/queue/map acknowledgements
still gate play. An absent/frozen driver or missing map acknowledgement fails.

The fix also services notification after startup, since the same gated consumer
processes music, Flame and SFX requests. Fixing only BOOT_CPU would merely move
the stall to the next map/DSP/SFX boundary.

## Additional diagnostics

Existing trace fields and A pagination remain. Added:

- Eight-VBlank wait observations (event7) while startup remains unfrozen.
- Notification observations (event8), sampled BEFORE setting the request bit,
  and startup notification count `W` in the DIAG header.
- Last sampled driver error word 0x0416, raw status word 0x0420, and driver end
  signature at 0x67ee (`53454741`, ASCII SEGA), shown on row27.
- An evidence label on row11. `REQUEST FLAG CLEAR` means a queued command,
  retained gate 1038, and clear request bit in that snapshot. `COMMANDS
  PROGRESSED` means cursor/history changed after DRIVER READY entry. `TIMER
  ALIVE NO ACK` means timer progress without observed command progress.
  `NO PROGRESS EVIDENCE` cannot distinguish halted CPU, unstarted driver,
  disabled interrupt, or unobserved progress. `CHECK DRIVER IMAGE` identifies
  a missing/mismatched SEGA signature, not a complete image hash validation.

`F` is a big-endian word: request byte 04e0 is its HIGH byte, configuration byte
04e1 its LOW byte. Thus host request bit7 is word mask 8000. `G1038` is the
retained MOVE.B gate; `G4E71` is its NOP mode. Current CONFIG alone does not
reveal the mode already selected. C=041a consumed cursor, T=8838 interval timer,
H=883a working history cursor, V=07f6 volume; Q IDs are hexadecimal, while
EXPECT/GOT are decimal. Timer8838 resets on commands; it is not monotonic ready.

Snapshots are sequential shared-RAM reads, not an atomic CPU snapshot. The
ring freezes on success/failure. Diagnostics never send a command or authorize
play. New sampling adds read traffic, so device timing still needs testing.

## Validation

Passed native pinned source build and disc/preservation checks. Full tests:

- Byte audit of real SGL initialization, SND_StopDsp publisher, 68000 gate,
  startup configuration patch and post-scan notification clear.
- Same production-C driver-gate model against original AI 3.0 and the repair:
  512 modeled cold loads and 512 warm audio reloads for each. The deliberately
  lost-wake baseline cases reproduce DRIVER READY / 0 / 12; repaired cases all
  become ready. Delayed/sparse consumption and request-clear races are varied.
  This tests a failure condition, not actual cold-start incidence.
- Driver-never-consumes and missing-map-ack still fail; synchronous consumption
  still succeeds. The original 17,141 startup trials and clock/ring cases run
  against the repaired transport as well.
- Current recovered audio UBSan stress: music, simultaneous persistent Flames,
  Shot/Explosion/Hit leases, spacing, queue rejection and release. All three
  existing readiness mutations remain rejected (early Fire map, timer alias,
  late consumption snapshot).
- Sixteen isolated executions of the current runtime loader suite, including
  its existing warm restart/load cases, plus every diagnostic evidence label.
  These use SDK/RAM mocks. They are not sixteen emulator cold boots or real
  Level 1 playthroughs.
- Exact AI 3.0 preservation and its original focused gameplay/50,000-tick
  movement tests, FF+A, stage-clear quota and Level 2 entry tests through the
  archived preservation chain. Current Level 2 loader and transport are tested
  separately, rather than claiming archived tests validate this repair.

The scope gate freezes every AI 3.0 file except Makefile and the three explicit
transport/diagnostic integrations. It also compares the entire approved audio
scheduler and command/event formatting verbatim. Music/SFX/graphics payloads,
Level 1 music and gameplay, AI 3.0, FF+A, stage progression, wingsuit simulation,
startup sequencing and build/workflow configuration are unchanged. Disc checks
validate the actual rebuilt executable and preserved Level 2 resources.

Inherited optional historical driver/allocator and dual-boot comparisons remain
skipped where their archived fixtures are unavailable. No unresolved regression
failure is accepted. Hardware/emulator verification remains outstanding.

## Cost, files, follow-up and build

Changed `src/wingsuit_audio.c`, `src/wingsuit_audio.h`,
`src/wingsuit_runtime.c`, `Makefile`. Added `tools/test-e108-request.py`,
`tools/validate-e108-request.py`, and this report. All AI 3.0 implementation
files are unchanged.

Matched native build: executable 245,904 -> 246,880 bytes (+976); linked BSS
0x663f4 -> 0x66404 (+16). Trace grows 12 bytes; polling clock adds four. No new
VDP1/VDP2/CRAM/SCSP allocation, sample, texture, disc access or heap allocation.
The intended sound-RAM change is the required host request bit, not bank data.
At most two bounded eight-ID scans are added per audio service call.

For device confirmation, record the full commit/BIN identity, platform/core and
BIOS, then compare fresh emulator processes/power-on cold starts with warm
resets, using both stage skip and natural Level 1 completion. Keep success and
failure counts separately. If E108 recurs, capture the complete error and
DIAG/C/F/V/T/H/G/Q/W/ERR/ST/SIG rows, then all A pages; preserve the failed state.
G1038/F with no 8000 and Q0C confirms a retained-gate/missing-notification
observation. With request bit set and no progress, dump the saved trace, sound
RAM 0..0x10000 and 68000 PC/registers to locate where initialization/dispatch
stopped. No further reset/delay/error suppression should be guessed from it.

Build after validation: **Actions → Manual Saturn playtest build → Run workflow**.
Workflow branch `fix/level2-e108-cold-start`; profile **stage-default**;
`source_ref` is the full repair commit SHA delivered with this report. Download
`mullet-force-stage-default-<SHA>` within one day and keep matching BIN/CUE and
checksums together. Open the CUE. No baseline merge or Actions dispatch is made.
