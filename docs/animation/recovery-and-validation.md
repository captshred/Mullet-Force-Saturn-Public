# Recovery checkpoint and task status

The interrupted task was recovered on its existing local branch
`character-animation-upgrade`, still based at ba4938e. The branch had not been
pushed and all implementation/artwork was uncommitted. The recovered source,
master references, selected generated walk study, 14 native images, 36 indexed
textures, contact sheets, GIFs, HTML viewer, documentation and tests were saved
and pushed in recovery checkpoint **5a6bd36**. The unselected first generated
walk study is retained in the artwork archive; no generation was repeated.

## Complete for this preparation phase

* Existing animation inventory: 15 normal, 7 bat and 3 torch upper poses per
  fighter, plus shared lower pieces, original anchors, timing selectors,
  hitboxes, source hashes and aligned texture costs.
* Native authoring specification: 128x96 canvas, root (64,92), 88px standing
  silhouette, three bands, palette/transparency rules and padded mirroring.
* Budgeted VDP1 cache proposal, including source-bank RAM and palette limits.
* Approved idle reuse plus six unapproved walk candidates for each fighter;
  contact sheets, transparent PNG/GIF assets and standalone HTML visual review.
* Feature-flagged Saturn preview that keeps all original sprites and gameplay.
  Preview instructions are placed below the feet for unobstructed art review.

## Partial / awaiting visual approval

The six-pose walk is a first art study. Near/far leg support, face/torso
consistency, pelvis registration, foot contact and loop continuity need visual
approval and manual cleanup. Idle remains the exact single approved reference
pose; breathing variants have not been authored. Pixel/packing tests establish
coverage and alignment, not the artistic quality of the gait.

## Deliberately not started

No additional punch, jump, bat, torch, hurt or recovery candidate art, complete
moveset replacement, live animation cache/streaming implementation, additional
enemy gameplay or physical Saturn validation. Those follow cycle approval.

## Verification scope

The recovered logs already showed successful native build, make check and make
test. Existing Yabause captures show the preview, walking, pause/step/mirror,
diagnostics, parallax handoff and entry into original gameplay. Recovery rechecks
these using a freshly identified committed build and verifies disabled and
fallback configurations. Full-build identity and exact layout are in the
included BUILD-INFO, checksums and link map. Host tests also cover texture
preflight failures and unchanged animation-selector/collision contracts.

The local core is libretro Yabause v0.9.15, commit
8926b0c6c347f8c5c755911ddb0ac695420ffbf8, software renderer/interpreter,
HLE BIOS, one thread, no expansion RAM. It does not establish physical Saturn
performance, audio correctness, exhaustive combat playtesting or WebRetro
compatibility for this new candidate. The user-validated ba4938e milestone
remains intact on vdp2-parallax-test.


Final recovery verification: all seven build/asset configurations, existing
host tests and preview sanitizers pass. The committed reproducible runtime helper
verifies all seven poses in both facings and the parallax return, with 432,000
actor/ground pixels matching, plus exact pause and gallery restoration. See
validation.json for tested code hashes and README.md for the measured RAM layout.
Only preview text placement was corrected during recovery; all character study
pixels and original game assets were retained without regeneration.
