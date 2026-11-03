# Neon District validation

Performed in this task on x86-64 Debian 13:

- Fetched the new starter from main and used its exact SDK pin and GCC 8.2.0.
- Ran SDK setup. The privileged bootstrap could not run without sudo; installed
  the missing genisoimage package under `/workspace/mf-host-tools` using apt's
  signed Debian 13 index and package-hash verification. Runtime MPFR/MPC and
  other compiler dependencies were already present.
- Clean-built after enabling FS/TGA/audio; built again incrementally after fixes.
- `make check`: Saturn boot header, ISO9660 data track, real `0.BIN`, CUE and
  package hashes passed. All 25 TGA and 3 PCM files match the ISO byte for byte.
  Texture dimensions/formats, source fingerprint, and memory budget passed.
- `make test`: nine test groups passed. Also ran the same tests with host
  AddressSanitizer and UndefinedBehaviorSanitizer successfully.
- Inspected the authored Buck sheet and street art composite. These are art
  reviews, not screenshots captured from the Saturn executable.
- Regenerated assets and verified their deterministic payloads against the
  previously built disc. No placeholder rectangles substitute for Buck or drums.
- Compiler reports one pinned-SDK warning in `jo_audio_is_channel_playing`
  (integer argument to slPCMStat); the game does not call that API. No game
  source compiler warnings or link errors were observed.

Not performed: emulator execution, audio playback, Saturn/SAROO boot, controller
playtest or real hardware performance measurement. The user's successful
OpenEmu starter boot applies to the starter, not this changed executable.

## OpenEmu / Saturn / SAROO playtest checklist

1. Cold boot the matching BIN/CUE with no starter/Beetle save state. Confirm a
   neon city, Buck in his silver jacket, HUD and PRESS START prompt appear.
2. Start the stage. Walk both directions and up/down; verify street boundaries,
   frame animation and horizontal flip. Walk right to reveal the whole venue,
   arcade and vinyl shop; walk back to verify camera limits.
3. Press B without directions. Confirm the shadow stays still while Buck rises
   and lands at the same street depth. Repeat with D-pad steering.
4. Stand beside a drum at its depth. Tap A: wind-up, contact spark, recoil and
   recovery should be distinct. Hold A: only one swing should occur. Release
   and press twice more to break it. Verify score and four-second respawn.
5. Punch while above/below a drum or facing away: no hit. Repeat facing left.
6. B then A beside a drum: the kick should hit during the lower portion of the
   jump if the drum is in the same lane and in reach. Landing recovers normally.
7. Move Buck behind and in front of a drum, then jump at both depths; confirm
   sorting follows feet on the ground, not the airborne sprite's vertical edge.
8. Pause during a jump and resume: simulation must freeze and resume. C toggles
   diagnostics. Record the source-hash prefix and image SHA-256 when reporting.
9. Listen for short punch/jump/impact effects. Check for clipping, repeated
   triggers, missing sounds, corruption and slow frames while scrolling.
10. Test BIN/CUE loading on actual SAROO before claiming SAROO compatibility.

## Buck redraw validation

- Replaced every Buck animation with 15 newly authored native-resolution frames.
  Verified the 88px idle silhouette, breathing height, centered anchors, common
  y=92 sole baseline, wide attack padding, and identical shared palettes.
- Inspected a contact sheet decoded from exported TGA files; provided 1:1 and
  2x versions in the Actions artifact. These remain art sheets, not emulator
  captures. Street, drums and PCM payloads are unchanged from adcae37.
- Switched Buck alone to the pinned SDK's 8-bit TGA/palette API, using its
  documented +1 raw pixel-index mapping and final padded palette-entry skip.
- Added animation tests for all six walk positions, takeoff/air/landing/kick,
  punch phases and the updated reach boundary. Landing adds visual recovery
  without delaying movement or input. Existing gameplay tests still pass.
- VDP1 texture allocation including HUD: 452,096 / 458,488 bytes.
- No emulator, sound or hardware execution was performed during this art pass.

## Native Drop Zone SEQ/TON music pass

- Analyzed the uploaded format-1 MIDI with the repository's strict SMF parser;
  cross-checked tracks, timing, polyphony and controllers using mido 1.3.3 in
  a temporary inspection directory. mido is not a runtime/build dependency.
- Evaluated pinned mid2seq sources against SGL/Sega driver headers, the SRL
  native SEQ sample and seq2mid format documentation. Reused the existing
  68000 driver and vendored converter/TON builder; no new driver was written.
- Built the Saturn executable with the exact existing SH-2 compiler, linking
  the existing SDK LIBSND control initializer. Added host gcc/Python to the
  unchanged pinned Docker base for converter generation.
- Independently decoded all 5,120 emitted notes and 1,206 pitch bends and
  compared times/gates/velocities/rounded bends against the source. Tempo,
  exact duration, paired native loop markers and per-loop cleanup passed.
- Validated tone layer pointers, dry outputs, non-looping percussion/SFX,
  finite releases, mapped addresses and sound RAM/voice budgets. All native
  payloads are checked byte-for-byte inside the ISO.
- Seven conversion tests cover tempo changes, large gates/deltas and initial
  silence, bend rounding, source inspection, drum routing, rejected malformed
  gates/sustain, truncated converter input and deterministic generation. Native transport tests mock SDK
  calls and verify start/pause/resume, partial-command retries and three simultaneous fixed SFX ports.
- The nine existing gameplay test groups still pass. Gameplay/graphics source
  and texture payloads were preserved; only audio setup, event dispatch and
  an off-by-default audio initialization diagnostic were added.
- No actual emulator or hardware audio playback was tested. Data validation
  and SDK command mocks do not establish the listening result. Follow the
  detailed listening checklist in `docs/native-music.md`.
