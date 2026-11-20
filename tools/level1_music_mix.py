#!/usr/bin/env python3
"""Apply the Level 1 native drum and bass mix and verify its narrow scope."""
from pathlib import Path
import struct
import subprocess

BASE = "5cdafa491cad5f785001147e8af5092a62e90324"
ROOT = Path(__file__).resolve().parents[1]
SCOPE = {
    "Makefile", "assets/cd/CUSTOM.MAP", "assets/cd/STAGE.TON",
    "assets/music/report.json", "assets/public-runtime-lock.json", "src/music_data.h",
    "tools/level1_music_mix.py", "tools/level1-sfx-pcm8-pass1.py",
    "tools/validate_level1_diagonal.py", "tools/validate_level1_guitar.py",
    "docs/level1-music-mix-pass1.md", "docs/level1-music-mix-midpoint.md", "docs/audio-previews/level1-music-mix-pass1.wav",
}
DRUM_TL = (2, 4, 14, 14, 18, 16, 18, 7, 7, 7)
SHARED_CURVE = bytes((25, 16, 54, 9, 49, 102, 19, 93, 122, 43))
BASS_CURVE = bytes((25, 16, 61, 9, 49, 108, 19, 93, 124, 43))

DRUM_PCM_GAIN = 10 ** (-0.375 / 20)


def apply(tone, voice):
    velocity_offset = int.from_bytes(tone[2:4], "big")
    peg_offset = int.from_bytes(tone[4:6], "big")
    _, pcm_offset = voice(tone, 0)
    assert bytes(tone[velocity_offset:peg_offset]) == SHARED_CURVE
    result = bytearray(tone[:peg_offset] + BASS_CURVE + tone[peg_offset:pcm_offset]
                       + bytes(2) + tone[pcm_offset:])
    for offset in range(4, 34, 2):  # PEG, PLFO, and thirteen voice offsets
        value = int.from_bytes(tone[offset:offset + 2], "big")
        result[offset:offset + 2] = (value + len(BASS_CURVE)).to_bytes(2, "big")
    for program in range(13):
        layer, address = voice(result, program)
        relocated = address + 12
        result[layer + 3] = (result[layer + 3] & 0xf0) | (relocated >> 16)
        result[layer + 4:layer + 6] = (relocated & 0xffff).to_bytes(2, "big")
        if program == 2:
            assert result[layer + 29] == result[layer + 15] == 0
            result[layer + 29] = 1  # Select the new velocity curve for bass only.
        if program >= 3:
            assert result[layer + 15] == DRUM_TL[program - 3]
            # The driver skips a half-step in TL. Apply the approved half-step
            # to the existing sample instead, retaining its format and tone.
            fmt = ">b" if result[layer + 3] & 0x10 else ">h"
            width = struct.calcsize(fmt)
            frames = int.from_bytes(result[layer + 8:layer + 10], "big")
            end = relocated + frames * width
            next_address = voice(tone, program + 1)[1] + 12 if program < 12 else len(result)
            assert end + 4 <= next_address and result[end:end + 4] == bytes(4)
            for offset in range(relocated, end, width):
                value, = struct.unpack_from(fmt, result, offset)
                struct.pack_into(fmt, result, offset, round(value * DRUM_PCM_GAIN))
    first_drum = voice(tone, 3)[1]
    assert result[pcm_offset + 12:first_drum + 12] == tone[pcm_offset:first_drum]
    return result


def validate_scope(git):
    if subprocess.run(["git", "cat-file", "-e", BASE + "^{commit}"], cwd=ROOT,
                      capture_output=True).returncode:
        git("fetch", "--no-tags", "--depth=1", "origin", BASE)
    changed = set(git("diff", "--name-only", BASE, "--").decode().splitlines())
    assert changed <= SCOPE, changed - SCOPE
