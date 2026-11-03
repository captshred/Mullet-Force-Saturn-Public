# Optional 88px sprite gallery

This experiment belongs to `sprite-upgrade-test`. Baseline preserved at
`178335ce694bf49c68c62d95b40dc7d02a8335ba`. No changes to main or original art.

Build with `MF_SPRITE_GALLERY=1 make native` (or `make` for the pinned Docker
build). The default, `MF_SPRITE_GALLERY=0`, compiles out the gallery, excludes
its textures from the disc and leaves normal gameplay rendering unchanged.
Switching configuration recopies sources so both main and gallery recompile;
stale gallery TGAs are removed from the disc staging folder when disabled.

The test disc boots into a static preview of both new characters over the
existing street, at native 88px height in the existing 320x240 viewport.
Press **A** on either connected controller to mirror both characters. Press
**Start** to leave the gallery for the original title screen, then Start to
play normally. Reboot the test disc to return to the gallery. Simulation and
music transport updates do not run in the gallery, and gallery input edges
are consumed before returning to the normal game.

## Pixel and positioning preservation

The six TGAs under `assets/gallery` are byte-for-byte copies of the approved
88px three-piece study candidates. Original full indexed PNGs are retained as
independent assembly references. No full asset generator was run. No existing
TGA, original animation metadata, `src/art_data.h`, game simulation or combat
configuration was modified.

Each character is divided at rows 20 and 76. Individual transparent margins are
trimmed, widths padded to eight pixels, and offsets recorded in
`src/gallery_data.h` and the separate gallery manifest. Runtime draws use
integer coordinates with no scaling. For right facing, a piece's top-left is
`(center - floor(full_width/2) + crop_x, ground - 88 + crop_y)`.
For left facing, x is `center + floor(full_width/2) - crop_x - padded_width`.
Mirroring includes transparent padding so all pieces reflect about one origin.

Gallery centers are x=90 and x=226. The foot boundary is y=210; the final visible
row is y=209. Both characters have exactly 88 visible rows, beginning at y=122.
All pieces use the same z=230, ahead of the z=500 street. They do not overlap
each other's occupied rows. Original gameplay anchors and world positions are
untouched; this gallery placement does not establish future combat-art anchors.

## Actual texture and palette costs

| Allocation | VDP1 bytes |
|---|---:|
| All original textures and HUD, including 32-byte per-texture alignment | 445,152 |
| Buck's three pieces | 5,344 |
| Chuck's three pieces | 5,440 |
| Gallery-only additional textures, beyond the six pieces | 0 |
| Total with gallery | **455,936** |
| Project texture capacity | 458,488 |
| Remaining | **2,552** |

The existing street and font provide background and labels. No new panel,
shadow or guide texture is allocated. One additional shared 256-entry palette
bank consumes 512 bytes of CRAM, separately from VDP1 textures. Six original
asset/runtime palettes plus font plus gallery use all eight configured banks.
Candidate TGAs contain 253 opaque RGB555 colors plus transparent raw index zero.
The pinned loader increments indices, so the transparent argument remains 1.

The loader reads the actual end address of the original last RGB texture and
checks the six aligned allocations before uploading. It checks dimensions and
the actual final allocation address, then displays measured texture bytes in
the gallery. It fails visibly if loading or budget checks fail.

## Validation and limits

`make check` validates the disc and exact executable, original assets, audio,
source identity and budget. The gallery extension validates the six ISO payloads,
shared RGB555 palette, index ranges, aligned sizes, header offsets, exact full
image reconstruction, mirrored assembly, and feet baseline. `make test` retains
every existing gameplay test and adds actual gallery C loader/draw tests for
both facings, palette restoration, gallery exit and pre-upload overflow rejection.
Both gallery-disabled and gallery-enabled builds must pass `make check`.

These are structural, pixel-assembly and host-mock checks. They do not establish
emulator boot, real Saturn/SAROO operation, visible absence of hardware seams,
controller response on hardware, or frame rate. No emulator is installed in
this workspace and no hardware is attached. On-device checks remain required:
boot the matching BIN/CUE, inspect both native sprites and feet, press A to check
mirrored seams, confirm the displayed allocation is 455936/458488, and use Start
to verify the original game and both controllers.

The added artwork is static; this experiment does not replace or add gameplay
animation. Its wider silhouettes do not change original hitboxes or reach.
