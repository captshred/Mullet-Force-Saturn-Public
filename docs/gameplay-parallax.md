# Live city-cleanup skyline parallax

Review branch `art/city-gameplay-parallax`, parent cleanup commit
`c0d42d151a81f1e3072e98e1b4264470eacca3b6`.

Build with `bash tools/build-gameplay-parallax.sh --native`, then `make check`
and `make test`. The wrapper enables MF_LIVE_CITY_PARALLAX and delegates to the
unchanged cleanup/neon/punch-combo profile. Existing wrappers remain controls.

Normal gameplay's existing street draw passes the actual game camera to
mf_parallax_game_draw. NBG1 retains the exact foreground scroll/culling and
shows screen rows 56..239. NBG2 shows rows 1..55, using source skyline rows
0..54 from the cleanup art. The 56-row tile source includes a final clipped row.
The roof/storefront boundary remains on NBG1 as in the proven preview split.
Skyline motion is camera/4 in fixed point, with the same (-1,-1) raster
registration. At camera zero the upper art is identical; later views intentionally
show a slower skyline. The full 640px skyline and two-page map avoid wrap/seams
through all gameplay cameras 0..320. This uses the actual approved skyline,
not the placeholder technical-demo sky. No background art is regenerated.

NBG2 priority is 1; NBG1 is 2; sprites remain 4 and HUD/text 7. Existing windows
0/1 separate the layers. Neon continues from its independent VBlank callback,
and the upper skyline contains only static palette indices. Palette banks,
trash cans, actors, controls, combat, sound and the game camera are unchanged.
The standalone ring/8K-long-map preview is disabled in this live variant; older
cleanup/neon builds retain it. The live layer is always active while playing,
not gated by gallery state or the preview's active flag.

VDP1 stays 453344 bytes / 255 definitions (5144 bytes free). B0 layout:

| Region | Offset from 0x25E40000 | Bytes |
| --- | --- | ---: |
| Original foreground map | 0..0x4000 | 16384 |
| Live skyline cells, padded/aligned | 0x4000..0xC000 | 32768 |
| Live skyline two-page map | 0xC000..0x10000 | 16384 |
| Free B0 | 0x10000..0x20000 | 65536 |

A0 still uses 106496 bytes with 24576 free. A1/B1 remain fully reserved to the
SDK. Total allocations plus reserved banks: 434176 bytes, +32768 versus cleanup;
90112 bytes remain free. Padding preserves a 16KiB-aligned two-page map. Only
21632 of the padded cell bytes contain unique skyline data. NBG2 setup checks
actual allocator addresses, exact input sizes and slScrAutoDisp success; failure
stops asset initialization. No SDK/compiler pins or modules change.

There is no per-frame transfer, allocation, streaming, extra VDP1 command or new
simulation state. Each draw submits layer scroll/window register settings only.
This is a resource/operation budget, not a physical-hardware performance claim.

Targeted tests exercise actual live loader/draw code, all 321 camera offsets,
quarter-speed fixed-point movement, aligned allocations, preserved map/bank tails,
no preview activation and no extra runtime uploads. The independent validator
reconstructs every skyline pixel and verifies the actual ISO payloads. The full
host suite covers existing gameplay, neon callback, props and combat. Source-lock
coverage still protects all gameplay/input/actor/audio sources; street.c is now
a deliberate presentation-only exception to the cleanup lock. Native build and
full checks validate the selected disc. Emulator/hardware scrolling, readability,
cycle scheduling and seam appearance still need controller-driven playtest.

The manual workflow on main adds a pinned gameplay-parallax option while retaining
city-cleanup, neon-stage and bat-fix. Choose main as workflow branch and that
profile; leave commit_sha blank or supply the reported full review SHA. The ZIP
artifact contains matching BIN/CUE, build identity, licenses and SHA256SUMS. No
workflow is dispatched during setup, and no game code is merged into main.
