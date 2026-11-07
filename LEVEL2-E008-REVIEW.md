# Level 2 loading review

Level 2 native sound requests now explicitly notify the driver through public communication flag 0x04e0 bit 7. The two map0 requests are submitted asynchronously with separate consumption acknowledgments. Cursor advancement at 0x041a, an empty command queue, map validation and the original 120-VBlank watchdog remain required. No forced readiness or arbitrary delay.

The previous cursor correction remains present. A gated native-driver test reproduces pending requests without notification and successful consumption after notification. The old unconditional-consumer mock concealed this transport dependency. The synchronous SDK map call also waits internally; replacing that call with equivalent asynchronous requests keeps the watchdog active.

Validation: private native compilation, make check, make test, readiness mutation tests and notification mutation tests passed. Repeated mixed explosions/shots/flames passed 600 frames without voice ownership losses. Both map acknowledgments are required; an unconsumed second request times out.

Actual BIN/CUE testing: native libretro/Yabause 0.9.15, HLE BIOS, software video, reached Level 2 gameplay. Twenty seconds of firing/flame input produced nonzero PCM, peak 6751/32768 and zero clipped samples. A controlled diagnostic retaining the driver's original notification gate stalls the old candidate at map submission and permits the fixed candidate to load. The exact failing WebRetro session has not been reproduced without diagnostic control. Numerical output is not listening or hardware approval.

Preserved: Level 1 source/effects, Level 2 gameplay, music notes/slides, all audio/art payloads, the 24x24 explosion visual upgrade and explosion-only gain reduction to 59.566% amplitude (-4.5 dB). No music/weapon/other SFX gain changes.

Memory delta: zero additional sprite definitions, VRAM/CRAM allocation, sound RAM, PCM or voices. Level 2 remains 28 sprite definitions, 33792 texture bytes, 81 maximum VDP1 commands, 32 CRAM bytes; SCSP high-water 447588 bytes, 76700 free, conservative voice budget 28/32.

Compilation and full regressions ran privately. Actions verifies the runtime BIN/CUE, package checksums and ISO structure, then publishes one playable artifact. Authoring assets, private source identifiers, source inventories and private history are excluded from this report and package metadata. The playable game image is unchanged by metadata sanitization.

Load mullet-force.cue. User WebRetro visual/audible approval is pending; nothing is merged into the approved baseline.
