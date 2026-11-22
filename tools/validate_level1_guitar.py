#!/usr/bin/env python3
"""Verify the auditioned guitar PCM and the exact sound-bank delta."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

import level1_housekeeping

ROOT = Path(__file__).resolve().parents[1]
BASE = "382b226b476b305c9ebab8e6d2ddbe763603d41b"
TON = "assets/cd/STAGE.TON"
MAP = "assets/cd/CUSTOM.MAP"
HEADER = "src/music_data.h"
REPORT = "assets/music/report.json"
LOCK = "assets/public-runtime-lock.json"
SEQ = "assets/cd/STAGE.SEQ"
AUDIO_DELTA = {TON, MAP, HEADER, REPORT, LOCK, SEQ} | level1_housekeeping.AUDIO_DELTA
PREVIEWS = "docs/audio-previews/guitar-sustain-rebuild/"
SCOPE = AUDIO_DELTA | {
    "Makefile", "tools/validate_level1_guitar.py", "tools/validate_level1_diagonal.py",
    "downloads/mullet-force-level1-medium-guitar.zip",
    "tools/level1-sfx-pcm8-pass1.py",
} | {PREVIEWS + name for name in (
    "README.md", "measurements.json", "muted-auditions.wav", "open-loop-auditions.wav",
    "open-long-pcm16-vs-pcm8.wav", "open-loop-auditions-pcm8.wav", "score-palm-muted.wav",
    "score-rapid.wav", "score-sustained.wav",
)}
START, END = 4344, 10937
PCM_SHA = "85af16caed83de4e60841cbb325df88578dda2d755145a2eb5ef50292c8682ef"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def old(path):
    return git("show", f"{BASE}:{path}")


def fingerprint(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def voice(data, program):
    layer = int.from_bytes(data[8 + 2 * program:10 + 2 * program], "big") + 4
    address = ((data[layer + 3] & 15) << 16) | int.from_bytes(data[layer + 4:layer + 6], "big")
    return layer, address


def outputs(pcm, mix=False, vehicle_pcm=None):
    assert fingerprint(pcm) == {"bytes": END * 2, "sha256": PCM_SHA}
    original = old(TON)
    count = (int.from_bytes(original[:2], "big") - 8) // 2
    first_layer, address = voice(original, 0)
    _, next_address = voice(original, 1)
    assert count == 13 and address == 544 and next_address - address == 6736

    sample = pcm + pcm[2 * START:2 * START + 4]
    sample += bytes(-len(sample) % 4)
    delta = len(sample) - (next_address - address)
    tone = bytearray(original[:address] + sample + original[next_address:])
    tone[first_layer + 6:first_layer + 10] = START.to_bytes(2, "big") + END.to_bytes(2, "big")
    for program in range(1, count):
        layer, sa = voice(original, program)
        relocated = sa + delta
        tone[layer + 3] = (original[layer + 3] & 0xf0) | (relocated >> 16)
        tone[layer + 4:layer + 6] = (relocated & 0xffff).to_bytes(2, "big")

    if mix:
        import level1_music_mix
        tone = level1_music_mix.apply(tone, voice)

    index = bytearray(old(MAP))
    stage = len(index) - 16
    assert index[stage] == 1 and index[stage + 4] == 0x80
    assert int.from_bytes(index[stage + 5:stage + 8], "big") == len(original)
    base = int.from_bytes(index[stage + 1:stage + 4], "big")
    index[stage + 5:stage + 8] = len(tone).to_bytes(3, "big")
    high_water = base + len(tone)
    assert (delta, high_water) == (15144, 478000 if mix else 477988)

    report = json.loads(old(REPORT))
    report["sound_ram_regions"][-1].update(size=len(tone), end=high_water)
    report.update(sound_ram_high_water=high_water, sound_ram_unallocated=524288-high_water)
    report["level1_open_guitar_medium"] = dict(
        baseline=BASE, program=0, sample_rate=22050, bits=16, frames=END,
        loop_start=START, loop_end=END, crossfade_frames=176, pcm_sha256=PCM_SHA,
        packed_bytes=len(sample), additional_bytes=delta,
    )
    if mix:
        report["level1_music_mix_midpoint"] = dict(
            baseline=level1_music_mix.BASE, drum_tl_change=0,
            drum_pcm_gain=level1_music_mix.DRUM_PCM_GAIN,
            bass_velocity_curve_before=list(level1_music_mix.SHARED_CURVE),
            bass_velocity_curve_after=list(level1_music_mix.BASS_CURVE),
            bass_cc7=127, bass_cc11=127, bass_tl=0, additional_bytes=12,
        )
    header, count_updated = re.subn(rb"(?m)^#define MF_STAGE_TON_BYTES 132148$",
                                    f"#define MF_STAGE_TON_BYTES {len(tone)}".encode(), old(HEADER))
    assert count_updated == 1
    assets = {TON: tone, MAP: index}
    if mix:
        import drop_zone_sequence as score
        bank = score.build(score.baseline(SEQ))
        index, header = score.relocate(bank, index, header, report)
        assets.update({SEQ: bank, MAP: index})
        honk, drive = vehicle_pcm if vehicle_pcm is not None else level1_housekeeping.baseline_vehicle_pcm()
        vehicle_assets, index, header = level1_housekeeping.outputs(honk, drive, index, header, report)
        assets.update(vehicle_assets)
        assets[MAP] = index
    lock = old(LOCK)
    entries = json.loads(lock)
    for path, data in assets.items():
        entry = fingerprint(data)
        if path not in entries:
            # The vehicle bank predates this runtime lock. Its exact bytes
            # are independently verified by the housekeeping validator.
            report["outputs"][Path(path).name] = entry
            continue
        previous = entries[path]
        for key in ("bytes", "sha256"):
            pattern = (rb'("' + re.escape(path.encode()) + rb'": \{[^}]*?"' +
                       key.encode() + rb'": )' + json.dumps(previous[key]).encode())
            lock, count_updated = re.subn(pattern, lambda match: match[1] + json.dumps(entry[key]).encode(), lock)
            assert count_updated == 1, (path, key)
        report["outputs"][Path(path).name] = entry
    return {**assets, HEADER: header, LOCK: lock,
            REPORT: (json.dumps(report, indent=2) + "\n").encode()}


def validate(pcm=None, mix=False, write_mix=False, vehicle_pcm=None):
    if subprocess.run(["git", "cat-file", "-e", BASE + "^{commit}"], cwd=ROOT,
                      capture_output=True).returncode:
        git("fetch", "--no-tags", "--depth=1", "origin", BASE)
    if pcm is None:
        tone = (ROOT / TON).read_bytes()
        _, address = voice(tone, 0)
        pcm = tone[address:address + END * 2]
        write = write_mix
    else:
        write = True
    for path, data in outputs(pcm, mix, vehicle_pcm).items():
        if write:
            (ROOT / path).write_bytes(data)
        assert (ROOT / path).read_bytes() == data, path
    changed = set(git("diff", "--name-only", BASE, "--").decode().splitlines())
    scope = SCOPE
    if mix:
        import level1_music_mix
        from validate_level1_diagonal import validate_hq_scope
        hq_scope = validate_hq_scope()
        level1_music_mix.validate_scope(git, hq_scope)
        scope = scope | level1_music_mix.SCOPE | hq_scope
    assert changed <= scope, changed - scope
    print("PASS exact Medium PCM, loop and guard, protected instruments and gameplay"
          + (", Level 1 midpoint gains and exact native Drop Zone entrances" if mix
             else ", 46,300 SCSP bytes free"), flush=True)
    return scope


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcm", type=Path, help="Install the hash-verified audition PCM")
    parser.add_argument("--mix-pass1", action="store_true")
    parser.add_argument("--write-mix", action="store_true", help="Install the verified native mix")
    parser.add_argument("--vehicle-wavs", type=Path, help="Private directory containing honk.wav and drive.wav")
    args = parser.parse_args()
    assert not args.write_mix or args.mix_pass1
    vehicle_pcm = None
    if args.vehicle_wavs:
        assert args.write_mix
        h = level1_housekeeping
        vehicle_pcm = (h.import_pcm(args.vehicle_wavs / "honk.wav", h.HONK_RATE),
                       h.import_pcm(args.vehicle_wavs / "drive.wav", h.CAR_RATE, h.CAR_LOOP_START))
    validate(args.pcm.read_bytes() if args.pcm else None, mix=args.mix_pass1,
             write_mix=args.write_mix, vehicle_pcm=vehicle_pcm)
