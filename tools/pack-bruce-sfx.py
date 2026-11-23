#!/usr/bin/env python3
"""Convert the owner's WAV archive into the native one-shot banks."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import wave
import zipfile

from drop_zone_sequence import encode
from level1_audio import build_ton

ROOT = Path(__file__).resolve().parents[1]
# MIDI note 60 at root 90 is 30 semitones below the native 44.1 kHz rate.
RATE = round(44100 / 2**(30/12))
NAMES = ("woopah.wav", "charge.wav", "arghhh.wav", "laugh.wav")


def align(data):
    return data + bytes(-len(data) % 4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    samples, songs, report = [], [], []
    with zipfile.ZipFile(args.archive) as archive:
        members = {Path(name).name.lower(): name for name in archive.namelist()
                   if not name.startswith("__MACOSX/")}
        for i, name in enumerate(NAMES):
            source = archive.read(members[name])
            with wave.open(io.BytesIO(source)) as wav:
                channels, bits, rate, frames = (wav.getnchannels(), wav.getsampwidth()*8,
                                               wav.getframerate(), wav.getnframes())
            pcm = subprocess.check_output(
                ["ffmpeg", "-v", "error", "-i", "pipe:0", "-ac", "1", "-ar", str(RATE),
                 "-f", "s8", "pipe:1"], input=source)
            # build_ton accepts the SDK nominal rate. Set root independently below.
            samples.append(dict(pcm=pcm, frames=len(pcm), rate=44100, root=90,
                                bits=8, loop=False, tl=0))
            duration = (len(pcm)*60 + RATE-1)//RATE
            gate = (len(pcm)*960 + RATE-1)//RATE + 32
            ext, short_gate = divmod(gate, 512)
            score = encode([(0, b"", bytes((0xb0,32,2))),
                            (0, b"", bytes((0xc0,i))),
                            (0, bytes((0x88,))*ext,
                             bytes((64 if short_gate >= 256 else 0,60,110,short_gate%256))),
                            (gate, b"", bytes((0xb0,32,2)))])
            songs.append(align(struct.pack(">HHHHII",480,1,16,8,gate,500000) + score + b"\x83"))
            report.append(dict(name=Path(members[name]).name, source_rate=rate, source_bits=bits,
                               source_channels=channels, source_frames=frames,
                               source_sha256=hashlib.sha256(source).hexdigest(),
                               pcm_rate=RATE, pcm_bits=8, pcm_channels=1, pcm_frames=len(pcm),
                               pcm_sha256=hashlib.sha256(pcm).hexdigest(), minimum_vblanks=duration))
    tone = build_ton(samples)
    offsets = [20 + sum(map(len,songs[:i])) for i in range(len(songs))]
    sequence = align(struct.pack(">H4I",4,*offsets)) + b"".join(songs)
    shared_address = 490128
    free = 524288-shared_address-len(tone)-len(sequence)
    assert len(tone)>18540 and free>=0
    out = ROOT/"assets/bruce-sfx"
    out.mkdir(exist_ok=True)
    (out/"BSFX.TON").write_bytes(tone)
    (out/"BSFX.SEQ").write_bytes(sequence)
    (out/"manifest.json").write_text(json.dumps(
        dict(shared_address=shared_address, tone_bytes=len(tone), sequence_bytes=len(sequence),
             free_bytes=free, samples=report), indent=2)+"\n")
    (ROOT/"src/bruce_sfx_data.h").write_text(
        "#ifndef MF_BRUCE_SFX_DATA_H\n#define MF_BRUCE_SFX_DATA_H\n"
        f"#define MF_BRUCE_TON_BYTES {len(tone)}u\n#define MF_BRUCE_SEQ_BYTES {len(sequence)}u\n"
        "#define MF_BRUCE_SFX_MIN_TICKS {" + ",".join(str(s["minimum_vblanks"]) for s in report) +
        "}\n#endif\n")


if __name__ == "__main__":
    main()
