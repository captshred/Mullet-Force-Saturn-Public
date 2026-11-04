# Level 2 E102: GFS directory-table overflow

The repair starts from `9d95685a44abec2aae4b11a8eefe5e717cc95fe8`,
which built successfully in manual run
[41916920197](https://github.com/captshred/Mullet-Force-Saturn-Public/actions/runs/41916920197).
The player reported completing Level 1 and reaching the E102 error after Stage
Clear. No new Actions run has been launched for this repair.

## Cause and evidence

The pinned Jo Engine revision `556d081146211b6a1cfa6591d70f9487d406758b`
defines `JO_FS_MAX_FILES = 256` in `jo_engine/jo/conf.h`. Its `fs.c` allocates
`__jo_fs_dirname[JO_FS_MAX_FILES]`, passes that capacity to GFS_Init and
GFS_LoadDir, and resolves both directory changes and file reads through
GFS_NameToId. An asset's presence in an ISO does not establish that this bounded
current-directory table can resolve it. The old disc validator only extracted
assets with isoinfo, which does not have this runtime limit.

Running the actual complete profile's staging code up to the compiler invocation
produced 263 named root entries, before the compiler adds `0.BIN`: 264 total.
In ISO alphabetical name order, the background files' one-based named positions
were WCELL.BIN=258, WMAP.BIN=262, WPAL.BIN=263. The six texture names occupied
positions 256, 257, 259, 260, 261 and 264. ISO special records can consume further
table entries. Thus the first background read can fail NameToId even though all
nine files are present and their bytes match the manifest. Increasing a timeout,
ignoring E102, or skipping an asset cannot solve this.

These counts come from reconstructed build staging, not a claim to have dumped
or run the downloaded Saturn image locally. The host regression reproduces the
bounded root lookup and fails W-file lookup until the current directory changes.

## Repair

- Stage all six sprite textures and all three background files under `/ALEVEL2`.
  None of their bytes, names, dimensions, formats, or budgets change.
- Remove only the nine obsolete root copies and the dedicated directory when
  reusing a staging tree. The helper is idempotent and also cleans these new
  assets when switching back to a non-wingsuit profile. Approved Level 1 files
  are neither moved nor changed.
- Resolve the early ALEVEL2 entry, enter it once with the pinned `jo_fs_cd()` API,
  load the entire bank, and restore `JO_PARENT_DIR` on every return from the
  resource loader. The pinned API returns void; missing child lookups also
  diagnose a failed directory entry. No Level 1 update/draw callback is resumed.
- The staged root now has 256 named entries including `0.BIN`; ALEVEL2 has named
  position 41, well inside the table even with the two ISO special records.
  Its child directory has just nine assets (11 records including dot entries).
  The actual Level 1 boot texture loader audit still reports 255 definitions /
  452,800 bytes; all 145 root entries it uses remain within the 256-record limit,
  conservatively including two special records. The last legacy TU entries are
  not used by the required HQ-torch profile.
- Keep the existing fatal load behavior. E102/E103 now show the specific asset,
  MISSING, LENGTH, READ/ALLOC, REGISTER or unexpected sprite-ID cause, plus
  expected/actual values. Directory, VDP1 drain/reset and VDP2 schedule failures
  also identify their subsystem. Jo's combined file reader cannot distinguish
  a read failure from an allocation failure, so the message says READ/ALLOC.
  No failed upload is treated as success.

The new validator reads primary ISO9660 directory records in actual on-disc
order. It requires ALEVEL2 to be reachable within the pinned 256-record table,
requires exactly the nine files in its child directory, compares every payload
byte with committed assets, rejects stale root copies, and checks record bounds.
It runs through the existing `validate-wingsuit.py --disc` / `make check` path.
This supplements all original payload/preservation checks.

## Validation

The host runtime tests load all nine assets through the changed current
directory with root W lookups unavailable. They check parent restoration after
success and failure, each asset missing, each asset one byte short with exact
expected/actual diagnostics, read/allocation failure, sprite registration
failure, missing directory, and unchanged VDP1/VDP2/SCSP handoff boundaries.

ISO fixtures use 303 root records and exercise correct early-directory access,
late-directory rejection, stale root files, a missing asset, corrupt payloads,
and exact nine-file contents. Staging tests cover repeated staging and disabling
the profile without changing a Level 1 sentinel. These are structural ISO and
host tests, not emulator execution.

The complete host `make test` passes. Existing stage-clear, approved artwork,
SFX2/audio, source-preservation checks and the boot texture audit pass. All 623
existing Level 1 asset blobs and all nine shooter payload blobs are unchanged.
Only `tools/build-native.sh`'s exact after-hashes change in the existing scoped
Level 2 source lock; its before-hashes and every other preservation entry remain
unchanged. No engine/compiler pin, workflow, Level 1 gameplay or art is altered.

A repaired native BIN/CUE and a new Saturn playthrough have not been produced in
this environment. To build after explicit approval to run Actions, use the
existing manual workflow, `stage-default`, and this feature branch's new exact
commit as source_ref. Alternatively run the documented native build locally,
then `make check` and `make test`. Retest the real 40-KO transition and both
controllers before calling the runtime repair hardware-validated.
