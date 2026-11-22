"""Pack and audit the Bruce baseline's vehicle audio replacement."""
from hashlib import sha256
import importlib
import json
from pathlib import Path
import struct
import subprocess

from drop_zone_sequence import encode, packets

ROOT = Path(__file__).resolve().parents[1]
BASE = "34b82980e1bb8bef967c29a1280d427d4f7ad2f0"
FX_TONE = "assets/cd/FX.TON"
FX_SCORE = "assets/cd/FX.SEQ"
CAR_TONE = "assets/cd/CARPASS.TON"
AUDIO_DELTA = {FX_SCORE, FX_TONE, CAR_TONE}
SCOPE = AUDIO_DELTA | {
    "tools/level1_housekeeping.py", "tests/ugh_transport_test.c",
    "downloads/level1-audio-housekeeping/mullet-force-level1-audio-housekeeping.zip",
}
HONK_RATE = 22050
CAR_RATE = 11025
HONK_FRAMES = 9474
CAR_FRAMES = 18441
CAR_LOOP_START = 128


def old(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


def aligned(data):
    return data + bytes(-len(data) % 4)


def sample(data, program):
    layer = struct.unpack_from(">H", data, 8 + 2 * program)[0] + 4
    start = ((data[layer + 3] & 15) << 16) | struct.unpack_from(">H", data, layer + 4)[0]
    return layer, start


def import_pcm(source, rate, loop_start=0):
    # Private authoring only. Public builds consume the checked runtime banks.
    import wave
    import numpy as np
    from scipy.signal import resample_poly

    with wave.open(str(source), "rb") as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (2, 1, 44100)
        stereo = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.uint8)
    mono = stereo.astype(float).reshape(-1, 2).mean(axis=1) - 128
    mono -= mono.mean()
    pcm = resample_poly(mono, 1, 44100 // rate)
    if loop_start:
        weight = np.linspace(0, 1, loop_start)
        pcm[-loop_start:] = pcm[-loop_start:] * (1 - weight) + pcm[:loop_start] * weight
    return np.clip(np.rint(pcm), -128, 127).astype("i1").tobytes()


def outputs(honk, drive, index, header, report):
    assert len(honk) == HONK_FRAMES and len(drive) == CAR_FRAMES
    original = old(FX_TONE)
    layer, start = sample(original, 7)
    next_layer, end = sample(original, 8)
    assert end-start == 16736 and original[layer+3] & 0xf0 == 0x10
    packed_honk = aligned(honk)
    tone = bytearray(original[:start] + packed_honk + original[end:])
    struct.pack_into(">H", tone, layer+8, len(honk))
    relocated = start + len(packed_honk)
    tone[next_layer+3] = (original[next_layer+3] & 0xf0) | (relocated >> 16)
    struct.pack_into(">H", tone, next_layer+4, relocated & 0xffff)
    assert tone[relocated:] == original[end:]

    # Former bat slot now holds the warning on its existing world SFX port.
    sequence = bytearray(old(FX_SCORE))
    song, following = struct.unpack_from(">II", sequence, 2 + 7*4)
    offset = struct.unpack_from(">H", sequence, song+4)[0]
    gate = (HONK_FRAMES * 960 + HONK_RATE - 1) // HONK_RATE
    events = list(packets(sequence[song+offset:following]))
    assert [e for _, _, e in events] == [b"\xb0\x20\0", b"\xc0\x07", b"\x00\x3c\x7f\xe9", b"\xb0\x20\0"]
    events[2] = (0, b"", bytes((0x40, 60, 127, gate-256)))
    events[3] = (gate, b"", events[3][2])
    payload = aligned(sequence[song:song+offset] + encode(events) + b"\x83")
    assert len(payload) == following-song
    sequence[song:following] = payload
    struct.pack_into(">I", sequence, song+8, gate)

    car_header = bytearray(old(CAR_TONE)[:96])
    car_layer, car_start = sample(car_header, 3)
    assert car_start == len(car_header)
    car_header[car_layer+3] |= 0x10
    car_header[car_layer+25] = 61 + 24  # 11.025 kHz at the unchanged MIDI note 61.
    struct.pack_into(">HH", car_header, car_layer+6, CAR_LOOP_START, len(drive))
    car = aligned(car_header + drive + drive[CAR_LOOP_START:CAR_LOOP_START+4])

    index = bytearray(index)
    rewrites = importlib.import_module("level1-sfx-pcm8-pass1")
    sizes = (len(tone), *(region["size"] for region in report["sound_ram_regions"][-2:]))
    address = int.from_bytes(index[25:28], "big")
    for offset, region, size in zip((24, 32, 40), report["sound_ram_regions"][-3:], sizes):
        index[offset+1:offset+4] = address.to_bytes(3, "big")
        index[offset+5:offset+8] = size.to_bytes(3, "big")
        region.update(start=address, size=size, end=address+size)
        address += size
    free = 0x80000 - address - len(car)
    assert free >= 0
    for name, value in {
        "MF_FX_TON_BYTES": len(tone),
        "MF_STAGE_SEQ_ADDR": report["sound_ram_regions"][-2]["start"],
        "MF_STAGE_TON_ADDR": address - sizes[-1],
    }.items():
        header = rewrites.replace_define(header, name, value)
    header = header.replace(b"#define MF_CUSTOM_MAP_BYTES", f"#define MF_CAR_TON_BYTES {len(car)}\n#define MF_CUSTOM_MAP_BYTES".encode())
    ticks = (HONK_FRAMES * 60 + HONK_RATE - 1) // HONK_RATE + 3
    header = header.replace(b"{25,11,47,8,7,28,32,49,50}", f"{{25,11,47,8,7,28,32,{ticks},50}}".encode())
    report.update(sound_ram_high_water=address, sound_ram_unallocated=0x80000-address)
    report["drop_zone_bruce_entry"]["car_profile_free_bytes"] = free
    report["level1_housekeeping"] = dict(
        baseline=BASE, bat_sample_bytes_removed=end-start,
        honk=dict(rate=HONK_RATE, frames=len(honk), packed_bytes=len(packed_honk), pcm_sha256=sha256(honk).hexdigest()),
        drive=dict(rate=CAR_RATE, frames=len(drive), packed_bank_bytes=len(car),
                   loop_start=CAR_LOOP_START, pcm_sha256=sha256(drive).hexdigest()),
        car_profile_used_bytes=address+len(car), car_profile_free_bytes=free,
    )
    return {FX_TONE: bytes(tone), FX_SCORE: bytes(sequence), CAR_TONE: bytes(car)}, bytes(index), header


def current_pcm():
    tone = (ROOT / FX_TONE).read_bytes()
    car = (ROOT / CAR_TONE).read_bytes()
    _, start = sample(tone, 7)
    _, car_start = sample(car, 3)
    pcm = tone[start:start+HONK_FRAMES], car[car_start:car_start+CAR_FRAMES]
    report = json.loads((ROOT / "assets/music/report.json").read_text())["level1_housekeeping"]
    assert [sha256(x).hexdigest() for x in pcm] == [report[k]["pcm_sha256"] for k in ("honk", "drive")]
    return pcm
