"""Normalize the private MIDI export and map its entrance bar to Drop Zone voices."""
import json
from pathlib import Path

import midi
from level1_audio import PPQN, ROUTING

BAR_TICKS = 4 * PPQN
ASSET = Path(__file__).resolve().parents[1] / "assets/music/bruce-ditty.json"
PARTS = ("bass", "guitar", "lead", "drums")


def import_bar(directory):
    tracks = {}
    for part in PARTS:
        _, ppqn, stems = midi.read(directory / f"Ditty {part.title()}.mid")
        assert ppqn == PPQN
        tracks[part] = stems

    bass, overlap, stray, unclosed = midi.notes(midi.merged(tracks["bass"]))
    assert bass and not (overlap or stray or unclosed)
    start = bass[0][0]
    end = start + BAR_TICKS
    result = {}
    for part, stems in tracks.items():
        # The drum export includes other clips carrying the same track name.
        # The shared time range identifies the single matching clip.
        matches = []
        for track in stems:
            notes, overlap, stray, unclosed = midi.notes(track)
            if not any(start <= a < end for a, *_ in notes):
                continue
            assert not (overlap or stray or unclosed)
            assert all(start <= a < b <= end and c == 0 for a, b, c, _, _ in notes)
            assert all(e["status"] in (128, 144, 224, 255) for e in track)
            assert any(e.get("meta") == 47 and e["tick"] >= end for e in track)
            bends = [(e["tick"] - start, e["data"][0] + 128 * e["data"][1])
                     for e in track if e["status"] == 224]
            assert all(0 <= tick < BAR_TICKS for tick, _ in bends)
            matches.append(dict(notes=[(a-start, b-start, key, velocity)
                                       for a, b, _, key, velocity in notes], bends=bends))
        assert len(matches) == 1, (part, len(matches))
        result[part] = matches[0]
    return result


def events(parts, samples):
    """Return native packets and independently checkable note timing."""
    packets, notes = [], []
    tones = {sample["role"]: (sample["program"], sample["root"]) for sample in samples}
    # Rhythm and lead use the existing open guitar. GM drum keys select
    # existing kit roles, which play at their native sample root.
    lanes = {"bass": [4], "guitar": [0, 1], "lead": [6], "drums": [12, 13, 14, 15]}
    pans = {"bass": [64], "guitar": [35, 93], "lead": [48], "drums": [64] * 4}
    programs = {}
    for part in PARTS:
        channels = lanes[part]
        available = dict.fromkeys(channels, 0)
        for channel, pan in zip(channels, pans[part]):
            for cc, value in ((32, 1), (7, 127), (11, 127), (10, pan)):
                packets.append((0, b"", bytes((0xb0 | channel, cc, value))))
            packets.append((0, b"", bytes((0xe0 | channel, 64))))
        for start, stop, key, velocity in parts[part]["notes"]:
            channel = next(c for c in channels if available[c] <= start)
            available[channel] = stop
            if part == "drums":
                program, key = tones[ROUTING[key]]
            else:
                program, _ = tones["bass" if part == "bass" else "open_guitar"]
            if programs.get(channel) != program:
                programs[channel] = program
                packets.append((start, b"", bytes((0xc0 | channel, program))))
            gate = stop - start
            extension, gate = divmod(gate, 512)
            status = channel | (0x40 if gate >= 256 else 0)
            packets.append((start, b"\x88" * extension, bytes((status, key, velocity, gate % 256))))
            notes.append((start, stop, channel, key, velocity))
        last = 64
        for tick, value in parts[part]["bends"]:
            # No bend-range RPN in the MIDI. Scale the default MIDI +/-2
            # semitones to the existing Drop Zone tone's +/-12 semitones.
            native = 64 + round((value - 8192) / (128 * 6))
            if native != last:
                packets.append((tick, b"", bytes((0xe0 | channels[0], native))))
                last = native
    packets.sort(key=lambda row: row[0])
    return packets, notes


if __name__ == "__main__":
    import sys
    # Store only the selected bar's runtime note data. Keep the original export private.
    parts = import_bar(Path(sys.argv[1]))
    ASSET.write_text(json.dumps(parts, separators=(",", ":")) + "\n")
