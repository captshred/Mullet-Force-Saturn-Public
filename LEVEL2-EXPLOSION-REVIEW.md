# Level 2 explosion review

Source branch: feature/level2-explosion-refinement
Source commit: ceec2d5c8ad3988b46e90da94a8f51c18de09e0f
Approved baseline: the-one-v2 (952bccd917dae73f40d0519c80d2d5ee280efb68).

Level 2 explosion controls alone change from volume 112 to 100. Real 68000 driver execution measures -4.5 dB, or 59.566% linear amplitude. Samples, pitch, timing and four-slot playback behavior are unchanged. Other SFX and music volumes are unchanged.

Level 2 reuses the approved Level 1 explosion pixels, converted to the existing RGB555 texture and rendered at 24x24. Level 1 art/audio are unchanged. The existing 12-tick lifetime and gameplay behavior remain unchanged.

Resource changes: zero additional VDP1 definitions, texture bytes, CRAM bytes or audio memory. Existing explosion texture: 2048 bytes. Level 2 VDP1 budget: 28 definitions, 33792 texture bytes, 81 maximum commands, 32 CRAM bytes. Sound RAM high-water: 447588 bytes, 76700 free; conservative voice budget: 28/32.

Private native compilation, make check and make test passed, including Level 1 preservation, repeated mixed SFX, ten simultaneous visual bursts, all animation lifetimes, scale restoration and the native-driver gain probe. Four coherent explosion voices have a conservative explosion-only peak bound of 0.3531 full scale (9.04 dB headroom). This is not a full-game mixed audio measurement.

This candidate has not been verified audibly or on hardware/emulator. Visual and audible user approval is pending; nothing is merged into the approved baseline.

Authoring files and private source history are excluded. GitHub Actions verifies and packages this privately compiled image; it does not compile the private source. The artifact contains the matching BIN/CUE, build information, licenses and focused results.

Load mullet-force.cue in your Saturn emulator or use your usual hardware workflow.
