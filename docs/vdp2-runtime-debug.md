# dc962cd runtime loading failure: diagnostics and return-check fix

Work remains on `vdp2-background-test`; the preserved gallery branch stays at
`b55ff47752f2708c44587d687a9e95d784708137`. No merge into either protected branch.

## Confirmed cause

The pinned SGL `slScrAutoDisp()` returns **0 on success and -1 on failure**.
dc962cd used `if (!slScrAutoDisp(...))`, turning successful setup into a failed
street load. Its host mock incorrectly returned 1 for success, masking the bug.

The functional fix is to reject a **negative** return, retaining the original
display configuration, tile/map data, palette, allocation checks and artwork.
The SDK binary was inspected: the success path loads r0=0 at function offset
0x31a; the give-up path loads r0=-1 at offset 0x27c. SDK pin is unchanged.

Native libretro Yabause 0.9.15 core at commit
`8926b0c6c347f8c5c755911ddb0ac695420ffbf8`, software renderer, interpreter,
one rendering thread, no RAM cartridge and HLE BIOS reproduced dc962cd's
original generic banner with the already-loaded street visible behind it.
With the corrected check, the gallery and original gameplay load, Start exits
the gallery and starts the game, and scripted left/right input scrolls the street.
The VDP1-control build also loads the gallery and original game in that core.

This is a native Yabause-core test, **not** a claim of successful execution in
the user's exact WebRetro browser build. WebRetro confirmation remains required.
No real BIOS was downloaded or bundled. No physical Saturn testing was performed.

## Diagnostic builds and controls

Normal fixed build: `MF_VDP2_STREET=1 MF_STREET_LEGACY_CHECK=0`.
Control: `MF_VDP2_STREET=0 MF_STREET_LEGACY_CHECK=0`.
Failure repro only: `MF_VDP2_STREET=1 MF_STREET_LEGACY_CHECK=1`.
All playtest builds use `MF_SPRITE_GALLERY=1`.

The legacy switch exists exclusively to reproduce the dc962cd check while
displaying diagnostics. It defaults to 0 and is recorded separately in the
executable source fingerprint and BUILD-INFO.txt. Do not use the repro build
as the fixed candidate; it is expected to stop with E110 / S150 / AUTO0.

On any asset error, the first failure is retained and shown with its stage,
item and index. A street failure stops the remaining initialization rather than
being obscured by later operations. On success, press **C in the gallery** to
show the same diagnostics; C again returns. A and Start retain their existing
gallery behavior. In normal gameplay, C retains its existing diagnostics role.

## Street diagnostic codes

| Code | Meaning |
|---|---|
| S000, STEP199 | Street load completed |
| S101 | Street palette ID differs from required bank 1 |
| S102 | Root lookup of 0.BIN or ST0.TGA failed |
| S110 / S111 | Cell allocation NULL / address not 0x25E00000 |
| S112 / S113 | Map allocation NULL / address not 0x25E40000 |
| S120 / S121 / S122 | STCELLS.BIN missing / read returned NULL / wrong length |
| S130 / S131 / S132 | STMAP.BIN missing / read returned NULL / wrong length |
| S140 / S141 / S142 | STPAL.BIN missing / read returned NULL / wrong length |
| S150 | Display setup rejected; AUTO shows the actual SGL return |
| S160..S164 | Original VDP1 street TGA load failure, indexed 0..4 |

The screen also records startup bitmap, returned cell/map addresses, palette ID,
root file IDs, each BIN lookup ID, reported length versus required length,
completed-read mask, last operation, build commit and source hash. Mask bits
1/2/4 correspond to cells/map/palette; mask 7 means all three finished. Values
-99 or lengths -1 mean an operation was not attempted or a size was not returned.
The SDK's NULL read return combines allocation and I/O failure; S121/131/141
identifies that exact API failure without pretending to distinguish its internals.

Asset-level E100/200/300/400/420/500 distinguish palette creation stages;
E110 selects the detailed STREET report; E210/310/410/510 identify actor/effect
loads with the exact TGA filename and index. E600 identifies true-color assets,
E610 HUD allocation, E620/E621 HUD textures, and E700 optional gallery setup.
Music readiness is observed without changing the existing music error policy.

## Filesystem and resource checks

Jo calls `jo_fs_init()` inside `jo_core_init()` before returning to `jo_main()`.
The diagnostic records that core initialization returned, then probes known
root-directory files. It does **not** rerun filesystem initialization or claim
to capture an initialization return value that Jo does not expose to the app.
Successful root probes and complete reads establish actual filesystem readiness.

The generated ISO directory contains `/STCELLS.BIN;1`, `/STMAP.BIN;1`, and
`/STPAL.BIN;1`. They are uppercase root files with valid 8.3 names and have
90,240 / 16,384 / 510 bytes. Jo uses the corresponding bare uppercase names.
`JO_ROOT_DIR` is NULL in this SDK, meaning no directory change; GFS starts at
the root and there is no earlier directory change before street loading.

Successful runtime diagnostics show palette 1, bitmap/cells 0x25E00000,
map 0x25E40000, complete expected lengths, read mask 7 and AUTO0.
The diagnostic repro reaches the same addresses and reads before reporting S150.
Thus missing files, filesystem timing and allocation-address conflicts are not
the confirmed cause of this banner. No names, paths, tile data or palette data
were changed to make loading pass.

VDP1 usage remains 302,336 / 458,488 with the gallery; VDP2 street allocation
remains 106,624 bytes. Diagnostics use the existing text layer, not new textures.

## Remaining runtime checks

Cold boot the fixed ZIP in WebRetro Yabause without a saved state. Confirm the
gallery, C's S000/STEP199/AUTO0 page, Start transition and original gameplay.
If it still fails, capture E/S/STEP/AUTO, addresses and read lengths from the
screen along with the build/source identity. Test the supplied VDP1 control in
the same browser session/settings. The repro ZIP should intentionally show S150.

The runtime comparison also exposed a pre-existing one-pixel background
registration difference: in this core the dc962cd VDP2 street is one pixel
up/left relative to the VDP1 control. The overlapping scenery pixels match
after that translation. This loading fix deliberately leaves registration
unchanged; it does not claim full pixel-for-pixel alignment between renderers.
Player/gallery art and gameplay were not changed to compensate. Hardware,
audio listening, exhaustive combat playtesting and WebRetro remain outside
the local loading smoke test.


## Registration follow-up

The loading fix above is preserved unchanged in the ancestor `8fb07eb`. The
one-pixel registration limitation was subsequently corrected in `street.c`;
see [VDP2 registration validation](vdp2-registration.md). The user confirmed
that the `8fb07eb` fixed disc loads both gallery and gameplay in WebRetro Yabause.
