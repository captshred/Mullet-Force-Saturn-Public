# Running bat visual milestone

Branch `running-bat-visual-test`, parent verified `1eacf2bee026a058d179edf1c0b30888798f9316`. All prior branches preserved; no merges.

The running-bat mechanic is unchanged. This opt-in `MF_RUNNING_BAT_VISUALS=1` build adds presentation only: a shared aluminum bat in the existing trailing glove across all four run poses, and silver covers over the original wooden-bat pixels during running attacks. Normal planted/air bat artwork remains original. No hitboxes, damage, KO classification, speed, momentum, state, input or attack timing changes.

## Native construction and transition

One cropped 32-pixel-wide carry texture is shared by both fighters and all eight running poses. Per-pose integer glove anchors position the same dark grip behind the original fist. The body occludes the grip, retaining the original hands and arm artwork. Fixed weapon scale/angle, binary alpha, existing gallery palette and normal hardware mirroring. The character retains three body pieces; carrying the bat adds one shared weapon submission behind them. No head/torso/hair or running leg art is regenerated.

At running-bat activation the last running body pose and carried bat persist for the existing opening windup counter values 1–5. At counter 6 the renderer returns to the original swing sequence. Cropped metal-only textures cover exactly the existing visible wood pixels, keeping hands, geometry and all swing timing. The original body/weapon sources remain intact and no whole-body attack banks are duplicated. Crops retain their parent's height parity for the pinned SGL raster registration. A small bright band provides the metal transition ring where readable.

The shared carry texture plus deduplicated swing covers use 10 resources / 8512 bytes. Total VDP1: 410464 bytes, 48024 free of 458488,169 texture slots. Increment:8512 bytes/10 slots. Existing palettes/4096-byte CRAM unchanged. No assets removed, new animation states, per-frame CD reads or dynamic allocation in presentation/update/draw. The loader preflights the entire increment before uploads. Disabling the visual flag preserves the preceding build configuration and allocations.

## Bounded final leg review

The concept sheet was used only for weapon appearance and attitude, never for legs. Existing source frames and anatomical overlays were reviewed once. The prior isolated knee fragments are already removed; remaining awkward hip/crossing shapes need deliberate manual re-authoring, rather than another broad generated pose pass. No further leg change was accepted. As authorized, this build preserves the current playable alternating cycle and prioritizes bat integration. Near-contact→far-drive→far-contact→near-drive, native root(64,92),88px character scale and six-tick run holds remain unchanged. Before/after leg crops are intentionally pixel-identical; diagnostic overlays remain development-only.

## Review files and limitations

`assets/running-bat-visual` contains native/4× bat-carrying run sheets/GIFs, the isolated bat, swing masks and transition previews. `docs/running-bat-visual-captures` contains actual emulator captures and test data. Current run masters, normal walking/idle, Corporate Punk, original combat, music and backgrounds remain unchanged.

The reused legacy swing body still differs stylistically from the detailed running art. The carry bridge avoids an immediate weapon disappearance; switching to the original coil at tick6 is a discrete pose/angle change. Existing attack weapon lengths/foreshortening are retained. Further full high-detail attack animation is not included. Hip polish and inherited free-arm motion remain manual-review work, with no timing changes to disguise them. Physical Saturn/WebRetro compatibility requires testing in those environments.

## Completed local results

Native build, image/asset/music checks, all existing gameplay tests, new loader overflow/mirroring tests and independent two-player carry-bridge tests pass. In the 900-frame controller-only local Yabause run, all 605 recorded gameplay states, idle clocks, dash and running-bat state records matched 1eacf2b byte-for-byte. Velocity remained 663/256 on 186 eligible dash samples; the full-health Corporate Punk KO occurred on the same frame 423 with the normal 250-point score. No game RAM was written by the test.

The visual checks compared 14863 exposed carry-weapon pixels across all 16 fighter/pose/facing combinations, 19186 windup-bridge pixels for both fighters and 8509 unobscured metallic swing pixels. All matched with zero differences. Active hit effects and screen clipping occlude some swing samples; static source-mask tests verify all authored swing poses separately. Runtime allocation was 410464 bytes/169 slots, 48024 free; texture hashes remained stable throughout gameplay.

Capture GIFs show actual running-to-swing, normal planted bat, left-facing attack and KO. Static transition sheets illustrate all legacy swing poses and the carry bridge. Remaining hip/crossing polish and the legacy-body style transition are explicitly deferred. Physical Saturn and WebRetro playtests remain outstanding.
