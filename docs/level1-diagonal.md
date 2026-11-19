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
