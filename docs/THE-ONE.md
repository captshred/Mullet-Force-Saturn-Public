# MULLET FORCE — THE ONE

Approved, independently playable gameplay baseline:
`8d79a36f97dfd0b02de7d1b6b58e85b16fdc0b96`, from `art/arcade-impact-fx`.
Named reference: `the-one-v1`. This reference must never be moved to experiments;
GitHub ref protection still needs verification/configuration by an administrator.

Main integrates both the approved history and its previous workflow-only changes
without rewriting either history. Gameplay and runtime assets are exactly the
approved tree. Only the manual workflow, this record and a default build entry
point are added/updated. Level 1 gameplay development is separate on
`feature/level1-stage-clear`, rooted at the approved commit.

To reproduce THE ONE: Actions -> Manual Saturn playtest build -> Run workflow,
workflow branch main, source ref the full approved SHA above, profile
arcade-impact-fx. The source SHA is resolved and recorded, and existing disc,
asset/gameplay validation and matching BIN/CUE/checksum packaging are preserved.
To build Level 1 development, select feature/level1-stage-clear and profile
level1-stage-clear. Source branches/tags and full commit SHAs are editable inputs.

Only workflow_dispatch is enabled. Do not trigger Actions automatically.
