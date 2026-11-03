# VDP2 street registration milestone

All changes are on `vdp2-background-test`, descended from the preserved runtime
loading fix `8fb07eb20f314d7442f8dab65527a4de2a852f43`. No main or sprite-gallery
branch changes, merges, asset edits, gameplay changes or animation changes.

## Cause and correction

The original `jo_sprite_draw3D2` path goes through SGL's center-based unit-scale
sprite placement (`JO_NO_ZOOM` is 65535, not 65536). Its street raster begins at
requested x+1,y+1. The initial VDP2 conversion correctly preserved every source
pixel, but displayed it at x,y. A data conversion comparison alone could not
catch this difference between source coordinates and actual screen coordinates.

The NBG1 scroll is now `(camera-1)*65536,-65536`. Multiplication is deliberate:
left-shifting a negative signed integer would be undefined in C. No source pixels
are shifted, repainted or resampled. Unit zoom and all priorities remain unchanged.

A scroll offset alone would expose wrapped map cells at screen edges. NBG1 alone
therefore uses SGL screen window 0, inclusive rectangle `(left,1)..(319,239)`.
Left is 1 at camera 0,128,256 and 0 otherwise. This exactly preserves the old
strict `x>-128 && x<320` sprite cull: a texture touching the left edge is excluded
when its requested x is -128. Top row, and those three leftmost columns, show
the original backdrop. This deliberately retains existing rendering behavior.
No other layer, HUD, text, actor, gallery piece or world/camera coordinate moves.
SGL converts the horizontal window coordinates to VDP2 register units. Window 0
is now reserved for the street owner; future layers must account for that.

The `slScrAutoDisp` success check remains `result<0` for failure. All loading
error diagnostics, paths and allocation guards from 8fb07eb are retained.

## Validation

* Independent asset validation still decodes the exact 640x240 source pixels,
  RGB555 palette and two-page map, including x=512. It additionally constructs
  the original five-sprite viewport using its strict culling and raster origin,
  and compares all 321 registered screen positions including backdrop borders.
* Host tests execute actual `street.c`, checking every scroll/window coordinate,
  NBG1-only window selection, allocation guards and the preserved SGL zero-success
  and legacy expected-failure regression cases. Original gameplay, combat, co-op,
  animation, input and music tests are retained.
* Local runtime comparison uses libretro Yabause v0.9.15, commit
  `8926b0c6c347f8c5c755911ddb0ac695420ffbf8`, software renderer, HLE BIOS,
  one thread, interpreter, no expansion cartridge. Two separate background-only
  test ROMs use the actual current `street.c` and pinned Jo/SGL: VDP1 fallback
  versus corrected VDP2. The frontend writes a volatile camera variable in
  emulated high RAM, waits six frames per position, and captures full RGB output.
  **All 321 complete 320x240 frames match exactly: 24,652,800 pixels, zero
  mismatches**, including camera 0,127,128,255,256,280,320. The supplied JSON
  report contains a matching RGB hash for each camera; sample A/B PNGs accompany
  the test artifact. The harness is separate from the delivered game.
* The delivered gallery/gameplay build is separately booted in the same local
  core, entering gameplay and moving right and left. It retains all original
  actors, animations, controls, title, HUD, music and effects. This is a smoke
  test, not exhaustive combat playtesting or audio listening.

The user already confirmed loading of the prior 8fb07eb disc in WebRetro Yabause.
The new aligned candidate still needs user visual acceptance in that browser.
No physical Saturn was tested, and HLE BIOS testing does not establish real-BIOS,
CD-drive timing or hardware performance compatibility.

## Exact memory, unchanged by registration

The correction adds register configuration only: **zero extra VRAM or CRAM bytes**.
Original and generated asset hashes are unchanged.

| VDP1 texture configuration | Allocated bytes (32-byte alignment + HUD) | Free of 458,488 |
|---|---:|---:|
| VDP1 street, gallery off | 445,152 | 13,336 |
| VDP1 street, gallery on | 455,936 | 2,552 |
| VDP2 street, gallery off | 291,552 | 166,936 |
| VDP2 street, gallery on | **302,336** | **156,152** |

Recovered: **153,600 bytes (150 KiB)**. The successful gallery's onscreen total
is the actual runtime end-of-texture-allocation measurement.

| VDP2 region | Start | End exclusive | Bytes |
|---|---|---|---:|
| Street cells, A0 | 0x25E00000 | 0x25E16080 | 90,240 |
| Street maps, B0 | 0x25E40000 | 0x25E44000 | 16,384 |
| SDK-protected A1 | 0x25E20000 | 0x25E40000 | 131,072 |
| SDK-protected B1 | 0x25E60000 | 0x25E80000 | 131,072 |

Actual street allocations: **106,624 bytes**. Including both whole protected
banks, **368,768 / 524,288 bytes reserved**, leaving **155,520** unassigned in
A0/B0. The protected-bank total is ownership reservation, not actual font payload.
The SDK's initial bitmap allocation is freed before street setup.
CRAM remains seven 512-byte banks without gallery, eight (4096 bytes) with it;
the existing street bank is ID 1, with 510 payload bytes at bank+1. No new palette.

## Foundation assessment

This is a suitable isolated foundation for future tiled environments: source
fidelity, screen registration, scrolling, loading and recovered texture space
are validated in local Yabause. It is not yet a completed streaming engine.
Before large-scale animation/background production, validate on real Saturn,
profile frame time and VDP2 cycle access, and design explicit bank/palette
ownership and bounded animation/level streaming. Current memory savings alone
do not establish how many detailed animated actors will fit or draw smoothly.

Disable using `MF_VDP2_STREET=0`; restore the exact prior loading-fixed version
by checking out preserved commit 8fb07eb and rebuilding. Never mix BIN/CUE files
or load old emulator save states when comparing candidates.
