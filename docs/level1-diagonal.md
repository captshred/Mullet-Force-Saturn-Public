# Level 1 Phase 3B-1

The outdoor street continues past the Phase 3A hotel, intersection and RECORDS frontage. The 320-pixel extension adds a down-right bend with wet pavement, two curb lines and three streetfronts. It stops at the temporary Level 1 test endpoint. ION ARCADE remains in the opening section. MEGA ARCADE is a future destination.

| Setting | Value |
|---|---|
| Background | 2,240 × 304 pixels |
| Camera | X 0–1,920, Y 0–64 |
| Player X | 26–2,214 |
| Walkable depth | 168–229 pixels relative to the road |
| Road drop | 1 pixel per 5 pixels of X after X 1,920 |
| Camera step | At most 2 X pixels and 1 Y pixel per simulation tick |
| Checkpoint floors | 0, 320, 640, 960, 1,280 |

The existing D-pad and movement rates operate in the same local lane coordinates. Walking right follows the grade, while Up and Down traverse the road between the curbs. The two-player tether still uses horizontal distance. Camera Y follows the grade at the right edge of the viewport, keeping the leading player's feet clear of the lower edge. VDP1 projects every actor, shadow and hit effect against the local road, and sorts by the projected foot position. Combat uses the existing lane depths. The independent skyline retains quarter-speed horizontal parallax.

The original 1,920 × 240 indexed pixels and the street palette are preserved byte for byte. The VDP2 ring streams the rows exposed by the bend and retains the preceding scan-out while filling new cells. The A0 tile cache stays at 1,664 tiles (106,496 bytes), with a 16,384-byte ring map and 434,176 bytes total VDP2 reserved. VDP1 textures, CRAM and SCSP have no new allocations. The background owns one contiguous Jo heap allocation for the packed graphics, map, offsets and decode cache. It is released at the existing Level 2 handoff.

## Build

Run `bash tools/build-source-complete.sh`, `make check` and `make test` with the pinned host setup. On GitHub Actions open **Manual Saturn playtest build**, select **Run workflow**, choose `feature/level1-phase3b-diagonal` in the branch picker, set `profile` to `level1-human-death-combat-sfx` (the workflow's source-complete recipe), and use the candidate's full SHA for `source_ref`. Download the artifact and open the CUE with its matching BIN alongside it.

## Phase 3B-2 · The Downhill Bomb

This continuation starts at tested Phase 3B-1 commit
`b95759d321b9a77a401620e1c552ed28f8c24a0a`. The road keeps its 1:5 grade
(11.31°) and the same curb-to-curb playable width. The parking lot is
placeholder scenery on the far side of the curb, with painted spaces,
concrete retaining walls and fencing. Its pavement and walls use the
existing street palette and VDP2 tile cache.

| Measurement | Phase 3B-1 | Phase 3B-2 |
|---|---:|---:|
| Hill start | X 1,920 | X 1,920 |
| Hill end | X 2,240 | X 2,560 |
| Horizontal hill length | 320 px | 640 px |
| Total road drop | 64 px | 128 px |
| Length measured along the grade | 326.3 px | 652.7 px |
| World | 2,240 × 304 px | 2,560 × 368 px |
| Camera X / Y limits | 0–1,920 / 0–64 | 0–2,240 / 0–128 |
| Player X limits | 26–2,214 | 26–2,534 |

All 2,240 × 304 approved source pixels are preserved. The packed tile
dictionary is 275,496 bytes on disc and the complete background allocation
is 377,435 bytes of the existing 393,216-byte Jo heap. The 128-block decode
cache and the 1,664-tile VDP2 cache retain their capacities. Camera tracking,
checkpoint rules and player and enemy lane coordinates continue through
the existing world-boundary code.

Build with the source-complete profile above. Select
`feature/level1-phase3b-downhill-extension` in the Actions branch picker
and use its exact commit SHA for `source_ref`.

## Phase 3B-3 · Visual polish

The approved geometry is retained from `382b226b476b305c9ebab8e6d2ddbe763603d41b`.
The uphill connection and the entire playable roadway retain their original
indexed pixels. Above the road, storefront rooflines, windows and signage stay level on
stepped foundations. Three open-sided parking decks at each of two
elevations sit behind a sloped concrete forecourt with stalls, drainage,
a ramp and streetlights. All art is flattened into the street layer using the
existing palette. The skyline remains an independent parallax layer.

The build uses the same source-complete profile. Select
`art/level1-downhill-visual-polish` in the Actions branch picker and use
the candidate's exact commit SHA for `source_ref`.
