#!/usr/bin/env python3
"""Reproduce and verify the three PCM8 effects against the approved PCM16 bank."""
import argparse
from hashlib import sha256
import importlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import tempfile

from level1_refinement import read as read_sequence

ROOT = Path(__file__).resolve().parents[1]
BASE = "342595360d8c0d82377b1b0a44171cef0d5ef341"
CANDIDATES = {
    0: ("Nonlethal impact", 8044, "95dbb6e91512"),
    2: ("Inorganic explosion", 15840, "2eca5219e7a0"),
    7: ("Bat swing", 16733, "8aca2c9a3c08"),
}
RATE = 22050


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def baseline(path):
    return git("show", f"{BASE}:{path}")


def aligned(n):
    return (n + 3) & ~3


def word(data, offset):
    return struct.unpack_from(">H", data, offset)[0]


def db_ratio(numerator, denominator):
    return round(20 * math.log10(numerator / denominator), 5)


def quantize(raw):
    original = struct.unpack(f">{len(raw) // 2}h", raw)
    rounded = [round(value / 256) for value in original]
    pcm = [min(127, max(-128, value)) for value in rounded]
    restored = [value * 256 for value in pcm]
    error = [a - b for a, b in zip(original, restored)]
    def rms(values):
        return math.sqrt(sum(value * value for value in values) / len(values))

    peak_before, peak_after = max(map(abs, original)), max(map(abs, restored))
    rms_before, rms_after = rms(original), rms(restored)
    # Measure the attack from the first crossing of -30 dB relative to
    # the original peak. The first 20 ms of file data can be nearly silent.
    threshold = peak_before * 10 ** (-30 / 20)
    onset_before = next(i for i, value in enumerate(original) if abs(value) >= threshold)
    onset_after = next(i for i, value in enumerate(restored) if abs(value) >= threshold)
    attack = slice(onset_before, onset_before + round(RATE * .020))
    stats = {
        "peak_pcm16_scale": [peak_before, peak_after],
        "rms_pcm16_scale": [round(rms_before, 3), round(rms_after, 3)],
        "peak_delta_db": db_ratio(peak_after, peak_before),
        "rms_delta_db": db_ratio(rms_after, rms_before),
        "attack_20ms_rms_delta_db": db_ratio(rms(restored[attack]), rms(original[attack])),
        "onset_frames_at_minus_30db": [onset_before, onset_after],
        "error_rms_pcm16_scale": round(rms(error), 3),
        "maximum_absolute_error_pcm16_scale": max(map(abs, error)),
        "signal_to_error_db": db_ratio(rms_before, rms(error)),
        "saturated_samples": sum(a != b for a, b in zip(rounded, pcm)),
        "output_rail_samples": sum(value in (-128, 127) for value in pcm),
    }
    assert not stats["saturated_samples"] and not stats["output_rail_samples"]
    return struct.pack(f"{len(pcm)}b", *pcm), stats


def repack(tone, sequence, tone_address):
    count = (word(tone, 0) - 8) // 2
    assert count == 9
    layers = [word(tone, 8 + 2 * i) + 4 for i in range(count)]
    assert all(tone[layer - 2] == 0 for layer in layers)
    offsets = [((tone[layer + 3] & 15) << 16) | word(tone, layer + 4) for layer in layers]
    assert offsets == sorted(set(offsets)) and offsets[0] == layers[-1] + 32
    bank = bytearray(tone[:offsets[0]])
    measurements = []
    for program, (layer, start, end) in enumerate(zip(layers, offsets, offsets[1:] + [len(tone)])):
        frames = word(tone, layer + 8)
        assert start % 4 == 0 and not tone[layer + 3] & 16
        pcm_end = start + frames * 2
        assert pcm_end <= end
        new_start = len(bank)
        flags = tone[layer + 3] & 0xf0
        if program in CANDIDATES:
            name, expected_frames, digest = CANDIDATES[program]
            raw = tone[start:pcm_end]
            assert frames == expected_frames and sha256(raw).hexdigest().startswith(digest)
            assert not (flags & 0x60) and word(tone, layer + 6) == 0
            assert tone[layer + 25] == 72 and end == aligned(pcm_end)
            assert not any(tone[pcm_end:end])
            _, events, _ = read_sequence(sequence, program)
            notes = [event for event in events if event["kind"] == "note"]
            assert [(n["program"], n["pitch"], n["velocity"]) for n in notes] == [(program, 60, 127)]
            pcm, stats = quantize(raw)
            flags |= 16
            bank.extend(pcm)
            bank.extend(bytes(aligned(len(bank)) - len(bank)))
            measurements.append({
                "program": program, "name": name, "sample_rate": RATE, "frames": frames,
                "original_pcm_bytes": len(raw), "converted_pcm_bytes": len(pcm),
                "packed_bytes_saved": end - start - (len(bank) - new_start),
                "original_address": tone_address + start, "converted_address": tone_address + new_start,
                "original_pcm_sha256": sha256(raw).hexdigest(),
                "converted_pcm_sha256": sha256(pcm).hexdigest(), **stats,
            })
        else:
            bank.extend(tone[start:end])
        assert new_start < 0x80000
        bank[layer + 3] = flags | (new_start >> 16)
        struct.pack_into(">H", bank, layer + 4, new_start & 0xffff)
    return bytes(bank), measurements


def fingerprint(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def replace_define(header, name, value):
    updated, count = re.subn(rb"(?m)^(#define " + name.encode() + rb" )\d+$",
                             lambda match: match[1] + str(value).encode(), header)
    assert count == 1, name
    return updated


def outputs():
    map_path = "assets/cd/CUSTOM.MAP"
    tone_path = "assets/cd/FX.TON"
    report_path = "assets/music/report.json"
    lock_path = "assets/public-runtime-lock.json"
    header_path = "src/music_data.h"
    index = bytearray(baseline(map_path))
    old_tone = baseline(tone_path)
    fx_base = int.from_bytes(index[25:28], "big")
    tone, measurements = repack(old_tone, baseline("assets/cd/FX.SEQ"), fx_base)
    report = json.loads(baseline(report_path))
    lengths = [len(tone), len(baseline("assets/cd/STAGE.SEQ")), len(baseline("assets/cd/STAGE.TON"))]
    address = fx_base
    for offset, region, length in zip((24, 32, 40), report["sound_ram_regions"][-3:], lengths):
        old_address = int.from_bytes(index[offset + 1:offset + 4], "big")
        old_size = int.from_bytes(index[offset + 5:offset + 8], "big")
        assert (region["start"], region["size"]) == (old_address, old_size)
        assert index[offset + 4] == 0x80 and address % 4 == length % 4 == 0
        index[offset + 1:offset + 4] = address.to_bytes(3, "big")
        index[offset + 5:offset + 8] = length.to_bytes(3, "big")
        region.update(start=address, size=length, end=address + length)
        address += length
    savings = report["sound_ram_high_water"] - address
    assert savings == len(old_tone) - len(tone) == sum(m["packed_bytes_saved"] for m in measurements)
    assert 0 <= address <= 524288 and index[48:] == b"\xff" * 8
    report.update(sound_ram_high_water=address, sound_ram_unallocated=524288 - address)
    report["level1_sfx_pcm8_pass1"] = {
        "baseline": BASE, "encoding": "signed PCM8, nearest ties-to-even, no dither or gain change",
        "packed_bytes_saved": savings, "samples": measurements,
    }
    binaries = {map_path: bytes(index), tone_path: tone}
    lock_text = baseline(lock_path)
    lock = json.loads(lock_text)
    for path, data in binaries.items():
        old_entry = lock[path]
        entry = fingerprint(data)
        # Update just the two existing lock entries, preserving the rest verbatim.
        for key in ("bytes", "sha256"):
            old = json.dumps(old_entry[key]).encode()
            new = json.dumps(entry[key]).encode()
            pattern = (rb'("' + re.escape(path.encode()) + rb'": \{[^}]*?"' +
                       key.encode() + rb'": )' + old)
            lock_text, count = re.subn(pattern, lambda match: match[1] + new, lock_text)
            assert count == 1, (path, key)
        report["outputs"][Path(path).name] = entry
    header = baseline(header_path)
    for macro, value in {
        "MF_FX_TON_BYTES": len(tone),
        "MF_STAGE_SEQ_ADDR": fx_base + len(tone),
        "MF_STAGE_TON_ADDR": address - lengths[-1],
    }.items():
        header = replace_define(header, macro, value)
    return {
        **binaries, header_path: header, lock_path: lock_text,
        report_path: (json.dumps(report, indent=2) + "\n").encode(),
    }


def test_level1():
    with tempfile.TemporaryDirectory(prefix="mf-pcm8-") as directory:
        exe = Path(directory) / "ugh_transport_test"
        subprocess.run(["cc", "-std=c99", "-Wall", "-Wextra", "-Werror",
                        "-fsanitize=undefined", "-fno-sanitize-recover=all",
                        "-Itests/sound_mock", "-Isrc", "tests/ugh_transport_test.c", "-o", exe],
                       cwd=ROOT, check=True)
        subprocess.run([exe], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--disc", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if subprocess.run(["git", "cat-file", "-e", BASE + "^{commit}"], cwd=ROOT,
                      capture_output=True).returncode:
        subprocess.run(["git", "fetch", "--no-tags", "--depth=1", "origin", BASE], cwd=ROOT, check=True)
    expected = outputs()
    for path, data in expected.items():
        if args.write:
            (ROOT / path).write_bytes(data)
        assert (ROOT / path).read_bytes() == data, path

    changed = set(git("diff", "--name-only", BASE, "--").decode().splitlines())
    assert changed <= set(expected) | {"Makefile", "tools/level1-sfx-pcm8-pass1.py",
                                     "docs/level1-sfx-pcm8-pass1.md"}, changed
    print("PASS exact PCM8 payloads, contiguously relocated banks, and protected baseline files", flush=True)
    if args.disc:
        importlib.import_module("validate-level2-balance").validate_disc()
        print("PASS native disc payloads and executable source fingerprint", flush=True)
    if args.test:
        test_level1()
        startup = importlib.import_module("validate-e108-root-cause")
        startup.test_current()
        startup.test_approved()


if __name__ == "__main__":
    main()
