# Level 1 audio regression and repair

## Boundary

The merge base of the two supplied commits is the full MEGA ARCADE Phase 4A.2 commit `bc05611bb5b174e8ca74a1d110204c703f158592`. The two commits on the ancestry path are asset import `650a30d` and runtime integration `ec4de33791226e920f189043b4d7053846c1aa0a`. The import adds the source assets, while the latter enables Bruce staging and adds one new ISO root directory. The latter is the introducing source commit. Neither commit changes music source, audio payloads, sound RAM constants, or the order of the original `mf_music_init` call.

The staging hook entered at `ec4de33:tools/build-native.sh:426` and put the bank at the root through `ec4de33:tools/stage-bruce-bank.py`. The runtime flags in `tools/build-source-complete.sh` enable it in stage-default. The ISO file order puts BRUCE at index 43. Jo Engine's pinned `jo/conf.h` defines `JO_FS_MAX_FILES` as 256, and its `fs.c` passes that size to GFS. With zero-based record indexing including . and .., STAGE.TON goes from record 255 to 256. The file is present in the ISO, but absent from the runtime root lookup.

`src/music.c:62–72` fails the read before DMA. At line 153 that failed upload contributes to the aggregate result, assigned to `ready` at line 165. At line 214 the ready gate prevents normal music and SFX dispatch. The 68K was running in every comparison and the other audio payloads reached their existing SCSP addresses. STAGE.TON alone was zero at its destination on both silent builds.

Level 2 resolves ALEVEL2 at root index 42, opens its own small directory table in `src/wingsuit_runtime.c:183–198`, and initializes its own map and track resources. Its directory path and payloads are unchanged.

## Controlled reproduction

The first broken image was remastered with the same executable and all content retained. The only lookup-layout change was moving the BRUCE directory under RICKY. This diagnostic image was used up to the Level 1 playback window. The shipping repair makes the equivalent layout change and updates Bruce's loader to traverse both directories and restore the root.

| Image | STAGE.TON root index | Primary SCSP tone bank at 330696 | Nonzero PCM values |
| --- | ---: | --- | ---: |
| Approved pre-Bruce disc | 255 | Exact | 1,287,338 |
| First Bruce disc | 256 | Empty | 0 |
| Approved Bruce combat disc | 256 | Empty | 0 |
| First Bruce disc, directory-only remaster | 255 | Exact | 1,287,338 |
| Repaired Bruce combat disc | 255 | Exact | 1,287,338 |

Each recording uses 1,950 Yabause HLE video frames and the same controller input, including a jab. The working, directory-only remaster, and repaired PCM streams are byte-for-byte equal. Broken streams consist entirely of zero sample values. At frame 1400 the approved and directory-only recordings had seven keyed SCSP voices, while both broken discs had zero. These are mixed emulator samples, not microphone recordings. The accompanying audio ZIP contains matching excerpts.

## Repair and memory

The fix nests the existing 19 TGA files at RICKY/BRUCE. It keeps the original sound files and their existing addresses. The disc validator now checks the actual first 256 ISO root records for the Level 1 audio resources. Neither the pinned SDK nor the sound driver was changed.

| SCSP payload | Start | Bytes |
| --- | ---: | ---: |
| FX.SEQ | 148864 | 368 |
| FX.TON | 149232 | 141336 |
| STAGE.SEQ | 290568 | 40128 |
| STAGE.TON | 330696 | 147304 |
| CARPASS.TON | 478000 | 25764 |

The last payload ends at 503764 in the 524288-byte SCSP RAM. The remaining 20524 bytes and the standard driver/work/transfer reservations are unchanged. SCSP is distinct from VDP1 texture VRAM. Bruce still uses the 162240-byte suffix. The combat fixtures measured 401600 resident VDP1 texture bytes with the 49152-byte hero reserve preserved, and reported zero asset and bank errors. The repair changes CD directory lookup, with no work-RAM table expansion or VDP1 allocation change.

## Playtest scope

The downloadable disc uses the normal gameplay path. The scripted Bruce fixtures exercise the real renderer and combat code using controlled positions and attack timing. They covered the entrance, charge, lunge, bat interruptions, 60 HP spawn, and defeat. Emulator audio output was checked through the encounter and after the Level 2 transition. Physical Saturn audio approval remains open.
