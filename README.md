# Mullet Force — Sega Saturn

Public development version of the two-player beat-em-up. This snapshot starts
from the jab-jab-cross build in run 41215154675, checked out as
`d3e4b0db9235114ff7ea73adf1b9b228deb3c2aa`. It excludes the later cross refinement.
The original private repository retains all development history and authoring assets.

## Download and play

Open Actions, select the latest successful **Playable Saturn build**, and download
`mullet-force-playable-<commit>`. Downloads expire after one day. Keep BIN/CUE
together and open the CUE. The track is MODE1/2048.

P1 Start starts/pauses. P2 Start joins as Chuck. D-pad moves; A jabs (three
successive presses chain jab-jab-cross), B jumps, jump+A kicks. Double-forward
dash uses preset B; A while dashing swings the bat. Hold A for one second for
the blowtorch. The existing boot gallery remains; the expanded Animation Test Lab
is a future change and is not implemented by this migration.

## Build

Use x86-64 Linux. `bash tools/bootstrap.sh` installs host prerequisites and the
pinned Jo Engine SDK. Then run:

```sh
bash tools/build-punch-combo.sh --native
make check
make test
```

With Docker available, `bash tools/build-punch-combo.sh` uses the unchanged
pinned container. Plain make retains the historical base profile; Actions selects
the complete jab-jab-cross profile explicitly. Do not change the compiler pin
or Docker base as part of unrelated development.

## Public/private boundary

This repository contains game-ready textures, compiled audio, code, runtime
manifests, and regression tests. Original high-resolution art, editable references,
PNG/GIF review exports, source MIDI and WAV files remain private. Public game
assets can be extracted from the build; private masters are not required to build.
Art regeneration scripts may reference private authoring files and are not part
of the public build path. Historical authoring documentation describes those
private inputs; it does not mean they are present here.

`make check` verifies exact runtime payload digests, disc structure and VDP2
layout. `make test` runs the existing C gameplay/rendering regressions. Private
source-art/MIDI/WAV fidelity validators stay in the private authoring repository.
Structural and native tests do not establish real-Saturn compatibility.

Original game artwork, audio and branding remain all rights reserved. Public
access does not grant a separate license to reuse those assets. Retain applicable
third-party notices in docs/JO-ENGINE-LICENSE.txt and third_party/mid2seq/LICENSE.
