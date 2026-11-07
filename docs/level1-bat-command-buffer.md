# Level 1 punch-to-bat command recovery

Parent/tag: the-one-v4-source-complete,
1e7077616f7da57436500b3d9cddda2e61e6a727. Branch fix/level1-bat-command-buffer.
This is an unreviewed local candidate; do not publish or merge it automatically.

Root cause: dash_input cleared tap history on every active attack, and bat
classification required !attack. Thus FF during punch/recovery could never arm
a bat; its A could instead become a buffered repeat jab. Even a retained command
would have been erased by the unconditional end-of-attack running_bat reset.
This is a recognition/priority/state-lifetime problem, not a tunable bat cooldown.
The new regression fails against the exact approved parent's game.c.

Grounded ordinary punches now permit input-only double-forward recognition using
the existing inclusive12-tick dash window and neutral/edge rules. The existing
released field value2 represents completed FF while a punch remains active;
it never enables dash movement during that punch. Hit-stop may also recognize
this input-only command without advancing attack state. Other dash guards remain.

FF+A stores the existing running_bat pending command. It has priority over jab
repeat and torch capture, survives punch completion, and executes at the existing
repeat-attack transition: counter13 for jabs,17 for the cross. Current punch
hitboxes are active only through counter10, so this does not cancel active damage.
The existing bat activation path owns animation, pose, movement/carry, hit mask,
damage and SFX. No new attack variant, fire rate or damage constant is introduced.
Jump, hurt/death, disconnect and pause retain command cancellation. The command
is consumed once; ordinary A without FF retains existing punches.

No new state fields, heap allocations, PCM, textures or memory arenas. Level2,
all audio source/resources, artwork, camera and native build inputs are frozen
against the approved parent. SCSP high-water/free485812/38476; VDP1 33792B/28
textures/81 max commands; VDP2 65792 payload/434176 reservation; CRAM32 unchanged.

Tests: both players/facings, one through five recent punches, FF+A during
recovery, immediate late completion, earliest13/17 execution, hit-stop capture,
no dash boost during punch, no accidental jab/double attack/repeat bat, FF without
A, jump and pause cancellation. Existing fast-bat tests verify idle/running A,
all running phases, both players/facings, unchanged active frames, one whoosh and
one contact, damage and score. Current combo/jab/movement/ground-air bat/combat/
coop/torch tests run with UBSan alongside full historical and recovered suites.
Exact preservation checks permit only the Level1 source/test/validation delta.

Native source build: tools/build-source-complete.sh. Full clean verification:
tools/verify-canonical-build.sh. Review and emulator/hardware playtesting remain
necessary; no subjective feel or owner approval is claimed. No Actions, remote
branch push, tag or merge is performed for this task.
