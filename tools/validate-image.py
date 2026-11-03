#!/usr/bin/env python3
"""Structural disc checks; no emulator or hardware execution is implied."""
from pathlib import Path
import hashlib,re,struct
root=Path(__file__).resolve().parents[1]
build=root/'build'; image=(build/'mullet-force.bin').read_bytes()
assert len(image)%2048==0 and image[:16]==b'SEGA SEGASATURN '
assert image[16*2048:16*2048+7]==b'\x01CD001\x01'
record=image[16*2048+156:16*2048+190]
extent=struct.unpack_from('<I',record,2)[0];size=struct.unpack_from('<I',record,10)[0]
directory=image[extent*2048:extent*2048+size]
offset=0;executable=None
while offset<len(directory):
 length=directory[offset]
 if not length: offset=(offset//2048+1)*2048;continue
 record=directory[offset:offset+length]
 if record[33:33+record[32]].upper()==b'0.BIN;1':
  sector=struct.unpack_from('<I',record,2)[0];count=struct.unpack_from('<I',record,10)[0]
  executable=image[sector*2048:sector*2048+count];break
 offset+=length
assert executable is not None
assert executable==(build/'game.raw').read_bytes()==(build/'cd/0.bin').read_bytes()
commit=re.search(r'^Commit: (.+)$',(build/'BUILD-INFO.txt').read_text(),re.M).group(1)
for marker in ('MULLET FORCE','LOADING NEON DISTRICT',commit):
 assert marker.encode() in executable,marker
assert (build/'mullet-force.cue').read_text()=='FILE "mullet-force.bin" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n    POSTGAP 00:02:00\n'
for line in (build/'SHA256SUMS.txt').read_text().splitlines():
 digest,name=line.split('  ',1)
 assert hashlib.sha256((build/name).read_bytes()).hexdigest()==digest,name
print('Disc layout, actual ISO executable, build identity and package hashes verified.')
print('BIN SHA-256:',hashlib.sha256(image).hexdigest())
print('Emulator boot, visible screen and controller behavior remain unverified.')
