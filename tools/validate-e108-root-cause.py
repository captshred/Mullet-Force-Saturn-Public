#!/usr/bin/env python3
"""Verify the startup delta and run current and approved baseline regressions."""
import argparse
import hashlib
import importlib
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = "7a55bae6b6428faec7300df7c82a2e4669f5063b"
CHANGED = {
    "Makefile",
    "src/wingsuit_audio.c",
    "src/wingsuit_runtime.c",
    "tests/wingsuit_mock/jo/jo.h",
    "tests/wingsuit_runtime_test.c",
    "tools/test-recovered-audio.py",
    "tools/validate-level2-balance.py",
}


def git(*args):
    return subprocess.check_output(["git", "-C", ROOT, *args])


def approved_tree():
    if subprocess.run(["git", "-C", ROOT, "cat-file", "-e", BASE], stderr=subprocess.DEVNULL).returncode:
        subprocess.run(["git", "-C", ROOT, "fetch", "--no-tags", "--depth=1", "origin", BASE], check=True)
    for item in git("ls-tree", "-r", "-z", BASE).split(b"\0"):
        if not item:
            continue
        metadata, name = item.split(b"\t", 1)
        sha = metadata.decode().split()[-1]
        path = name.decode()
        if path not in CHANGED:
            data = (ROOT / path).read_bytes()
            header = f"blob {len(data)}".encode() + b"\0"
            if hashlib.sha1(header + data).hexdigest() != sha:
                raise AssertionError(f"Approved file changed: {path}")


def preserve_sections(path, sections):
    old = git("show", BASE + ":" + path).decode()
    new = (ROOT / path).read_text()
    for begin, end in sections:
        def section(source):
            start = source.index(begin)
            return source[start:source.index(end, start) if end else None]
        assert section(old) == section(new), (path, begin)


def test_current():
    subprocess.run(["python3", "tools/test-level2-balance.py", "--e108-root-cause"], cwd=ROOT, check=True)
    subprocess.run(["python3", "tools/audit-level2-audio-sdk.py"], cwd=ROOT, check=True)
    subprocess.run(["python3", "tools/audit-level2-driver-ready.py"], cwd=ROOT, check=True)
    with tempfile.TemporaryDirectory(prefix="mf-e108-") as folder:
        exe = Path(folder) / "runtime"
        subprocess.run(["cc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-fsanitize=undefined",
                        "-fno-sanitize-recover=all", "-DMF_LEVEL2_WINGSUIT=1", "-DMF_DEV_STAGE_SKIP=1",
                        "-Itests/wingsuit_mock", "-Isrc", "tests/wingsuit_runtime_test.c",
                        "src/wingsuit.c", "-o", exe], cwd=ROOT, check=True)
        subprocess.run([exe], cwd=ROOT, check=True)


def test_approved():
    with tempfile.TemporaryDirectory(prefix="mf-e108-approved-") as folder:
        reference = Path(folder)
        subprocess.run(["git", "clone", "--quiet", "--shared", "--no-checkout", ROOT, reference], check=True)
        subprocess.run(["git", "checkout", "--quiet", "--detach", BASE], cwd=reference, check=True)
        origin = git("remote", "get-url", "origin").decode().strip()
        subprocess.run(["git", "remote", "set-url", "origin", origin], cwd=reference, check=True)
        for name in (".deps", "build"):
            (reference / name).symlink_to(ROOT / name, target_is_directory=True)
        subprocess.run(["make", "test"], cwd=reference, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disc", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    approved_tree()
    preserve_sections("src/wingsuit_audio.c", [
        ("static void enqueue(", "static int commands_empty("),
        ("static void audio_step(", None),
    ])
    preserve_sections("src/wingsuit_runtime.c", [
        ("static char *read_asset(", "static jo_palette *background_palette"),
        ("static void draw(", "void mf_ws_runtime_frame("),
    ])
    assert "SND_StopDsp(" not in (ROOT / "src/wingsuit_audio.c").read_text()
    assert "slSoundOnWait(" not in (ROOT / "src/wingsuit_audio.c").read_text()
    print("PASS approved Level 1, assets, wingsuit simulation, rendering and audio scheduling preserved", flush=True)
    if args.disc:
        importlib.import_module("validate-level2-balance").validate_disc()
        print("PASS current disc payloads and executable source fingerprint", flush=True)
    if args.test:
        test_current()
        test_approved()


if __name__ == "__main__":
    main()
