#!/usr/bin/env python3
"""Verify the single-file Noah disc delta against the approved asset layout."""
import argparse
from hashlib import sha256
from pathlib import Path

from wingsuit_disc import GFS_LIMIT, SECTOR, directory_records

REMOVED = "RN23.TGA"
# Payloads come from the Phase D (26ca8b5) staging inventory. Record order
# comes from the approved e0c65d3f disc with the same asset inventory.
# Both fingerprints omit RN23.TGA; the executable payload varies per build.
APPROVED_PAYLOADS = "08b7281a52a5f75579aeb82ba35cd8c463ebd638a1bc6af7ee0f7ae6fcb132fd"
APPROVED_RECORDS = "92afd0a269148555e19e27d491d553f6321cf205def44da12ec57a2614c95c55"
ROOT_LOOKUPS = {
    "0.BIN": 2, "ALEVEL2": 42, "CARPASS.TON": 65,
    "CICELL.BIN": 82, "CIMAP.BIN": 83, "COMBAT": 85, "CUSTOM.MAP": 108,
    "FX.SEQ": 131, "FX.TON": 132, "IXMAP.BIN": 144, "IXOFF.BIN": 145,
    "IXPACK.BIN": 146, "NSPAL.BIN": 166, "RBV00.TGA": 209, "RICKY": 223,
    "SHADOW.TGA": 247, "ST0.TGA": 248, "STAGE.SEQ": 253, "STAGE.TON": 254,
    "STCELLS.BIN": 255,
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
    assert REMOVED not in files, f"{REMOVED} still present"
    assert len(files) == 442, f"Expected 442 assets, found {len(files)}"
    assert payload_digest(files) == APPROVED_PAYLOADS, "Approved disc payload inventory differs"


def validate_stage(stage):
    files = {
        path.relative_to(stage).as_posix(): path.read_bytes()
        for path in stage.rglob("*") if path.is_file() and path != stage / "0.bin"
    }
    validate_payloads(files)


def inspect_disc(image, removed=None):
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
            if path == removed:
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
    assert len(names) == 264 and root_bytes == ROOT_BYTES, "Root directory geometry changed"
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
        print("PASS Noah E1 staging: only RN23.TGA excluded")
    else:
        validate_disc(args.disc.read_bytes())
        print("PASS Noah E1 disc: exact assets and directory records, required lookups within GFS window")
