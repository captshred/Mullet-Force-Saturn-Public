# Mullet Force starter

- Read README.md for fresh-environment setup. Do not assume another project or
  environment has installed dependencies; run tools/setup.sh for this checkout.
- Keep the Jo Engine/compiler pin and Docker base unchanged unless explicitly
  asked to change them. Inspect .deps/joengine headers/examples before using APIs.
- make uses Docker; make native uses the same pinned compiler with host packages.
  make clean is required after engine module changes. Run make check after builds.
- Keep .deps/ and build/ out of commits. Supply complete matching BIN/CUE files.
- This is a boot/input starter, with no game assets or gameplay specification yet.
  Do not copy Battle Beetle character, scenery or music into this repository.
- Distinguish structural validation from emulator/hardware testing in reports.

## Public development snapshot

- Start from jab-jab-cross run 41215154675 / d3e4b0d, not the later cross refinement.
- Keep authoring masters, source MIDI/WAVs and full art archives private.
- Public builds use committed runtime assets with MF_PRESERVE_AUDIO=1.
- Use tools/build-punch-combo.sh for the complete selected profile.
- Keep one default CI build and one playable artifact, retention-days: 1.
- Do not restore the historical variant matrix or upload asset archives.
- make check validates exported runtime assets; make test retains C regressions.
- The expanded Animation Test Lab has not yet been implemented.
