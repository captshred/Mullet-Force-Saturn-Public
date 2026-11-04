# Approved dual impact and explosion FX

Foundation: `2c32e134452d5cd90fcbfee2aba13c2ce6b0166b`, complete HQ gameplay,
city cleanup/neon, quarter-speed live skyline parallax and SFX Update 2.

The approved gallery's native 32x32 LEFT spark is `assets/cd/HIT.TGA`.
The RIGHT explosion is `assets/arcade-fx/EXPLODE.TGA`. These runtime files are
lossless exports of the approved pixels, not redesigned effects. Their hashes,
approved review image hashes and RGB555 pixel hashes are in the FX manifest.

`MF_ARCADE_FX=1` replaces only the obsolete legacy Buck idle-breathe upload
(`BU01.TGA`, indexed8, 48x54, 2592 bytes) with the explosion (RGB555, 32x32,
2048 bytes), at the same point in initialization. HQ idle/gallery pieces remain
unchanged. The original BU01 file remains present on disc. With the flag off,
the original indexed upload and fallback behavior remain intact. Incomplete
profiles cannot enable the substitution.

| Allocation | Approved foundation | Dual FX |
| --- | ---: | ---: |
| Sprite definitions | 255 | 255 |
| VDP1 texture bytes | 453344 | 452800 |
| Free against 458488-byte capacity | 5144 | 5688 |
| VDP2 reserved bytes | 434176 | 434176 |
| SCSP high water bytes | 432308 | 432308 |

The original flash, respawn and spark clocks, anchors and depth keys are retained.
Surviving props use LEFT; destroyed props use RIGHT. The existing global spark
uses the last impact's type. A presentation observer reads newly set hit-mask
bits after each simulation step in the same player/drum/enemy resolution order,
so simultaneous prop breaks and enemy hits are classified without position
heuristics, changing gameplay state, or changing the game structure ABI.
Both definitions remain stable throughout rendering; there is no per-frame
upload, alias mutation, new particle, palette allocation or sound change.

## Build locally

On the supported x86-64 Linux environment:

```sh
git switch art/arcade-impact-fx
bash tools/bootstrap.sh
bash tools/build-arcade-impact-fx.sh --native
make check
make test
python3 tools/validate-full-gameplay-sfx2.py --disc
python3 tools/validate-arcade-fx.py --disc
python3 tools/audit-sprite-memory.py > build/sprite-memory.csv
```

The unchanged pinned Docker build is also available through
`bash tools/build-arcade-impact-fx.sh` after SDK setup. Keep the matching
`build/mullet-force.bin` and `build/mullet-force.cue` together; open the CUE.
`build/BUILD-INFO.txt` identifies the source SHA and `Arcade dual FX: 1`.

## Manual GitHub build

Open **Actions → Manual Saturn playtest build → Run workflow**. Select branch
`art/arcade-impact-fx` and profile `arcade-impact-fx`. Leave `commit_sha` empty
to use that branch's selected head, or supply that exact full SHA.

Equivalent explicit manual command:

```sh
gh workflow run build.yml --ref art/arcade-impact-fx -f profile=arcade-impact-fx
```

The workflow has only `workflow_dispatch`; pushes and pull requests do not start
it. It validates the complete disc and uploads one matching BIN/CUE artifact
with checksums and one-day retention. The older `full-gameplay-sfx2` profile
remains pinned to the original approved foundation.

## Validation scope

`make test` includes real damage-resolution/draw-mock cases for both players,
nonlethal and lethal props, equal-position enemy/prop hits, simultaneous LEFT
and RIGHT rendering, and unchanged flash/respawn predicates. The boot-loader
audit runs the actual initialization functions with bounded host mocks, then
compares dual and legacy profiles: 255 definitions in both, with only slot 1's
payload changing. All other dimensions, formats and allocation sizes match.

The original preservation map remains intact. The small authorized set of
source/build changes is recorded separately with before/after Git blob hashes.
An additional SHA256 map protects every other foundation file, including all
gameplay, character, background, parallax, audio and original BU01 payloads.
Host tests and structural disc checks do not establish emulator/hardware visual
or performance compatibility.
