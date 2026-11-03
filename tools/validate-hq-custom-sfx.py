#!/usr/bin/env python3
from preserved_source import preserved_bytes
"""Lock latest HQ artwork/music and verify actual disc sound payloads."""
from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1]
v=json.loads((R/'assets/sfx/custom-combat/hq-integration-verification.json').read_text())
for group in ['unchanged','wavs']:
 for name,sha in v[group].items():assert hashlib.sha256(preserved_bytes(R,name)).hexdigest()==sha,name
image=(R/'build/mullet-force.bin').read_bytes();rec=image[16*2048+156:16*2048+190];start=struct.unpack_from('<I',rec,2)[0]*2048;size=struct.unpack_from('<I',rec,10)[0];directory=image[start:start+size];files={};i=0
while i<len(directory):
 n=directory[i]
 if not n:i=(i//2048+1)*2048;continue
 r=directory[i:i+n];name=r[33:33+r[32]].decode('ascii');at=struct.unpack_from('<I',r,2)[0]*2048;count=struct.unpack_from('<I',r,10)[0];files[name.upper()]=image[at:at+count];i+=n
for name in ['STAGE.SEQ','STAGE.TON','FX.SEQ','FX.TON','CUSTOM.MAP']:
 assert files[name+';1']==(R/'assets/cd'/name).read_bytes(),('disc payload mismatch',name)
print('PASS exact latest HQ artwork/music and source WAV hashes; actual ISO contains exact approved custom FX and unchanged stage payloads.')
