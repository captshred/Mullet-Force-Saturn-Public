# Repository consolidation and branch-cleanup proposal

Snapshot: 2026-10-30. This audit inspected **all 39 remote branches**, **zero pre-existing tags** and **zero PRs in all states**. No old branch was deleted, retargeted or merged as a cleanup action. Full SHAs, tree IDs, ancestry and recommendations are in [repository-audit.json](repository-audit.json).

## Approved baseline and preservation

- Approved source: `921ed1ddf78a1334684833a7c49633e404366817` (`player-run-waist-seam-fix`). The user build shorthand is `mullet-force-player-run-waist`; exact CI artifact is `mullet-force-player-run-waist-seam-<SHA>`.
- Verified original main: `178335ce694bf49c68c62d95b40dc7d02a8335ba`. It is an ancestor, **45 commits behind** with no main-only commits. There is no need to reset or force-push main.
- Annotated `v0.1-playable-baseline`: target `921ed1ddf78a1334684833a7c49633e404366817`, tag object `e51509c78614ec7cb8ea811fa6ef576cefe0b5c0`.
- Annotated `archive/main-before-v0.1-playable-baseline`: target `178335ce694bf49c68c62d95b40dc7d02a8335ba`, tag object `a7cf89dfc53a438e4c3d5959d30e36e677a3ae49`. Created/pushed before any main promotion.

Never retarget either tag. GitHub returned HTTP 403 for repository rulesets because this private repository plan does not support the feature. These are annotated, recorded preservation refs, **not server-enforced immutable locks**. No plan, privacy or permission settings were changed. An owner may choose an eligible plan/protection mechanism later; making the repository public is not part of this work.

## Promotion method and invariants

Use the related `repo-consolidation-v0.1` PR into main and a normal **merge commit**, preserving the original main and all approved ancestors. The consolidation branch starts at the exact approved SHA and changes only README, ART_WORKFLOW, ASSET_INDEX, CONTRIBUTING and these two audit documents. No manual game-tree copy, force-push, squash or history rewrite is needed. The PR and final merge are the authoritative promotion record.

Before merge, verify main still equals the archived original, PR head is the tested documentation commit, CI passes and the game/build/asset trees equal the approved tag. If main or PR head changes unexpectedly, stop and re-evaluate. After merge, compare all non-document files, rebuild the full approved profile, check actual disc sprite/audio payloads against the approved artifact and inspect the main-commit Actions run. Repository auto-delete-on-merge is disabled; do not enable `--delete-branch`.

Current full-profile command remains `bash tools/build-run-waist-seam.sh --native`. Plain `make` / `make native` remain historical base-profile controls. Build configuration and all 29 profile jobs are unchanged. Main contains the approved game plus organizational documentation; the original tag remains an exact snapshot, including its original docs.

## Unmerged work requiring preservation

Nine heads have distinct commits outside approved ancestry. Do not infer inclusion from a branch name or from its patch having been integrated elsewhere:

- Seven `artifact-export-*` heads contain unique ZIPs/reports or delivery workflows. Four have **unrelated histories**; the other delivery commits replace a source tree with a tiny export-only tree. They are delivery archives, not safer/newer game bases. Preserve their exact heads and binary exports before any later deletion; do not merge them.
- `custom-combat-sfx` has one distinct commit (`b45528b`) outside the approved ancestry. Its three source WAVs and FX.TON, FX.SEQ and CUSTOM.MAP are verified byte-identical to the approved restored HQ integration. Preserve the original source history with a tag before considering branch deletion; do not merge its older gameplay over current HQ art.
- `integration/latest-gameplay-fm-boost` has a distinct FM-integration commit and ten source/report paths absent from the approved tree. It is not part of the approved soundtrack. Keep it pending explicit owner/audio review.

## Classification at inspection

Main is listed as the active default line with its pre-promotion SHA; after the authorized merge its head changes to the promotion commit. The new consolidation branch is active during this task and is retained after merge. No independent active feature work can be established from the old milestone names alone.

| Category | Original branch count |
|---|---:|
| Active development | 1 |
| Current approved baseline | 1 |
| Historical milestone worth preserving | 28 |
| Superseded experiment | 8 |
| Unknown / requires review | 1 |

## Proposed cleanup list — approval required

**No deletion is authorized by this table.** There are 36 tag-first archive candidates, one FM branch to keep for review, the approved milestone branch to keep, and main to keep. For every archive candidate, first refresh its head, check for new collaborator work, create an annotated tag at that exact SHA, verify the remote peeled target, and preserve any unique exported ZIPs. Only then ask the owner to approve the specific branch deletion list. If a head changed since this snapshot, re-audit it rather than tagging/deleting the old assumption.

The proposed `archive/branches/...` tags below **have not been created**. Only the baseline and original-main tags above were created in this task.

| Branch | Inspected SHA | Classification | Proposal |
|---|---|---|---|
| `artifact-export-custom-sfx-b45528b` | `44baaf126dd1` | Superseded experiment | Tag `archive/branches/artifact-export-custom-sfx-b45528b`; archive candidate only |
| `artifact-export-fm-pcm-3f55ac9` | `4e93b6745787` | Superseded experiment | Tag `archive/branches/artifact-export-fm-pcm-3f55ac9`; archive candidate only |
| `artifact-export-latest-fm-6cd42a0` | `260a7bac6714` | Superseded experiment | Tag `archive/branches/artifact-export-latest-fm-6cd42a0`; archive candidate only |
| `artifact-export-sprite-gallery-b55ff47` | `a01275efab11` | Superseded experiment (unrelated history) | Tag `archive/branches/artifact-export-sprite-gallery-b55ff47`; archive candidate only |
| `artifact-export-vdp2-alignment-f653dca` | `51021535cb0f` | Superseded experiment (unrelated history) | Tag `archive/branches/artifact-export-vdp2-alignment-f653dca`; archive candidate only |
| `artifact-export-vdp2-background-dc962cd` | `399d7a1688f8` | Superseded experiment (unrelated history) | Tag `archive/branches/artifact-export-vdp2-background-dc962cd`; archive candidate only |
| `artifact-export-vdp2-runtime-8fb07eb` | `b8803abf3ccf` | Superseded experiment (unrelated history) | Tag `archive/branches/artifact-export-vdp2-runtime-8fb07eb`; archive candidate only |
| `bat-strike-momentum-fix` | `1686681ee6ff` | Historical milestone worth preserving | Tag `archive/branches/bat-strike-momentum-fix`; archive candidate only |
| `character-animation-upgrade` | `05b53c0e6d70` | Historical milestone worth preserving | Tag `archive/branches/character-animation-upgrade`; archive candidate only |
| `character-combat-animation-upgrade` | `176ba47494a7` | Historical milestone worth preserving | Tag `archive/branches/character-combat-animation-upgrade`; archive candidate only |
| `chuck-run-cleanup-player-hurt` | `99ac5d48ea5e` | Historical milestone worth preserving | Tag `archive/branches/chuck-run-cleanup-player-hurt`; archive candidate only |
| `chuck-run-denim-waist-cleanup` | `3f26c763306e` | Historical milestone worth preserving | Tag `archive/branches/chuck-run-denim-waist-cleanup`; archive candidate only |
| `chuck-run-final-fix-player-death` | `0fbc5fbb6918` | Historical milestone worth preserving | Tag `archive/branches/chuck-run-final-fix-player-death`; archive candidate only |
| `combat-attack-sequencing-fix` | `a7e1d0522cca` | Historical milestone worth preserving | Tag `archive/branches/combat-attack-sequencing-fix`; archive candidate only |
| `corporate-punk-hq-combat-test` | `53861e0a9591` | Historical milestone worth preserving | Tag `archive/branches/corporate-punk-hq-combat-test`; archive candidate only |
| `corporate-punk-integration-test` | `f45cad4b4d4f` | Historical milestone worth preserving | Tag `archive/branches/corporate-punk-integration-test`; archive candidate only |
| `corporate-punk-lighting-test` | `094c21e25f4a` | Historical milestone worth preserving | Tag `archive/branches/corporate-punk-lighting-test`; archive candidate only |
| `corporate-punk-scale-refinement` | `bf4e41df9c68` | Historical milestone worth preserving | Tag `archive/branches/corporate-punk-scale-refinement`; archive candidate only |
| `corporate-punk-sprite-test` | `c25d00c15805` | Historical milestone worth preserving | Tag `archive/branches/corporate-punk-sprite-test`; archive candidate only |
| `custom-combat-sfx` | `b45528b727b3` | Historical milestone worth preserving | Tag `archive/branches/custom-combat-sfx`; archive candidate only |
| `dash-alternating-stride-fix` | `aae373fb6fe1` | Historical milestone worth preserving | Tag `archive/branches/dash-alternating-stride-fix`; archive candidate only |
| `dash-bat-attack-test` | `05f2a58f42c5` | Historical milestone worth preserving | Tag `archive/branches/dash-bat-attack-test`; archive candidate only |
| `dash-leg-artifact-fix` | `1eacf2bee026` | Historical milestone worth preserving | Tag `archive/branches/dash-leg-artifact-fix`; archive candidate only |
| `double-tap-dash-test` | `afb8e61382ca` | Historical milestone worth preserving | Tag `archive/branches/double-tap-dash-test`; archive candidate only |
| `hq-blowtorch-animation-test` | `2ce28c4b0c2e` | Historical milestone worth preserving | Tag `archive/branches/hq-blowtorch-animation-test`; archive candidate only |
| `hq-build-custom-sfx-integration` | `bba999c0621f` | Historical milestone worth preserving | Tag `archive/branches/hq-build-custom-sfx-integration`; archive candidate only |
| `hq-jump-anatomy-fix` | `76f3002a21b6` | Historical milestone worth preserving | Tag `archive/branches/hq-jump-anatomy-fix`; archive candidate only |
| `hq-jump-animation-test` | `8c339aca6cef` | Historical milestone worth preserving | Tag `archive/branches/hq-jump-animation-test`; archive candidate only |
| `integration/latest-gameplay-fm-boost` | `6cd42a04021f` | Unknown / requires review | Keep; owner/audio review |
| `jab-cohesion-input-bat-cleanup` | `c50d7146f38a` | Historical milestone worth preserving | Tag `archive/branches/jab-cohesion-input-bat-cleanup`; archive candidate only |
| `main` | `178335ce694b` | Active development | Keep main |
| `original-three-walk-test` | `a44464fb5578` | Historical milestone worth preserving | Tag `archive/branches/original-three-walk-test`; archive candidate only |
| `player-run-waist-seam-fix` | `921ed1ddf78a` | Current approved baseline | Keep approved branch |
| `running-bat-visual-test` | `20b0fcf743ac` | Historical milestone worth preserving | Tag `archive/branches/running-bat-visual-test`; archive candidate only |
| `sprite-upgrade-test` | `b55ff47752f2` | Historical milestone worth preserving | Tag `archive/branches/sprite-upgrade-test`; archive candidate only |
| `swagger-walk-test` | `8e86fa1a4d7e` | Superseded experiment | Tag `archive/branches/swagger-walk-test`; archive candidate only |
| `vdp2-background-test` | `f653dcae9e16` | Historical milestone worth preserving | Tag `archive/branches/vdp2-background-test`; archive candidate only |
| `vdp2-parallax-test` | `ba4938ecac49` | Historical milestone worth preserving | Tag `archive/branches/vdp2-parallax-test`; archive candidate only |
| `walk-knee-lift-test` | `c3edb05bb3f6` | Historical milestone worth preserving | Tag `archive/branches/walk-knee-lift-test`; archive candidate only |

## Validation and remaining decisions

The approved BIN/CUE/ELF identity and hashes were verified against Actions run [41117479621](https://github.com/captshred/Mullet-Force-Saturn/actions/runs/41117479621), artifact [13007006445](https://github.com/captshred/Mullet-Force-Saturn/actions/runs/41117479621/artifacts/13007006445). Its full-profile source fingerprint is `8cf48b5b13830d1440ae88ac6914485a2c2aafb1f4057acb989f87918d7238b6`. A fresh native rebuild, `make check` and `make test` pass before promotion. The approved run already passed 29 CI jobs and native controller-driven Yabause comparisons. New PR/main CI results and merge SHA are recorded by GitHub and the completion report, not asserted in advance here.

Expected after promotion: unchanged 446,304 VDP1 bytes, 12,184 free, 253 definitions; identical `src/`, `assets/`, `tools/`, tests, build config and workflow relative to the approved SHA. Only the named documentation may differ. Approved audio hashes are permanently recorded in the JSON audit. No new emulator/hardware compatibility claim is implied by consolidation.

Owner decisions remaining after promotion:

1. Approve an exact later archive/delete list; no branch is deleted now.
2. Decide whether to retain or separately evaluate the alternate FM soundtrack. It stays outside main.
3. If server-enforced tag immutability is required, choose a supported protection/plan solution. Existing privacy remains unchanged.

Dustin’s visual collaboration is documented in the four root guides. No account invitation, collaborator permission change or message to another person is performed.

## Safe recovery

```sh
git fetch origin --tags
git switch -c recovery/approved-v0.1 v0.1-playable-baseline
git switch -c recovery/original-main archive/main-before-v0.1-playable-baseline
```

Use separate recovery branches; do not reset/force-push main or move preservation tags.
