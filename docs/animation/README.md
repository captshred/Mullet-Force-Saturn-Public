# Current review: character animation polish

This build retains ff24c5e and every functioning gameplay sprite bank, while
adding a selectable polished set. See **polish.md** for the art changes, memory
accounting, tests and limitations. Earlier prototype notes are preserved in
prototype-readme.md; their memory figures describe the old checkpoint.

Open **polished/preview.html** in the downloaded artifact for a side-by-side
viewer. The polished folder contains native/2x walk and idle comparisons, four
breathing poses, six refined walk poses per fighter, guard handoffs and GIFs.
The original prototype files and master references remain alongside them.

For Saturn: cold-boot the matching BIN/CUE. Down opens the review. A+B toggles
polished/original, Up selects idle/walk, B pauses, Left/Right steps, A mirrors,
Down returns to gallery, Start returns to original title/game, C diagnostics.
The normal game always renders its original animation banks.

Current VDP1 textures: **430,496 / 458,488 bytes; 27,992 free**. Exact piece
sharing avoids 45,344 bytes of additional allocation. No new palette or VDP2
memory is required. No live animation cache or full-moveset replacement is added.


Validation: all seven native build configurations, existing tests, preview
sanitizers and local Yabause rendering pass. polish-validation.json records
7,171,200 independently compared pixels and measured idle holds. The SH-2
resident image grows 2,960 bytes over ff24c5e when parallax is enabled. Device
and new-browser visual testing remain outstanding; artistic acceptance is yours.
