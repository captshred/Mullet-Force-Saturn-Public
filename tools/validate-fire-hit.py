#!/usr/bin/env python3
"""Bank identity, immutable scheduler sections and native allocator isolation."""
from pathlib import Path
import hashlib,json,struct,subprocess,importlib.util
R=Path(__file__).resolve().parents[1];A=R/'assets/wingsuit'
r=json.loads((A/'fire-hit.json').read_text());t=(A/'WFIRE.TON').read_bytes();old=(A/'WDEATH.TON').read_bytes()
assert len(t)==38224 and struct.unpack_from('>5H',t)==(10,28,38,48,52)
assert t[10:52]==old[16:58]
v=bytearray(t[52:88]);o=bytearray(old[94:130])
for b in (v,o):b[7]&=240;b[8:14]=bytes(6)
assert v==o,'all tone parameters other than address/sample bounds must match'
assert hashlib.sha256(t[88:88+38132]).hexdigest()==r['pcm_sha256']
assert t[-4:]==bytes(4) and r['source']['sha256']=='1abc11ab39191e031c38b5ec1c27a919a01b2e667d53d4a44c549b0f87bcfe35'
assert struct.unpack_from('>HH',t,62)==(0,19066)
for n,e in r['files'].items():
 b=(A/n).read_bytes();assert len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256']
base='6e5c8d9eb9b83e4cf3ebb278939b02b8787a0b1e'
# Parent is fetched for its source archive by the main reference harness only
# when needed; the lock records section hashes so this check is history-free.
x=json.loads((R/'docs/fire-hit-lock.json').read_text());s=(R/'src/wingsuit_audio.c').read_text()
for name,e in x['sections'].items():
 a=s.index(e['begin']);b=s.index(e['end'],a);expected=e['sha256'] if name!='readiness' else json.loads((R/'docs/fire-hit-startup-lock.json').read_text())['startup_sha256'];assert hashlib.sha256(s[a:b].encode()).hexdigest()==expected,name
spec=importlib.util.spec_from_file_location('native',R/'tools/audit-level2-polyphony.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
driver=(R/'.deps/joengine/Compiler/COMMON/SGL_302j/INC/SDDRVS.TSK').read_bytes();assert hashlib.sha256(driver).hexdigest()==native.PIN
# 29 principal slots (18 music + 4 Flame handoff + 2 Fire + 4 Explosion + Hit)
# leave three native allocator records. Different MIDI channels share gain only.
slots=[(0,0x100|60,0xa,i+1) for i in range(18)]
slots += [(1,k,0xa,i+19) for i,k in enumerate([60,61,0x13c,0x13d])]
slots += [(2,0x23c,0xa,23),(3,0x33c,0xa,24)]
slots += [(p,(p<<8)|60,0xa,p+21) for p in range(4,8)]
slots += [(2,0x83c,0xa,29)]+[(0,0,0,0)]*3
for port,key in [(2,0x83c),(2,0x23c),(3,0x33c)]:
 chosen,fallback=native.allocator(driver,slots,port,key);assert chosen==29 and not fallback
assert len(slots)==32 and r['scsp_high_water']==485812 and r['scsp_free']==38476
print('PASS Fire/Hit resources: exact mono import, immutable old Shot/Flame/music/Explosion bank, frozen Fire/Explosion schedulers and readiness; native allocator selects free records for channel8 Hit separately from Fire, 29-principal/32 physical budget')
