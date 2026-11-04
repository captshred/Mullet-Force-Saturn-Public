# City stage: Sunset Strip lighting candidate

Review branch: `art/city-neon-stage`, from public approved bat-fix commit
`b1abb866aa0f6cfd09794a0ed76e5f054a6ecf6f`. This is an opt-in visual candidate,
not a promotion of new art to main. The manual Actions workflow on main offers this playtest profile and the
known-good bat-fix profile. Game/art code is not merged into main, and no
workflow is automatically dispatched.

## Art direction

The 640x240 city layout, roofline, four businesses, streetlamp supports,
sidewalk/curb, moon and fighting lane are retained. The candidate adds cool
roof/awning recesses, richer brick values and weathering, layered glass
reflections, arcade cabinet silhouettes/screens, record-shop details and small
posters. Cyan arcade light, magenta club light and warm lamps provide distinct
local color accents. The road remains dark navy with thin wet-neon reflections
and low-contrast wear, keeping the highest contrast above the combat plane.

ION ARCADE is the hero: cyan tubing and a soft blue surround, with magenta trim.
The neighboring signs remain secondary. No player/enemy artwork, roots, sprite
scales, gameplay code, controls, attack timing, collision, camera behavior or
sound assets were changed. Existing source art and runtime locks remain intact.
A generated high-resolution study was reduced to the native raster and RGB555;
the high-resolution master/review exports remain outside the public source tree.
`assets/city-neon/CITY555.BIN` is the native RGB555 source of truth (640x240,
big-endian words). No historical generator or original street asset was replaced.

## Build and rollback

```sh
# Review candidate; same complete punch-combo/fast-running-bat gameplay profile:
bash tools/build-city-neon.sh --native
make check
make test
python3 tools/audit-sprite-memory.py

# Restore the approved artwork with the existing wrapper:
bash tools/build-punch-combo.sh --native
make check
```

Both wrappers support the pinned Docker route by omitting `--native` when Docker
is available. The candidate requires VDP2 and is explicitly selected with
`MF_CITY_NEON=1`; the default is zero. `BUILD-INFO.txt` records that selection and
the source fingerprint. The committed playtest build is rebuilt from a clean
checkout so the embedded Commit identifies its exact source. For this environment
only, the existing local
`genisoimage` installation is made available with:

```sh
export PATH=/workspace/work/mullet-bat-final/genisoimage-local/usr/bin:$PATH
```

Art re-export uses `python3 tools/build-city-neon.py` with NumPy and Pillow.
Normal builds copy committed candidate payloads; they do not require generating
art or changing SDK/compiler pins. Re-export reconstructs the indexed/native
palette, the cell atlas, two-page map and compatible long-map preview payloads.

## Saturn implementation

The existing NBG1 street owner loads `CICELL.BIN`, `CIMAP.BIN`, `CIPAL.BIN` for
the candidate. Original ST assets remain on disc and in source for the default
and VDP1 fallback profiles. The same camera registration, clipping window,
priorities, two-page map and tile stride are used. No new render layer is added.

A 224-color static palette plus eight region-specific live colors fits in the
existing street CRAM bank. Live cell indices 240..247 occur only in the arcade
sign/interior ROI; the packer/validator enforces this. Palette data offsets
239..246 account for the pinned Jo bank+1 convention. Characters and all other
palette banks are untouched.

`mf_street_animate()` runs from the existing VBlank callback only in the
candidate. It updates eight 16-bit colors once per eight VBlanks:

- A roughly 4.27-second 90–100% breathing cycle, quantized to RGB555.
- Cabinet colors offset in phase from the sign.
- One letter group dips to 65% for eight VBlanks (about 133 ms), once per
  1024 VBlanks (about 17.07 seconds). The sign never blacks out.

The palette clock uses hardware VBlank time and does not change simulation
ticks, pause/hit-stop behavior or game state. Repeated timestamps are idempotent,
and unsigned wrap is tested. The animation does no allocation, CD access, map
update or texture upload. Budget: at most 16 bytes of CRAM stores per update,
120 bytes/second at 60 Hz, plus a small amount of palette arithmetic.
The effect uses an eight-byte SH-2 pointer/step state and a 16-byte constant
base-color table; it allocates no heap storage. This is an
operation budget, not a measured hardware frame-time claim. The environment can
continue to glow while gameplay is paused.

The technical parallax preview retains its existing ring maps, camera and
skyline geometry. Its street chunk IDs are regenerated for the candidate atlas;
its static skyline indices are translated to the candidate's static palette.
Historical parallax assets and all fallback profiles remain unchanged.

## Packing and resource impact

The native study initially produces 2330 unique indexed tiles, exceeding the
2048-cell CN_12BIT 8bpp A0 address space. The scoped packer keeps **all facade
rows 56..159 and every live-color pixel lossless after palette quantization**.
It reuses near-identical tiles only in the low-contrast sky/road, reducing the
atlas to 1664 cells. `CIREF.BIN` records the pre-cell-compression indexed image;
`CIPIX.BIN` records the exact final hardware reconstruction. Neither is loaded
at runtime. The maximum merged-pair RGB555 channel RMS is approximately 0.577
channel steps (about 4.6/255 in RGB888). This is a tile-pair metric, not a claim
that every source pixel is unchanged. The storefront remains exact relative
to CIREF, and sign/interior classes retain their exact indices.

| Resource | Approved bat-fix | Candidate | Delta |
| --- | ---: | ---: | ---: |
| VDP1 texture bytes | 453,344 | 453,344 | 0 |
| VDP1 definitions | 255 | 255 | 0 |
| VDP1 free bytes | 5,144 | 5,144 | 0 |
| New CRAM banks | 0 | 0 | 0 |
| Street cells in A0 | 90,240 | 106,496 | +16,256 |
| Street map in B0 | 16,384 | 16,384 | 0 |
| Street palette payload | 510 | 510 | 0 |
| Preview cells/maps in B0 | 16,384 | 16,384 | 0 |
| Protected SDK A1/B1 reservations | 262,144 | 262,144 | 0 |
| Total VDP2 allocations plus protected banks | 385,152 | 401,408 | +16,256 |

The actual pinned ownership ranges (end exclusive) are:

| Region | Address range | Bytes |
| --- | --- | ---: |
| Street cells, A0 | `0x25E00000..0x25E1A000` | 106,496 |
| Remaining A0 | `0x25E1A000..0x25E20000` | 24,576 |
| SDK-reserved A1 | `0x25E20000..0x25E40000` | 131,072 |
| Street ring/map, B0 | `0x25E40000..0x25E44000` | 16,384 |
| Skyline cells, B0 | `0x25E44000..0x25E46000` | 8,192 |
| Skyline map, B0 | `0x25E46000..0x25E48000` | 8,192 |
| Remaining B0 | `0x25E48000..0x25E60000` | 98,304 |
| SDK-reserved B1 | `0x25E60000..0x25E80000` | 131,072 |

The loader checks the actual returned bank addresses before uploads, and tests
check every range for overlap and bank tails for unwanted writes. The pinned
Jo release allocator does not generally guard bank overflow, so these explicit
ownership/length checks are retained. No change to VDP2 cycle configuration,
character format, layer priorities or reserved SDK regions is required.

A0 still has 24,576 bytes free; B0 has 98,304 bytes free including the existing
preview. No protected bank is written. The palette is replaced within its
existing bank; it is not an extra allocation. The main street payloads total
123,390 disc bytes. The candidate retains original payloads for fallback;
CICHUNK/CISKY replace equal-length preview files only in the staged candidate.

## Verification and review limits

- The entire existing host gameplay/rendering suite passes, including the
  immediate/established running-bat regressions and both players/facings.
- Candidate loader tests check actual A0/B0 bounds, unchanged bank tails, no
  street VDP1 uploads/draws, all camera offsets, initialization failure guards,
  palette-only animation isolation, repeated VBlank values and unsigned wrap.
- `tests/city_gameplay_test.py` extracts the actual registered VBlank callback
  from main.c and runs it during 2048 active co-op simulation updates, including
  input/combat. Neon changes while game state stays byte-identical to a control;
  non-neon palette entries, cells and maps stay untouched. No gallery API is
  involved. This verifies the live gameplay path with host I/O mocks, not video.
- Candidate parallax tests exercise the same ring/cache and restore paths.
- `check-city-neon.py` independently decodes big-endian cells/PNDs, checks all
  321 gameplay cameras, the page seam, animated-index scope, facade integrity,
  translated preview and actual packaged ISO payloads.
- The approved wrapper (candidate off) and candidate wrapper both build locally
  and pass full `make check`. All 520 original public runtime locks and audio
  payloads remain unchanged. The sprite audit still reports 255 / 453,344.
- No new emulator or physical-Saturn capture has been made. Native PNG/GIF
  reconstructions are offline previews, not gameplay footage or proof of
  cycle scheduling/performance. Hardware visual and readability approval is
  still required, especially palette brightness and the subtle letter dip.
- No Actions run, main merge, baseline-tag operation or private-repository edit.

Native/4x review images and a 17-second palette-animation preview are kept in
`/workspace/work/city-neon/`. The local candidate BIN/CUE and identity/checksums
are in `build/`. The Actions artifact is downloaded after manually running the workflow below;
local export remains unavailable in this environment. The original checksum-verified
bat-fix ZIP is retained separately and has not been overwritten.

## Suggested polish after review

First playtest character readability against the richer arcade/club facades at
all camera positions. Tune the letter dip and glow if they compete with action.
A later art pass could sharpen individual native sign glyphs and selected glass
clusters or add a second, very slow warm window accent using remaining static
palette space. Keep future atmosphere on VDP2 and review bank/CRAM ownership
before adding palette classes; do not spend the full VDP1 pool on glow sprites.


## Manual GitHub Actions playtest build

Open Actions -> **Manual Saturn playtest build** -> **Run workflow**. Choose
workflow branch **main**, profile **neon-stage**, and leave `commit_sha` blank
for the exact pinned neon playtest commit, or enter that same full SHA. For the
known-good control, choose **bat-fix** and leave the SHA blank (or enter
`b1abb866aa0f6cfd09794a0ed76e5f054a6ecf6f`). Other SHA/profile combinations fail
before checkout. The dispatch-only workflow uses one standard GitHub-hosted
Ubuntu job, read-only contents permission, pinned checkout/upload actions, and
one downloadable ZIP artifact retained for one day. It installs host dependencies
including genisoimage, builds the selected native wrapper, runs make check/test,
and packages BIN/CUE, BUILD-INFO, licenses and SHA256SUMS. No run was dispatched
as part of setup.

For emulator playtest, keep BIN/CUE together and open the CUE at native 320x240.
Start leaves the gallery; Start again begins play. P2 Start joins Chuck. Move
along the strip to inspect ION ARCADE, then watch at least 18 seconds for the
letter dip; confirm it continues during normal movement/combat. Check both
fighters/enemies against storefronts in both directions, single jabs/combo,
immediate and established-running bat, jump/kick, torch and sound. B in the boot
gallery opens the existing technical parallax preview; check scrolling/reversal
there separately from the normal gameplay camera. Record emulator/core/version
and captures; native host tests are not visual approval or hardware certification.
