#!/usr/bin/env python3
"""Verify the startup delta and run current and approved baseline regressions."""
import argparse
import hashlib
import importlib
from pathlib import Path
import os
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


def verify_baseline(repo):
    commit = subprocess.check_output(["git", "rev-parse", "--verify", BASE + "^{commit}"],
                                     cwd=repo, text=True).strip()
    if commit != BASE:
        raise RuntimeError(f"Unexpected approved baseline commit: {commit}")
    # Traverse the complete snapshot, including every subtree and blob.
    subprocess.run(["git", "rev-list", "--objects", "--missing=error", BASE],
                   cwd=repo, stdout=subprocess.DEVNULL, check=True)


def approved_tree():
    if subprocess.run(["git", "-C", ROOT, "rev-list", "--objects", "--missing=error", BASE],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        subprocess.run(["git", "-C", ROOT, "fetch", "--refetch", "--no-tags", "--depth=1",
                        "origin", BASE], check=True)
    verify_baseline(ROOT)
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


def stage_approved_fixture(reference, env):
    # The pinned scripts predate --stage-only. Run their staging commands
    # in the historical tree and stop at the Saturn compilation boundary.
    profile_path = "tools/build-source-complete.sh"
    native_path = "tools/build-native.sh"
    profile = (reference / profile_path).read_text()
    native = (reference / native_path).read_text()
    entry = "bash tools/build.sh --native"
    boundary = "\nmake -C build -f ../make/saturn.mk "
    if profile.count(entry) != 1 or native.count(boundary) != 1:
        raise RuntimeError("Historical staging entry point or native build boundary changed")
    profile = profile.replace(entry, 'bash -c "$1" tools/build-native.sh')
    staging = native.split(boundary, 1)[0]
    subprocess.run(["bash", "-c", profile, profile_path, staging],
                   cwd=reference, env=env, check=True)


def test_approved():
    with tempfile.TemporaryDirectory(prefix="mf-e108-approved-") as folder:
        reference = Path(folder)
        # Fetch into an independent object store so shallow CI checkouts
        # cannot affect which baseline objects are visible in the test clone.
        origin = git("remote", "get-url", "origin").decode().strip()
        subprocess.run(["git", "init", "--quiet"], cwd=reference, check=True)
        subprocess.run(["git", "remote", "add", "origin", origin], cwd=reference, check=True)
        subprocess.run(["git", "fetch", "--no-tags", "origin", BASE],
                       cwd=reference, check=True)
        verify_baseline(reference)
        subprocess.run(["git", "checkout", "--quiet", "--detach", BASE], cwd=reference, check=True)
        (reference / ".deps").symlink_to(ROOT / ".deps", target_is_directory=True)
        # GNU make can also forward command-line MF_* overrides through MAKEFLAGS.
        env = {name: value for name, value in os.environ.items()
               if not name.startswith("MF_") and name not in {"MAKEFLAGS", "MFLAGS", "MAKEOVERRIDES"}}
        stage_approved_fixture(reference, env)
        # Historical link-budget assertions still inspect the candidate's
        # native link. Share only those inputs, leaving staging isolated.
        for name in ("game.elf", "game.raw", "game.map"):
            (reference / "build" / name).symlink_to(ROOT / "build" / name)
        subprocess.run(["make", "test"], cwd=reference, env=env, check=True)


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
