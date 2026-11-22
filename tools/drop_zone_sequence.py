"""Build the two native Drop Zone entrances from the committed Bruce score."""
import json
from pathlib import Path
import re
import struct
import subprocess

import bruce_ditty
import seq

ROOT = Path(__file__).resolve().parents[1]
BASE = "719ce3f8f260076cd0c0257bae3ea45779557473"
SCOPE = {
    "assets/cd/STAGE.SEQ", "assets/cd/CUSTOM.MAP", "assets/music/report.json",
    "assets/public-runtime-lock.json", "src/music_data.h",
    "tools/drop_zone_sequence.py", "tests/bruce_music_test.c",
    "tools/bruce_ditty.py", "assets/music/bruce-ditty.json",
    "downloads/bruce-music-transition/mullet-force-bruce-drop-zone-34735c3.zip",
    "downloads/bruce-entrance-ditty/mullet-force-bruce-entrance-ditty.zip",
}
OPENING = 1920
BRUCE_BAR = 151680  # GPIF master bar 80, 3/4, at 480 PPQN.
NEXT_BAR = 153120
DELTA = {0x8c: 256, 0x8d: 512, 0x8e: 2048, 0x8f: 4096}


def packets(data):
    """Yield absolute tick, gate extension bytes, and event without its delta."""
    tick = 0
    while data:
        gate = bytearray()
        delta = 0
        while data[0] in range(0x88, 0x90):
            if data[0] in DELTA:
                delta += DELTA[data[0]]
            else:
                gate.append(data[0])
            data = data[1:]
        opcode = data[0]
        if opcode == 0x83:
            return
        size = 5 if opcode < 0x80 else 2 if opcode == 0x82 else 4 if opcode & 0xf0 == 0xb0 else 3
        tick += delta + data[size - 1]
        if opcode < 0x80 and opcode & 0x20:
            tick += 256
            opcode &= ~0x20
        yield tick, bytes(gate), bytes((opcode,)) + data[1:size - 1]
        data = data[size:]


def encode(events):
    result = bytearray()
    previous = 0
    for tick, gate, event in events:
        delta = tick - previous
        assert delta >= 0
        previous = tick
        for code, amount in reversed(DELTA.items()):
            count, delta = divmod(delta, amount)
            result.extend(bytes((code,)) * count)
        result.extend(gate + event + bytes((delta,)))
    return bytes(result)


def build(original):
    original_song, = struct.unpack_from(">I", original, 2)
    ppqn, tempo_count, data_offset, loop_offset, end, tempo = struct.unpack_from(
        ">HHHHII", original, original_song)
    assert (ppqn, tempo_count, loop_offset, end, tempo) == (480, 1, 8, 279840, 365854)
    events = list(packets(original[original_song + data_offset:]))
    opening_notes = [event for tick, _, event in events if tick < OPENING and event[0] < 0x80]
    assert [(event[0] & 15, event[1]) for event in opening_notes] == [
        (0, 38), (1, 45), (2, 50), (3, 57), (8, 26)]
    old = seq.decode(original)
    assert all(start == 0 and stop == OPENING for start, stop, *_ in old["notes"][:5])
    assert old["notes"][5][0] == OPENING
    assert [t for t, _, c, note, _ in old["notes"]
            if BRUCE_BAR <= t < NEXT_BAR and c in (12, 13) and note == 38] == [
                151694, 151924, 152190]

    street = encode((max(0, tick - OPENING), gate, event)
                    for tick, gate, event in events if tick >= OPENING or event[0] >= 0x80)
    # Restore controller, program and bend state before the first retained
    # event. Gated notes from the previous bar are intentionally absent.
    state = {}
    for tick, _, event in events:
        if tick >= BRUCE_BAR:
            break
        if event[0] >= 0xb0:
            key = event[:2] if event[0] & 0xf0 == 0xb0 else event[:1]
            state[key] = event
    assert all(key[0] & 0xf0 in (0xb0, 0xc0, 0xe0) for key in state)
    parts = json.loads(bruce_ditty.ASSET.read_text())
    samples = json.loads((ROOT / "assets/music/level1-custom-report.json").read_text())["samples"]
    prelude, ditty_notes = bruce_ditty.events(parts, samples)
    ditty_ticks = bruce_ditty.BAR_TICKS
    # Release the entrance lanes and restore the original score state at the
    # barline. The first boss notes and the full fill follow on this same clock.
    prelude += [(ditty_ticks, b"", bytes((0xb0 | c, 123, 0))) for c in range(16)]
    prelude += [(ditty_ticks, b"", event) for _, event in sorted(state.items())]
    # Match the street loop's complete terminal state cleanup before entering
    # its shared loop marker and bank/program initialization.
    prelude += [(ditty_ticks + tick - BRUCE_BAR, gate, event) for tick, gate, event in events
                if tick >= BRUCE_BAR and event != b"\x82"]
    prefix = encode(prelude)

    street_ticks, boss_ticks = end - OPENING, ditty_ticks + end - BRUCE_BAR
    street_header, boss_header = 12, 28
    loop_data = boss_header + 24 + len(prefix)
    bank = struct.pack(">HII", 2, street_header, boss_header) + bytes(2)
    bank += struct.pack(">HHHHII", ppqn, 1, loop_data - street_header, 8, street_ticks, tempo)
    bank += struct.pack(">HHHHIIII", ppqn, 2, 24, 16, boss_ticks, tempo, street_ticks, tempo)
    bank += prefix + street + b"\x83"
    bank += bytes(-len(bank) % 4)

    normal = seq.decode(bank)
    boss = seq.decode(bank, 1)
    assert normal["notes"] == [(a - OPENING, b - OPENING, *note)
                               for a, b, *note in old["notes"][5:]]
    for key in ("controls", "programs", "bends"):
        assert normal[key] == [(max(0, t - OPENING), *event) for t, *event in old[key]]
    assert normal["loops"] == [0, street_ticks] and normal["end"] == street_ticks
    assert sorted(boss["notes"][:len(ditty_notes)]) == sorted(ditty_notes)
    assert boss["notes"][len(ditty_notes):] == [(ditty_ticks + a - BRUCE_BAR, ditty_ticks + b - BRUCE_BAR, *note)
                             for a, b, *note in old["notes"] if a >= BRUCE_BAR] + [
                                 (a + boss_ticks, b + boss_ticks, *note) for a, b, *note in normal["notes"]]
    assert boss["loops"] == [boss_ticks, boss_ticks + street_ticks]
    assert boss["tempo_loop_offset"] == 16
    assert boss["tempos"] == [(boss_ticks, tempo), (street_ticks, tempo)]
    return bank


def baseline(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


def relocate(bank, index, header, report):
    index = bytearray(index)
    stage = len(index) - 24
    assert index[stage] == 0x11 and index[stage + 8] == 1
    seq_addr = int.from_bytes(index[stage + 1:stage + 4], "big")
    tone_bytes = int.from_bytes(index[stage + 13:stage + 16], "big")
    tone_addr = seq_addr + len(bank)
    # Preserve the contiguous car tone bank used by the Bruce playtest profile.
    high_water = tone_addr + tone_bytes
    car_end = high_water + len(baseline("assets/cd/CARPASS.TON"))
    assert car_end <= 0x80000
    index[stage + 9:stage + 12] = tone_addr.to_bytes(3, "big")
    index[stage + 5:stage + 8] = len(bank).to_bytes(3, "big")
    for name, value in (("MF_STAGE_SEQ_BYTES", len(bank)), ("MF_STAGE_TON_ADDR", tone_addr)):
        header, count = re.subn(rb"(?m)^(#define " + name.encode() + rb") \d+$",
                                lambda m: m[1] + f" {value}".encode(), header)
        assert count == 1
    regions = report["sound_ram_regions"]
    regions[-2].update(size=len(bank), end=tone_addr)
    regions[-1].update(start=tone_addr, end=high_water)
    report.update(sound_ram_high_water=high_water, sound_ram_unallocated=0x80000-high_water)
    report["drop_zone_bruce_entry"] = dict(
        opening_ticks_removed=OPENING, original_measure=80, original_tick=BRUCE_BAR,
        ditty_ticks=bruce_ditty.BAR_TICKS, first_full_loop_ticks=277920, car_profile_free_bytes=0x80000-car_end,
    )
    return bytes(index), header


if __name__ == "__main__":
    bank = build(baseline("assets/cd/STAGE.SEQ"))
    print(len(bank), "sequence bytes")
