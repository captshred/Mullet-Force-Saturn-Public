# Four-pose sprint and running bat experiment

Historical report for05f2a58. For the current corrected artwork and memory figures, see [alternating-stride.md](alternating-stride.md). The combat implementation below is unchanged.

Parent: approved `afb8e61382ca5d947273e835654eb06d8e1d9705`; branch `dash-bat-attack-test`. No existing animation branch/work was present. All inherited assets remain byte-identical; locked PNG/TGA hashes are validated. This is new review artwork, not permission to change approved idle/walk/Corporate Punk art.

Opt-in `MF_RUN_BAT=1` requires approved dash preset B and the inherited full lighting/player/parallax configuration. Set it to0 to retain the approved three-pose dash and original combat. `src/run_bat_config.h` defines six simulation ticks per running frame and eight momentum ticks. Dash detection/release/reversal/window/speed, normal walk/idle, camera, world/depth clamps, shared tether, and existing collision rules remain unchanged.

## Input and combat

Priority: simultaneous B cancels dash as before. A on the second directional tap uses the existing planted-bat gesture. A on any later tick of an already active, eligible grounded dash uses running bat, even inside the old bat window or after many seconds. It consumes the same A edge and clears torch charge; no punch or double attack is emitted. Hit-stop queues that classification with the existing buffered A edge. Hurt, pause, disconnect or B discard a pending classification.

The existing seven-frame bat bank is reused with its36-tick swing, active ticks12–17, original reach78 and depth±8 (against the target's hurtbox), facing, hit mask, effects, hit-stop and defeat/respawn behavior. Running bat carries a fixed horizontal663/256 pixels per tick for eight advanced simulation ticks including activation, then stops during the rest of the swing. Input cannot redirect or accelerate the carry. Hit-stop freezes movement/timer. Boundaries and the co-op tether may shorten displacement. The carry ends before active bat frames in this first version: it positions the swing rather than providing a moving active hitbox. No invincibility is added.

Only running-bat hits on explicit `MF_ENEMY_CORPORATE_PUNK` targets reduce remaining HP to zero. Special-class targets take ordinary bat damage2. Existing punches, kicks, planted/air bats, torch, drums and scoring are unchanged. Multi-target hits use the existing per-target mask; each defeat scores250 once. No body-blocking/wall-map collision is introduced: the parent has neither.

The attack completes into normal held-direction walking or released idle. Fresh eligible neutral and a new double-tap are required to dash again; repeated A during the swing cannot restart it. This follows existing attack recovery without adding a cooldown.

## Art and resources

Eight generated reference poses are isolated by their actual alpha components, uniformly scaled per fighter (passing poses are not stretched), converted to the existing gallery palette with binary transparency and exported as native128×96 PNG masters. Root(64,92), two contact soles at row91; passing feet lift. Three disjoint cropped bands per pose use8-pixel width alignment/even heights and32-byte VDP1 allocation. All four poses per fighter have distinct pixel and leg content; whole-character facing is never used to fake opposite strides. Source guide, native/4x sheets, native/4x GIFs and walk/run comparison GIFs are retained in `assets/running`.

This pass adds24 unique pieces and41664 bytes. Byte interning found no identical pieces to share across the new frames; no duplicate frame uploads or P1/P2 copies are created. Boot allocation is404512 of458488 bytes:53976 free,159 texture slots. Delta+41664 bytes/+24 slots. No new palette: existing eight banks/4096-byte CRAM allocation. Existing bat artwork is reused. Gameplay state adds40 bytes over the approved dash milestone (two16-byte attack records plus two4-byte explicit enemy-class entries). No heap allocation or CD reads in gameplay/update/draw.

The old full six-frame comparison expansion would require480512 bytes, exceeding the texture budget by22024. In this opt-in build, gallery Down therefore opens a resident approved-walk/run comparison instead (Up toggles, B pauses, A mirrors, Left/Right steps). It performs no uploads. Prior build configurations keep the original full review gallery and every source asset remains present.

## Review limitations

The new running art is a first review pass from the approved master designs. Its leg silhouettes and pumping/overlap differ between contact phases; facial/pixel-cluster consistency and in-game foot-slip/game feel still need visual approval. Six-tick holds are initial timing, not matched mathematically to sole speed. Finite four-frame motion and reused legacy bat art produce a visible style/pose transition. No new weapon sprite or animation cache is included. This is not physical-Saturn validation.

Validation results and real controller-driven emulator captures accompany the review artifact.

## Completed local validation

Native BIN/CUE build, image/asset/music validation and all inherited gameplay tests pass. Focused tests cover both fighters/facings, >3-second dash activation, activation-tick planted priority, independent simultaneous swings, eight-tick cutoff, held/released recovery, multi-target/full-health KO and score once, special-class normal damage, lane rejection, hurt, jump and hit-stop buffering. Loader tests verify overflow preflight, exact cropped/mirrored reconstruction and zero extra preview uploads.

A900-frame controller-only local Yabause run observed all four run frames for both players in both facings.147725 visible native run pixels matched with zero differences;186 eligible dash velocity samples remained663/256 and21 carry samples matched that velocity. A full-health Corporate Punk was defeated on frame423 with the normal250-point award. Actual allocator state was404512 bytes/159 slots,53976 free; texture hashes stayed constant throughout gameplay. Onscreen captures/GIFs and the JSON report are in `docs/running-bat-captures`. The trace is read-only; no game-state injection was used. Emulator testing does not establish hardware frame pacing or WebRetro compatibility.
