# Source-complete SFX timing candidate

Parent and preserved owner-tested tag `the-one-v3-source-complete`:
`6596c96d30569bdfc0fdaa0b72e6da4bab0a32e0`. The original `the-one-v3` tag
remains historical. This feature is unapproved pending owner WebRetro testing.

Both players share Shot controls/channels 2 and 3, unchanged PCM/program/gain.
Successful projectile allocation already sets one owner event bit; failed
allocation sets none. Each event requests one attack. Prefer a FREE Shot;
otherwise select the greatest unsigned age of the last accepted Note On.
An alternating tie-break index handles same-tick starts. Send control-local
Note Off/key60 to that Shot only, then immediately Note On to the same control.
RESTARTING retains selection if the stop succeeds but the new start is rejected.
Natural retirement after the old lease is preserved. Four pending Shot requests
retain bounded retry behavior; prolonged SDK failure may still overflow it.

Explosion controls/channels 4..7 retain gain100, PCM and the 49-tick conservative
retirement lease. `MF_WS_EXPLOSION_MIN_SPACING=5u` VBlanks gates accepted starts
only. FREE controls are selected in index order. Never stop an occupied Explosion
to make space; completed keys are still retired naturally. The existing pending
counter now has fixed capacity `MF_WS_EXPLOSION_PENDING_MAX=8u`; identical events
need no payload FIFO. Requests drain in arrival order, and newest excess is
counted/dropped. No visual/gameplay event is delayed. Fixed capacity also avoids
unsigned room underflow as pending requests fill free controls.

Only two new unsigned words (8 bytes) track Shot tie-break and Explosion next
start. RESTARTING occupies the existing state field. No PCM or heap allocation.
SCSP high-water/free stay 447588/76700. VDP1 stays 33792 bytes/28 definitions/81
maximum commands; VDP2 payload/reservation stay 65792/434176; CRAM stays32 bytes.

All music, Flame, readiness, runtime and gameplay code/resources are frozen
except these scheduling paths. Music control0/gain127, Flame control1/channels0/1,
38-tick handoff, independent releases, consumed-command cursor0x041a and all
neon resources remain unchanged. The complete source-complete-parent lock is
additive to the unchanged historical recovery lock. Documentation clarifies
canonical owner approval without moving the preservation tag.

Current-source tests cover actual allocation/attack equality, full projectile
pool silence, free-first/oldest reuse, same-tick ties, control-local isolation,
partial command rejection, 100/105/110 and 100/106 starts, occupied-pool retention,
eight-event overflow, overlapping tails, no early Explosion stop, clock wrap,
and dense dual-Flame/music/dual-Shot/Explosion stress. Recovery/UBSan/readiness
mutation and current gameplay/camera/runtime tests remain active.

Release verification: commit all files, create an empty detached checkout of
that commit, then run `bash tools/verify-canonical-build.sh`. BUILD-INFO and
CANONICAL-SHA256SUMS identify the exact source and BIN/CUE. The build compiles
committed source; the preserved executable is only a validation reference.

Manual Actions: workflow from main, profile stage-default, source_ref the exact
feature delivery SHA. No automatic Actions run or feature THE ONE tag is created.
