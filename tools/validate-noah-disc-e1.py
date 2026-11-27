#!/usr/bin/env python3
"""Verify legacy RUN and VDP1 street exclusions from the Noah disc against the approved asset layout."""
import argparse
from hashlib import sha256
from pathlib import Path

from wingsuit_disc import GFS_LIMIT, SECTOR, directory_records

LEGACY_RUN = frozenset(f"RN{index:02}.TGA" for index in range(24))
LEGACY_STREET = frozenset(f"ST{index}.TGA" for index in range(1, 5))
# Payloads come from the Phase D (26ca8b5) staging inventory. Record order
# comes from the approved e0c65d3f disc with the same asset inventory.
# Both fingerprints omit LEGACY_RUN and LEGACY_STREET.
# The executable payload varies per build.
APPROVED_PAYLOADS = "e75ea2d1a1ee8225362d3b45397890a772f3b9ac1ebf5267edc90799fb3bf3fa"
APPROVED_RECORDS = "c045f24ecba51127805df2489d96401941cee3e9d89742482cbc77908216c629"
ROOT_LOOKUPS = {
    "0.BIN": 2, "ALEVEL2": 42, "CARPASS.TON": 65,
    "CICELL.BIN": 82, "CIMAP.BIN": 83, "COMBAT": 85, "COMBO": 86,
    "CUSTOM.MAP": 108, "FX.SEQ": 131, "FX.TON": 132, "HQDEATH": 140, "HQHURT": 141,
    "HQJUMP": 142, "HQTORCH": 143, "IXMAP.BIN": 144, "IXOFF.BIN": 145,
    "IXPACK.BIN": 146, "LCMAP.BIN": 147, "LCSKY.BIN": 148, "NSPAL.BIN": 166,
    "RBV00.TGA": 209, "RICKY": 223,
    "SHADOW.TGA": 224, "ST0.TGA": 225, "STAGE.SEQ": 226, "STAGE.TON": 227,
    "STCELLS.BIN": 228,
}
ROOT_BYTES = 6 * SECTOR
BOOT_EXECUTABLE_LBA = 39


def word(record, offset):
    value = int.from_bytes(record[offset:offset + 4], "little")
    assert value == int.from_bytes(record[offset + 4:offset + 8], "big")
    return value


def payload_digest(files):
    return sha256("".join(
        f"{name}\t{len(data)}\t{sha256(data).hexdigest()}\n"
        for name, data in sorted(files.items())
    ).encode()).hexdigest()


def validate_payloads(files):
    assert "ST0.TGA" in files, "Startup requires ST0.TGA"
    remaining = (LEGACY_RUN | LEGACY_STREET).intersection(files)
    assert not remaining, f"Excluded textures still present: {sorted(remaining)}"
    assert len(files) == 415, f"Expected 415 assets, found {len(files)}"
    assert payload_digest(files) == APPROVED_PAYLOADS, "Approved disc payload inventory differs"


def validate_stage(stage):
    files = {
        path.relative_to(stage).as_posix(): path.read_bytes()
        for path in stage.rglob("*") if path.is_file() and path != stage / "0.bin"
    }
    validate_payloads(files)


def inspect_disc(image, removed=()):
    assert image[:16] == b"SEGA SEGASATURN " and len(image) % SECTOR == 0
    pvd = image[16 * SECTOR:17 * SECTOR]
    assert pvd[:7] == b"\x01CD001\x01"
    root = pvd[156:190]
    files = {}
    metadata = []
    root_names = []

    def extent(record):
        return word(record, 2), word(record, 10)

    def walk(directory, parent, prefix):
        names = []
        for name, record in directory_records(image, directory):
            path = prefix + name
            if path in removed:
                continue
            lba, size = extent(record)
            start = lba * SECTOR
            assert start + size <= len(image), path
            names.append(name)
            metadata.append(f"{path}\t{len(record)}\t{record[25]}\t{record[33:33 + record[32]].hex()}\n")
            if name == ".":
                assert record[25] & 2 and (lba, size) == extent(directory), path
                continue
            if name == "..":
                assert record[25] & 2 and (lba, size) == extent(parent), path
                continue
            if record[25] & 2:
                walk(record, directory, path + "/")
            elif path != "0.BIN":
                files[path] = image[start:start + size]
            else:
                assert start == BOOT_EXECUTABLE_LBA * SECTOR and size > 0, "Boot executable extent moved"
        if prefix:
            assert len(names) <= GFS_LIMIT, prefix
        else:
            root_names.extend(names)

    walk(root, root, "")
    return files, metadata, root_names, word(root, 10)


def validate_disc(image):
    files, metadata, names, root_bytes = inspect_disc(image)
    assert len(names) <= GFS_LIMIT, "Root directory exceeds the GFS window"
    assert len(names) == 237 and root_bytes == ROOT_BYTES, "Root directory geometry changed"
    for name, index in ROOT_LOOKUPS.items():
        assert index < GFS_LIMIT and names[index] == name, (name, index)
    assert sha256("".join(metadata).encode()).hexdigest() == APPROVED_RECORDS, "ISO directory records or order changed"
    validate_payloads(files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--stage", type=Path)
    source.add_argument("--disc", type=Path)
    args = parser.parse_args()
    if args.stage:
        validate_stage(args.stage)
        print("PASS Noah F1 staging: exactly the legacy RUN and ST1–ST4 textures excluded")
    else:
        validate_disc(args.disc.read_bytes())
        print("PASS Noah F1 disc: exact assets and directory records, required lookups within GFS window")
