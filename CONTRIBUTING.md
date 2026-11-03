# Contributing

Main is the preferred development line. Start from it, not an older experiment
whose name happens to sound newer. `v0.1-playable-baseline` preserves the exact
approved source `921ed1ddf78a1334684833a7c49633e404366817`; the archived original
main is `archive/main-before-v0.1-playable-baseline`.

## Branches and pull requests

```sh
git fetch origin --tags
git switch -c art/chuck-new-pose origin/main
```

Use a descriptive, scoped branch: `art/<character>-<action>`,
`fix/<subsystem>-<issue>`, `docs/<topic>` or another agreed task name. Preserve
existing experiments and uncommitted work before switching or creating branches.
Never force-push main, reset a milestone tag, delete a remote branch without
approval, or merge unrelated experimental work as part of a cleanup.

Open a PR into main. State the concrete problem, parent SHA, resulting behavior,
changed asset/logic scope, memory delta, validation and remaining limits. Link
native previews and the exact playable artifact. Use merge commits for milestone
promotions so approved ancestry remains recoverable. Other PR merge methods are
a project-owner decision; do not rewrite existing public/shared history.

Art and gameplay changes should have separate review scopes. Dustin collaborates
on visual direction and native animation quality; follow [ART_WORKFLOW.md](ART_WORKFLOW.md).
Do not infer changes to movement, timing, hitboxes, AI, damage, controls or audio
from an art approval. The project owner approves the playable result and baseline
promotion. Do not invite collaborators or alter repository permissions implicitly.

## Build the correct profile

```sh
bash tools/build-run-waist-seam.sh --native
make check
make test
```

Or omit `--native` for the pinned Docker toolchain. See [README.md](README.md)
for initial setup. Plain `make` / `make native` still build the historical base
profile for compatibility tests; they are not the full HQ release command.
Keep the Jo Engine/compiler/Docker pins unchanged. Run `make clean` after engine
module configuration changes. Do not commit `.deps/`, `build/`, BIOS images or
unrelated generated exports.

The wrapper preserves approved audio and enables the HQ character/enemy,
jump/torch, hurt/death, walk/run/waist, VDP2 and custom-SFX configuration.
Verify `build/BUILD-INFO.txt`, the Git SHA, source fingerprint and profile flags
before comparing builds. A successful older profile is not proof of the HQ one.

## Validation expectations

- Run checks relevant to the change plus the existing `make check` / `make test`.
  Native builds use the bundled SH-2 compiler; host-C tests exercise simulation
  and mocks, not the Saturn executable itself.
- Preserve immutable source/hash references. Register a new candidate/override
  explicitly rather than deleting reference assets or weakening old checks.
- Inspect actual VDP1 bytes, free space, palette allocation and sprite definitions
  before and after adding art. Include existing HUD, effects and definition-only
  views. Main starts at 446,304 / 458,488 bytes and 253 / 255 definitions.
- Verify native indexed reconstruction, alpha, roots, both mirrors, seams and loop
  boundaries. Changes to shared pieces require every consumer to be checked.
- Check the actual packaged ISO payloads and matching BIN/CUE hashes, not just
  files left in a workspace. Keep the CUE's MODE1/2048 declaration.
- For relevant playable changes, use controller-driven emulator captures and
  compare simulation against the approved build. Clearly separate offline art
  previews, native emulation, browser emulation and physical hardware results.
- Preserve custom WAVs/FX payloads and STAGE.SEQ/TON unless an audio change was
  explicitly requested. Do not regenerate the entire art sheet or sound banks
  merely to compile a sprite experiment.
- Report failed/unavailable tests honestly. Do not change gameplay solely to
  make artwork or a validation script pass. Compilation is not a hardware
  performance or compatibility certification.

Optional runtime scripts are `tools/test-*-runtime.py`; they require a built
Yabause/libretro core, headers, COFF-capable `sh-elf-nm`, NumPy and Pillow.
The existing test frontends may provide real pad sequences; they are not game
controls or authorization to inject RAM changes and call them normal play.

## Review builds and CI

GitHub Actions retains multiple historical profile jobs as regression coverage.
The current approved full-profile job is `player-run-waist-seam-fix`, producing
`mullet-force-player-run-waist-seam-<SHA>`. Do not hand off a generic legacy
artifact under the HQ build's name. Include the BIN/CUE pair, build identity,
checksums, previews and explicit emulator/hardware limitations.

Artifacts can expire. Keep stable source tags, reports and payload fingerprints.
Never claim that a local `/workspace/...` file is downloadable without verifying
the supported export or published artifact. CI status can lag publication;
verify the artifact's commit and payloads before handing it off.

## Tags and later cleanup

Annotated milestone and archival tags are never retargeted or force-replaced.
Record their tag object IDs and peeled commit targets. The current private-repo
plan rejects tag-ruleset access, so this policy is not a server-enforced tag lock;
changing account/visibility settings requires an explicit owner decision.

The [branch audit](docs/repository-consolidation.md) is a proposal, not a deletion
instruction. Before any approved future deletion: refresh the head, confirm no
new work, create/verify an annotated archival tag at that exact head, preserve
unique ZIPs/reports, and check the owner-approved list. An ancestor check does
not prove an unrelated delivery branch or alternate soundtrack has been saved.
Do not close or merge unrelated PRs. No branch deletion or automatic branch
cleanup is part of this consolidation.
