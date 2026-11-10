# Level 2 E008 diagnostic candidate — approval required

Based on bb7b6b61af79ccddd9994a9623456d3f10ad6613. Branch:
`diagnostics/level2-e008-startup`. No production repair. Do not push or dispatch
Actions until the user approves this candidate. No workflow YAML changes.

## Independent archive comparison

Both supplied ZIPs were read independently with pycdlib. Each contains 384
regular ISO files. Every path, length and SHA256 matches, including 0.BIN and
all sound banks. Both discs are 3,043,328 bytes. All differing raw bytes lie in
ISO directory-record or volume-descriptor timestamp fields; no other differing
bytes remain after masking those defined fields. G22 BIN SHA256:
`0fb07066225da1f58b1a4a3d2e0ba504edeac667efdab8193e9c9028f2a802ea`.
Rebuild BIN SHA256:
`df5056a7294584bb974c224e3a3913b12e5c8613447a5f0ed85c1bef026c6896`.
G22 is a personal filename, never a Git ref.

## Changes and overhead

- main.c binds the existing volatile VBlank counter once; no new interrupt hook.
- wingsuit_audio.h defines a 128-record SH-2 trace and debugger API.
- wingsuit_audio.c records stage entry/completion, wait labels, boot changes,
  readiness and timeout. Each 36-byte record stores VBlank, stage, boot, event,
  cursor041a, flags04e0/1, volume07f6, timer8838, history883a, gate10da and eight
  queue command IDs. Timeout additionally saves all 128 queue bytes and freezes
  the capture. Success freezes it too. The next audio load resets it.
- wingsuit_runtime.c adds failure-only text and A-button trace pagination.
- Makefile selects a diagnostic scope validator. Original preservation locks
  are unchanged. The validator checks every baseline file outside the five
  reviewed integrations, runs original checks/tests in a temporary baseline
  tree, then tests the actual diagnostic audio/runtime.
- tests/e008_startup_test.c tests production C with mocked SDK/68000/SCSP.

Capture storage is 4,744 bytes; total BSS growth is 4,752 bytes, including clock
pointer and screen page. Matched local builds: executable 242,368 -> 243,008
bytes (+640). No new VRAM allocations or sound-RAM allocations/writes. Existing
font rendering is used only after failure. Sampling performs bounded volatile
reads; each record reads 20 sound-RAM bytes. No startup printing, file writes,
extra driver commands, timeout changes, audio assets or gameplay changes.
A failure adds a 128-byte read after the watchdog has expired.

Snapshots are sequential, not atomic relative to the running 68000. Timestamps
have VBlank resolution; stage durations are entry-to-completion tick differences.
Multiple events can share a tick. The finite ring retains the latest 128 events.
Detailed per-command latency is not measured. Instrumentation inevitably changes
bus traffic and SH-2 instruction timing; hardware noninterference is unproven.
The 68000 PC cannot be captured through these shared-RAM reads. Use the emulator
CPU debugger; do not halt/reset the 68000 from game code.

## Validation and reproduction

Use the pinned SDK via `bash tools/setup.sh`, then
`bash tools/build-stage.sh --native`, `make check`, `make test`.
Profile is stage-default, with preserved audio and developer stage skip enabled.
The local baseline and instrumented startup suites have identical outcomes over
17,141 trials. Tests cover synchronous consumption, cold/reload models, delayed
and missing acknowledgments, full queues after load, request gating, missing map
acknowledgments, sparse polling and clock/ring retention. Mocked warm reload is
not an actual Level 1 playthrough. Existing recovered-audio UBSan regressions pass.
No Saturn emulator executable or BIOS is available in this workspace; no actual
emulator boots or physical Saturn tests were performed. No root cause confirmed.

After approval: push only this diagnostic branch; dispatch the existing
"Manual Saturn playtest build" with profile `stage-default` and source_ref set
to the full diagnostic commit SHA (`git rev-parse HEAD`). Download the matching
BIN/CUE from that run. Do not use the definitive tag for source_ref.

## Capture when failure appears

1. Photograph the complete original error plus diagnostic rows. Do not reset.
2. Record BIN SHA256, emulator/version or Saturn model, BIOS/region, cold versus
   reset boot, stage-skip versus natural transition, and trial number.
3. Press A for older trace pages; photograph until events repeat. Lines read
   sequence index, VBlank T, stage S, boot state B, event E.
4. C=041a; F=04e0/1; V=07f6; T=8838; H=883a; G=10da opcode word. Queue bytes
   are hexadecimal; D12 is decimal-command-12 presence in the frozen snapshot.
   Events: 1 entry, 2 completion, 3 wait, 4 boot change, 5 timeout, 6 ready.
5. With a debugger, dump `mf_ws_startup_capture` (4,744 bytes; use game.map for
   this exact build), and sound RAM 0..0x10000. Also record 68000 PC/registers,
   exception state and SCSP state. Capture successful runs for comparison.
   The ring remains in SH-2 RAM, not persistent storage; power loss destroys it.

At initial asynchronous failure the original source assigns error=108 and prints
`E%d`. The diagnostic adds a separate literal `DIAG E108` for comparison; it does
not change the original error. Identical supplied executables do not explain the
reported E008. A complete display capture is still needed to distinguish a
rendering/transcription issue from other execution state. No claim of resolution.
