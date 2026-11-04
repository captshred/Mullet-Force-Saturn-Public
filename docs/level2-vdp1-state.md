# Level 2 VDP1/SGL state restoration

Parent: `b071808c5c41a7590a07b0ac11ff36e9aa27dc9f`.
The player reported a scrolling Level 2 NBG1 with no visible VDP1 objects after
successfully loading `/ALEVEL2`. This repair establishes the complete shared
sprite render state without changing any actor, projectile or world coordinates.

## Cause, evidence and limits

The confirmed code defect is incomplete ownership of the render state at the
handoff: the loader wrote PTMR=0, then restored an arbitrary sampled PTMR value,
and never established its own SGL sprite window, color decoding or eight
priority entries after the background schedule change. Restoring zero leaves
command execution stopped; restoring a one-shot value is not an automatic
frame-change restart policy. All six object types share this one render path.
The previous host mock only counted Jo draw calls and assumed an initial PTMR
of 2, so it could not catch stopped drawing, rejected SGL submissions, or hidden
sprite priorities.

The user's playtest contains no PTMR/SPCTL/PRISA/window register capture. It does
not prove which individual state value was wrong in that run. This is a concrete
restoration repair with a reproducing stopped/inherited-state regression, not a
claim to have measured the failing hardware state or validated the new pixels
in an emulator. A new native build and real playtest remain necessary.

The pinned Jo Engine revision is
`556d081146211b6a1cfa6591d70f9487d406758b`. The investigation inspected its
`core.c`, `sprites.c`, `jo/sprites.h`, and the actual SGL 3.02j `SL_DEF.H` and
`LIBSGL.A` (Git blob `b0be8d1423dce25c5d7b51d15ee96a0ad73b30f8`).
Relevant pinned library objects and contracts:

- `sglC00.o` / `slInitSprite` installs VDP1 PTMR=2. That is the established
  automatic frame-change drawing mode, not a guessed priority register value.
- `sglB063.o` / `slPriority` updates SGL's register shadow; the public
  `slPrioritySpr0` through `slPrioritySpr7` macros are the correct way to set all
  eight sprite priority slots. Direct writes to hardware PRISA can be overwritten
  by the next SGL VBlank transfer and are not used.
- `sglB015.o` / `slScrAutoDisp` builds the VDP2 fetch/display schedule. It does
  not substitute for initializing the sprite renderer. The new call includes
  the supported SPRON flag, and explicit sprite postconditions are applied
  afterward. There is no evidence here that this helper alone cleared PRISA;
  this repair does not claim that as the measured cause.
- `sglC20.o` / `SpriteEntry` rejects a depth at or nearer than
  `screen_distance >> depth_level`, or beyond the window's far limit. SGL's
  320-wide TVSizeTbl stores half-width 160, so its normal default near cutoff
  is 80 at level 1. The existing Z=100 alone is therefore not an explanation
  for this failure. The repaired window makes these values explicit and a
  compile-time guard checks the unchanged Z against them.
- `jo_sprite_free_all()` calls `jo_sprite_free_from(0)`, resetting the allocator
  cursor and last definition ID. Jo and SGL continue to use the same static
  texture-definition array. No full Jo/SGL initializer or undocumented
  `slInitSprite` call is needed after this release. Calling `jo_sprite_init()`
  alone would not reset Jo's texture address cursor and is not used.

## Exact initialization sequence

The existing three empty callbacks / real-VBlank drain and EDSR completion check
remain. PTMR stays stopped while old textures are released and all nine assets
are loaded from `/ALEVEL2`. After configuring NBG1:

1. `slScrAutoDisp(NBG0ON|NBG1ON|SPRON)` establishes the background schedule.
2. `slSetSprTVMode(TV_320x240)` establishes VDP1's supported SGL display mode.
3. `slCurWindow(winFar)` and `slFrameClipSize(320,240)` select the expected frame.
4. `slWindow(0,0,319,239,1024,160,120)` establishes a full-screen system clip,
   far depth 1024, and local origin at screen center. A rejected window is a
   fatal E107 / VDP1 WINDOW error; no sprite rendering proceeds.
5. `slSetScreenDist(160*65536)` and `slZdspLevel(1)` establish an accepted
   depth interval for the unchanged sprite Z=100 (near cutoff 80, far 1024).
6. `slSpriteColMode(SPR_PAL_RGB)` enables the RGB555 texture bank. Both the
   sprite-pixel window and VDP2's sprite screen-window restriction are disabled
   through `slSpriteWinMode(OFF)` and `slScrWindowModeSPR(0)`.
7. All eight `slPrioritySprN(4)` slots are set through SGL. NBG1 stays at 1 and
   NBG0/text stays at 7, so sprites are above the city and below the HUD.
8. PTMR is explicitly set to 2. Jo's existing core `slSynch()` submits/restarts
   the fresh command lists; there is no second core loop or recycled Level 1 list.

The existing per-frame Jo attribute reset still clears horizontal/vertical flip,
transparency/dark/gouraud effects, scaling and user clipping before submission.
That reset complements the SGL system/local-coordinate/window reset above.

## Verification and preservation

The runtime host test now includes the actual runtime translation unit so it
can exercise its real static renderer without adding production test hooks.
Its SGL mock deliberately starts with PTMR=0, and poisons inherited RGB, window,
depth and priority state at the background schedule call. It requires the exact
initialization order, all eight priority slots, valid Z, RGB decoding, automatic
drawing and unrestricted sprite windows before accepting any draw.

A fixture independently populates Buck, Chuck, a drone, player shot, enemy shot
and explosion, then calls the real renderer with no gameplay update. All six
texture IDs must be submitted through the corrected shared path. No diagnostic
texture or visible test block is shipped. The test also injects SGL window
failure and requires stopped drawing plus the specific error. Existing asset,
resource-lifecycle and `/ALEVEL2` error/restoration tests remain active.

`make test` exits 0 with 186 PASS reports. The runtime test also passes UBSan.
Approved artwork/SFX2/source preservation, city/skyline checks and stage-clear
regressions pass. All 633 existing asset blobs (623 old assets plus the shooter
bank and its manifest) remain identical. No preservation hashes needed updating:
protected Level 1 modules, the shooter simulation, staging helper, filesystem
repair, workflow and native build configuration are unchanged.

Resource budgets remain six definitions / 7,552 VDP1 texture bytes, 10,944 VDP2
payload bytes in the same arenas, 32 CRAM payload bytes, the same SCSP release,
and 32 player shots / 16 hostile shots / eight drone slots. There is no extra
texture, projectile pool, gameplay allocation or gameplay coordinate change.
SGL owns its existing window/system-command bookkeeping.

No Actions run has been triggered. This environment has not rebuilt the repaired
native BIN/CUE or verified visible pixels on Saturn/WebRetro. Retest the existing
manual `stage-default` build at the delivered commit, complete the real Stage
Clear handoff, and verify both players, both bullet types, drones and explosions.
If sprites remain absent, capture PTMR/EDSR/SPCTL/PRISA and SGL draw acceptance
rather than claiming a specific register value was observed from host tests.
