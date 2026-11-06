# Level 2 native music playtest

[Download the complete BIN/CUE ZIP](downloads/mullet-force-level2-native-music-7a1de3b.zip?raw=true).

Extract all files together and open `mullet-force.cue` (MODE1/2048).

Source build: `7a1de3bda065a3397de764ae5469793405f2aef4`, branch `feature/level2-native-music` in the private authoring workspace, based on approved `506d5f1762d1f70bbf8975b36c616c0fa5f54472`.

This is an artifact delivery branch: its repository source stays at the approved baseline. The ZIP contains the new native music build plus memory/accuracy reports and validation logs. The GP source, MIDI reference, articulation JSON and authoring source commit stay private.

Native build, `make check` and `make test` passed. Audible Saturn emulator/hardware playback remains unverified.

Three musical parts only: two rhythm guitars and bass. 141 measures, 206 BPM, 164.271768 seconds; 4,403 performed notes. Existing PCM instruments and SFX are preserved. Music uses 69,652-byte SEQ and 70,676-byte TON; 76,700 sound-RAM bytes remain free. Conservative combined voice bound: 28/32.

ZIP SHA-256: `3396e1a534c72274f87eac463f2a19281cfffee3ad437c7f18a9759b8aa97a0c`.
