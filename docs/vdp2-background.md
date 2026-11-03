# Phase 1: exact street on tiled VDP2

Branch: `vdp2-background-test`, created directly from preserved gallery commit
`b55ff47752f2708c44587d687a9e95d784708137`. No merge or modification to
`main` or `sprite-upgrade-test`.

## Build and rollback

The default on this experimental branch is `MF_VDP2_STREET=1`. For the test
disc use `MF_VDP2_STREET=1 MF_SPRITE_GALLERY=1 make native`. The existing pinned
Docker build is also supported through `make` with the same environment flags.
No SDK/compiler revision, SDK module configuration, viewport or game timing changed.

`MF_VDP2_STREET=0` restores the original five-texture VDP1 loader and drawing
path. Gallery inclusion remains independently controlled by `MF_SPRITE_GALLERY`.
All four flag combinations are validated. The original assets and monolithic
art generator are unmodified. Returning to `sprite-upgrade-test` restores the
previous implementation; rebuild after switching branches.

The downloadable candidate boots into the unchanged 88px gallery. A mirrors
both figures. Start leaves the gallery for the original title screen; Start
again begins gameplay. The gallery samples the street at camera=280, as before.
Normal gameplay uses the original camera, controls, actors, HUD and text.

## Pixel conversion

`tools/build-street.py` reads only `ST0.TGA` through `ST4.TGA`. It does not
resample or recolor artwork and never writes those source files. It joins the
exact 640x240 source, preserves Jo's +1 indexed-TGA mapping, and deduplicates
identical row-major 8x8 indexed cells. There are 2,400 cell positions and 1,410
unique cells. The palette contains the same original colors converted with the
same RGB555 operation as Jo's old TGA loader.

New root-disc payloads:

| File | Bytes | Meaning |
|---|---:|---|
| STCELLS.BIN | 90,240 | 1,410 8-bit cells, 64 bytes each |
| STMAP.BIN | 16,384 | Two horizontal 512x512 hardware map pages |
| STPAL.BIN | 510 | Original 255 palette entries as big-endian RGB555 words |

The map uses 1-word pattern names, CN_12BIT, 8bpp and 8x8 cells. Each cell
address is expressed in 32-byte units (`tile_id * 2`). Palette bank bits remain
1, matching the street palette's original first-allocation ID. Each page has
64x64 entries; the second page begins at world x=512. The two-page plane is
1024x512, so the existing 640px street does not wrap at x=512. Off-street cells
are initialized but never enter the existing valid camera range 0..320.

## Memory accounting

VDP1 physical memory remains 512 KiB. The project's original command/table
reservation and texture limit remain unchanged: 458,488 texture bytes.

| Configuration | VDP1 bytes, including HUD and 32-byte alignment | Free |
|---|---:|---:|
| Original street, gallery off | 445,152 | 13,336 |
| VDP2 street, gallery off | 291,552 | 166,936 |
| Original street, gallery on | 455,936 | 2,552 |
| VDP2 street, gallery on | **302,336** | **156,152** |

Recovered in either configuration: **153,600 bytes (150 KiB)**. The five source
TGAs remain on disc for preservation and the fallback, but are never uploaded
to VDP1 in the new path. There are no replacement background sprites. The gallery
continues to show the runtime end-of-allocation measurement, now 302336/458488.

VDP2 has a separate 524,288-byte VRAM. Its exact ownership policy is:

| Region | Address interval, end exclusive | Bytes |
|---|---|---:|
| Street cells, A0 | 0x25E00000..0x25E16080 | 90,240 |
| SDK-protected A1 | 0x25E20000..0x25E40000 | 131,072 |
| Street maps, B0 | 0x25E40000..0x25E44000 | 16,384 |
| SDK-protected B1 | 0x25E60000..0x25E80000 | 131,072 |
| **Street allocations** | | **106,624** |
| **Street plus protected bank reservations** | | **368,768** |
| **Unassigned A0/B0 capacity** | | **155,520** |

The protected banks preserve SGL/Jo font/maps, back-color and reserved table
locations. Their full-bank reservations are conservative: 262,144 bytes is
reserved address space, not a claim that the font itself occupies 256 KiB.
No new data is written to those banks. Original Jo's 262,144-byte startup NBG1
bitmap allocation is released before the cell allocation; it is not added again
to the final totals. Both allocations must start at the expected bank addresses
or loading fails before any writes to them.

CRAM allocation is unchanged: one existing 512-byte street bank, seven total
configured banks with gallery off or all eight with gallery on. The palette
payload occupies 510 bytes at the existing bank+1 address; entry zero retains
the SDK's transparency convention. Palette copying uses 16-bit stores rather
than DMA to the halfword-aligned address. Cell/map uploads are DMA-aligned.

## Configuration and isolation

`src/street.c` owns NBG1 and provides load/draw functions for both game and
gallery. It uses Jo's existing VDP2 allocation functions and pinned SGL calls.
The only SDK-storage adapter is the exported `nbg1_bitmap` pointer, released and
cleared before switching from startup bitmap mode. No SDK sources were patched.
Do not mix Jo's NBG1 bitmap helper APIs with this owner.

Display is disabled for setup/uploads and restored on success or failure.
NBG1 is configured for cells, two-page planes, unit zoom, and the existing camera
scroll, corrected by (-1,-1) source pixels to match the original SGL raster
origin. NBG1 alone uses screen window 0 (top=1, right=319, bottom=239; left=1
at camera 0/128/256, otherwise 0), preserving the original strict sprite cull
and backdrop borders without wrapping padded map cells into view. Window 0
is reserved for this module; no sprites or NBG0 text use it. `slScrAutoDisp(NBG0ON|NBG1ON)` recomputes VRAM fetch cycles for cell and
pattern-name access, with its return value checked. Priorities are street=1,
all sprite priority classes=4, text/NBG0=7. Existing VDP1 ground-depth sorting
still determines actor/prop order within the sprite image. NBG0 itself is not
reallocated, moved or reformatted. The 320x240 NTSC viewport is unchanged.

During gameplay only the scroll position is updated. There is no animation
streaming, per-frame background upload, map streaming, parallax or artwork redesign.

## Validation and device checklist

The independent converter validation decodes actual hardware page ordering and
compares every 640x240 source index and its RGB555 palette. It checks every valid
camera offset 0..320 and all visible rows, including original 128px boundaries,
8px cell boundaries, sub-tile scrolling and the x=512 page boundary. The pinned
compiler's object encoding is checked as big-endian before accepting map bytes.

The host C test executes the actual loader/draw source against mocked hardware:
no street VDP1 uploads or draw calls, correct file sizes/addresses, unchanged bank
tails and palette guard, two-page setup, unit scale, priorities, cycle-configuration
call, all camera values, and rejection of a wrong allocation bank or truncated
file. A second compilation tests the original VDP1 fallback path.

All original animation assembly/hash, gameplay, input, music, disc and executable
identity validation remains in place. The separate gallery tests still verify
exact pixels, both facings, grounding and runtime allocation guards. `make check`
now distinguishes original asset payload sizes from actual runtime VDP1 residency.

The loading fix at `8fb07eb` has successful user-confirmed WebRetro Yabause
gallery and gameplay loading. The registration correction was additionally
compared against the original VDP1 path in local libretro Yabause: all 321
full 320x240 background-only captures matched exactly (24,652,800 RGB pixels).
See `vdp2-registration.md` for scope and evidence. These checks do not establish
physical Saturn operation. No hardware is attached.

On-device checks before accepting this migration:

1. Boot matching BIN/CUE and confirm the complete street behind both gallery figures.
2. Verify text, feet, both mirrored figures and the displayed VDP1 total 302336.
3. Enter the original game. Walk right to camera=320 and back left, watching the
   original image seams and new page seam. Confirm no wrapping, blank cells or
   one-pixel jumps, especially around world x=512.
4. Test title/pause panels, HUD, diagnostics, both players, enemies, shadows,
   torch and bat effects. Confirm street behind all sprites and text on top.
5. Repeat on an accurate emulator and real Saturn; record frame timing and the
   included executable source identity. Confirm actual cycle patterns/registers.

The SDK/compiler and framebuffer setup are unchanged. The new candidate still
needs user visual testing in WebRetro and testing on physical Saturn hardware.
No SAROO or hardware frame-rate claim is made.
