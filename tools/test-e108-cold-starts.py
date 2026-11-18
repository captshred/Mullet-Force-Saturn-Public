#!/usr/bin/env python3
"""Run separate Yabause processes against a matching Saturn disc and SH-2 symbol file."""
import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from wingsuit_disc import directory_records

ROOT = Path(__file__).resolve().parents[1]
CORE_PIN = "8926b0c6c347f8c5c755911ddb0ac695420ffbf8"


def addresses(program):
    data = program.read_bytes()
    offset, count = struct.unpack_from(">II", data, 8)
    strings = data[offset + count * 18:]
    symbols = {}
    index = 0
    while index < count:
        start = offset + index * 18
        name = data[start:start + 8]
        if name[:4] == bytes(4):
            name = strings[int.from_bytes(name[4:], "big"):]
        name = name.split(b"\0", 1)[0].decode(errors="replace")
        address = int.from_bytes(data[start + 8:start + 12], "big")
        section = struct.unpack_from(">h", data, start + 12)[0]
        if section > 0:
            symbols[name] = address
        index += 1 + data[start + 17]

    def symbol(name):
        matches = [value for key, value in symbols.items()
                   if key == name or key.startswith(name + ".lto_priv.")]
        if len(matches) != 1:
            raise ValueError(f"{name}: expected one symbol, got {matches}")
        return matches[0]

    error = symbol("_error")
    phases = [value for name, value in symbols.items() if re.fullmatch(r"_phase\.lto_priv\.\d+", name)]
    # The other phase belongs to the enemy-bank loader, in a different object.
    phase = min(phases, key=lambda address: abs(address - error))
    if abs(phase - error) >= 256:
        raise ValueError("Could not locate the wingsuit runtime phase")
    return phase, error, symbol("_game"), symbol("_mf_ws_startup_capture")


def disc_bytes(cue):
    match = re.search(r'^FILE "([^"]+)" BINARY$', cue.read_text(), re.MULTILINE)
    if not match:
        raise ValueError("Expected a single-track BIN/CUE")
    return (cue.parent / match[1]).read_bytes()


def disc_program(disc):
    for name, record in directory_records(disc, disc[16 * 2048 + 156:16 * 2048 + 190]):
        if name == "0.BIN":
            start = struct.unpack_from("<I", record, 2)[0] * 2048
            size = struct.unpack_from("<I", record, 10)[0]
            return disc[start:start + size]
    raise ValueError("Disc is missing /0.BIN")


def build_frontend(args, out):
    sdk = (args.core_checkout or ROOT / ".deps/e108-yabause").resolve()
    if not sdk.exists():
        subprocess.run(["git", "clone", "--no-checkout", "https://github.com/libretro/yabause.git",
                        str(sdk)], check=True)
        subprocess.run(["git", "-C", str(sdk), "checkout", "--detach", CORE_PIN], check=True)
    lib = sdk / "yabause/src/libretro"
    if subprocess.check_output(["git", "-C", str(sdk), "rev-parse", "HEAD"], text=True).strip() != CORE_PIN:
        raise ValueError("Wrong Yabause checkout")
    for name, probe_name in (("libretro/libretro.c", "e108-yabause-probe.inc"),
                             ("scsp.c", "e108-yabause-scsp-probe.inc")):
        rel = "yabause/src/" + name
        source = sdk / rel
        upstream = subprocess.check_output(["git", "-C", str(sdk), "show", f"{CORE_PIN}:{rel}"])
        probe = (ROOT / "tests/runtime" / probe_name).read_bytes()
        if source.read_bytes() not in (upstream, upstream + probe):
            raise ValueError("Use a dedicated, unmodified Yabause checkout for this probe")
        if source.read_bytes() != upstream + probe:
            source.write_bytes(upstream + probe)
    with (out / "core-build.log").open("w") as log:
        subprocess.run(["make", "-C", str(lib), "-j2"], stdout=log, stderr=subprocess.STDOUT, check=True)
    core = lib / "yabause_libretro.so"
    frontend = out / "frontend"
    subprocess.run(["cc", "-O2", "-Wall", "-Wextra", "-Werror", "-I" + str(lib / "libretro-common/include"),
                    str(ROOT / "tests/runtime/e108-startup-frontend.c"), "-ldl", "-o", str(frontend)], check=True)
    return core, frontend


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cue", type=Path, default=ROOT / "build/mullet-force.cue")
    parser.add_argument("--program", type=Path, default=ROOT / "build/game.elf")
    parser.add_argument("--raw", type=Path, default=ROOT / "build/game.raw")
    parser.add_argument("--build-info", type=Path, default=ROOT / "build/build-info.h")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--core-checkout", type=Path)
    parser.add_argument("--bios-directory", type=Path)
    parser.add_argument("--cold", type=int, default=50)
    parser.add_argument("--warm", type=int, default=0, help="Reset rounds in a separate emulator process")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--start-frame", type=int, default=1000)
    parser.add_argument("--skip-frame", type=int, default=1100)
    parser.add_argument("--spread", type=int, default=31, help="Number of consecutive X timing offsets")
    parser.add_argument("--pause", nargs=2, type=int, default=(0, 0), metavar=("START", "RESUME"))
    parser.add_argument("--stress", type=int, default=0, help="Extra frames of two-player input after Level 2 entry")
    parser.add_argument("--timeout", type=int, default=360, help="Host seconds allowed per process")
    args = parser.parse_args()
    if args.cold < 1 or args.jobs < 1 or args.spread < 1 or args.warm < 0 or args.stress < 0:
        parser.error("Invalid cycle count, timing spread, stress or parallelism")
    out = args.out.resolve()
    out.mkdir(parents=True)
    disc = disc_bytes(args.cue)
    if disc_program(disc) != args.raw.read_bytes():
        raise ValueError("The disc and raw executable differ")
    build_info = args.build_info.resolve()
    offset_exe = out / "started-offset"
    subprocess.run(["cc", "-include", str(build_info), "-I", str(ROOT / "src"), "-x", "c", "-o",
                    str(offset_exe), "-"], input=('#include <stddef.h>\n#include <stdio.h>\n#include "game.h"\n'
                    'int main(void) { printf("%zu\\n", offsetof(mf_game, started)); }\n'), text=True, check=True)
    started_offset = int(subprocess.check_output([offset_exe]))
    phase, error, game, trace = addresses(args.program)
    core, frontend = build_frontend(args, out)
    environment = dict(os.environ, MF_E108_START_FRAME=str(args.start_frame))
    bios = str(args.bios_directory.resolve()) if args.bios_directory else "-"

    def run_trial(index, warm=0):
        save = out / (f"cold-{index + 1:03}" if not warm else "warm-reset")
        save.mkdir()
        skip = args.skip_frame + index % args.spread
        numeric_args = [hex(phase), hex(error), hex(game + started_offset), hex(trace),
                        skip, *args.pause, skip + 1400 + args.stress, warm, args.stress]
        command = [frontend, core, args.cue.resolve(), save, bios, *map(str, numeric_args)]
        with (save / "trace.csv").open("w") as log, (save / "core.log").open("w") as err:
            try:
                status = subprocess.run(command, env=environment, stdout=log, stderr=err,
                                        timeout=(warm + 1) * args.timeout).returncode
            except subprocess.TimeoutExpired:
                status = 124
        rounds = []
        with (save / "trace.csv").open() as log:
            for row in csv.reader(log):
                if not row or row[0] != "RESULT":
                    continue
                names = ("round", "end_frame", "phase", "error", "level1_frame", "level2_frame", "pcm_frames", "pcm_peak")
                rounds.append(dict(zip(names, map(int, row[1:]))))
        result = {"trial": save.name, "skip_frame": skip, "exit_status": status, "rounds": rounds}
        print(json.dumps(result), flush=True)
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        jobs = [pool.submit(run_trial, index) for index in range(args.cold)]
        if args.warm:
            jobs.append(pool.submit(run_trial, 0, args.warm))
        trials = [job.result() for job in jobs]
    summary = {"core_commit": CORE_PIN, "bios": bios if bios != "-" else "Yabause HLE",
               "bin_sha256": hashlib.sha256(disc).hexdigest(), "trials": trials}
    (out / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    return any(trial["exit_status"] for trial in trials)


if __name__ == "__main__":
    raise SystemExit(main())
