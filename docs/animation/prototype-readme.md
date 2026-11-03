# Buck and Chuck idle / walk artwork study

Branch `character-animation-upgrade` starts at the user-validated parallax
milestone ba4938e. No old assets, animation selectors, combat code, hitboxes,
controls or simulation timings are replaced. No branch is merged.

Open `preview.html` in the downloaded review folder for a local animated viewer;
all PNGs must stay beside it. `contact-native.png` shows actual 88px figures;
`contact-2x.png` uses nearest-neighbor enlargement. Individual RGBA PNGs and
transparent walking GIFs are included. GIF timing is quantized to 80/80/90 ms
repeated twice (500ms); the HTML and Saturn preview use equal 5/60-second holds.

The first column is the exact approved idle artwork, reused rather than
redrawn. The other six columns are **unapproved image-generated walk candidates**
referenced to the user masters and the old six-pose guide. No punch, jump, bat,
torch, hurt or recovery candidates have been generated. Idle is a single held
reference pose in this prototype; breathing poses remain future work.

Review anatomy/torso width, facial consistency, hairstyle/costume silhouette,
which leg supports weight, heel/toe contact and loop continuity at native size.
The two passing poses and two contact poses still need near/far-leg clarification
and pixel cleanup. Standing-to-walking guard width changes visibly. Labels name
intended phases, not an assertion that the generated gait is production ready.
The extraction centers silhouettes provisionally; manually register pelvis and
planted foot landmarks before promoting any frame into gameplay.

## Optional Saturn preview

```
MF_ANIMATION_PREVIEW=1 MF_SPRITE_GALLERY=1 MF_VDP2_STREET=1 make native
make check
make test
```

Add `MF_PARALLAX_DEMO=1` to retain the parallax preview as well. All experiment
flags default off except the existing VDP2 street. The animation flag requires
VDP2, the gallery and the fixed SGL display check. Original VDP1 fallback builds
remain available with MF_ANIMATION_PREVIEW=0.

Cold-boot the matching BIN/CUE. From the normal gallery:

* Down opens/closes the animation study.
* Up switches approved idle / six-frame walk.
* B pauses/resumes. Left/Right step walk frames and pause.
* A mirrors both fighters. C keeps the existing asset diagnostics.
* Start leaves the study and gallery, returning to the original title; Start
  again begins normal gameplay with its original characters.

Entering animation review closes parallax first, restoring the original street.
Leaving the study restores the original gallery. Animation state never enters
`mf_game` and does not drive its clock, input, damage or collision logic.

## Costs and scope

36 new 8bpp textures occupy **53,472 bytes including 32-byte allocation padding**:
Buck 26,656, Chuck 26,816. The six approved idle texture IDs are reused, with
zero duplicated idle uploads. No per-frame uploads, allocation, file reads or
palette changes occur. This prototype deliberately keeps all walk frames resident;
the future cache is a design proposal, not an implemented streaming system.

| VDP1 configuration | Allocated | Free / 458,488 |
|---|---:|---:|
| Existing VDP2 gallery | 302,336 | 156,152 |
| Gallery plus animation study | **355,808** | **102,680** |

Preflight checks the actual last idle texture address before uploading any new
pieces, and verifies every dimension and final allocation address. The shared
approved gallery palette remains bank 7, 253 opaque indices plus transparency;
all eight existing 512-byte CRAM banks remain allocated, with **zero new banks**.
No VDP2 allocations are added: with parallax enabled, layer allocations remain
123,008 bytes; 385,152 including SDK-protected reservations, 139,136 unassigned.
Without parallax they remain 106,624 / 368,768 / 155,520 respectively.

The candidate TGA payloads total 53,472 pixel bytes plus 36 x 786-byte TGA headers
and palettes (81,768 CD bytes); these pieces require no additional VDP1 allocator padding. The native
asset manifest is authoritative. Extra SH-2 memory includes 42 sprite IDs and
small preview state plus compiled metadata/code; the final link map gives the
complete image end. No retained CPU frame bank or dynamic animation cache is
introduced. Jo's TGA decoder uses temporary load buffers and frees them.

See `current-inventory.md/json` for all original frame resources, anchors and
contracts; `frame-spec.md` for the new native authoring format; and
`cache-architecture.md` for a budgeted future residency design. The review
pipeline only writes assets/animation-study and src/animation_data.h. It never
runs tools/draw-assets.py or regenerates the original sprite sheet.


## Recovery validation

All seven native configurations pass build and asset checks, including VDP1
fallback, preview-disabled builds, and preview with/without parallax. Existing
make test, animation-selector/collision contracts, preview controls/upload guards
and ASan/UBSan preview checks pass. Local Yabause runs cover pause/step/mirror,
diagnostics, parallax handoff, gallery restoration and entry to original gameplay.
Independent RGB comparison verifies all seven native poses for both fighters in
both facings, plus the restored idle after parallax: **432,000 actor/ground-region
pixels, zero mismatches**. Paused captures and the restored gallery match exactly.
This verifies rendering/packing, not artistic gait quality or real Saturn timing.
The machine-readable report is `validation.json`; selected captures are in
`runtime-captures/`. The code/data hashes in that report identify the tested source.

The complete resident image end is 0x06097094 with both experiments enabled,
versus 0x060965B4 for parallax alone: **2,784 extra bytes** of code, metadata,
preview state and alignment. With animation only, the increase is 2,816 bytes.
The preview's static state is 196 bytes (including its initialized facing value);
it is part of that image increment, not an additional allocation. The 384KiB
Jo heap reservation is unchanged; loader temporary peak was not separately
profiled. No CPU copy of the whole animation bank remains resident.

To reproduce the optional runtime checks, first build with animation, gallery,
VDP2 and parallax enabled, then run:

```
python3 tools/test-animation-runtime.py --core /path/to/yabause_libretro.so \
  --libretro-include /path/to/libretro-common/include --out /tmp/mf-animation-test
```

It uses real emulated controller input and a supplied existing core, and performs
no source edits. It requires Pillow and a host C compiler. Browser HTML syntax
is checked, but the HTML viewer and this new BIN/CUE still need user visual testing.
No physical Saturn, audio listening or exhaustive combat playtest is claimed.
