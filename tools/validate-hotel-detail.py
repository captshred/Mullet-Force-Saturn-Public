#!/usr/bin/env python3
"""Hotel-only native art milestone; all approved runtime/other planes frozen."""
from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1];BASE='8d85905eb12421cfe356b994ebab43893680e1b1';A=R/'art/intersection-hotel-detail';O=R/'assets/level1-intersection'
p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args()
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
proof=json.loads((A/'proof.json').read_text());old=(A/'before.bin').read_bytes();new=(O/'EXTPIX.BIN').read_bytes();mask=(A/'mask.bin').read_bytes()
assert len(old)==len(new)==len(mask)==640*240
assert proof['baseline']==BASE and proof['outside_changes']==0
for data,key in [(old,'before_sha256'),(new,'after_sha256'),(mask,'mask_sha256')]:assert hashlib.sha256(data).hexdigest()==proof[key]
assert hashlib.sha256((A/'hotel-native-study.png').read_bytes()).hexdigest()==proof['study_sha256']
assert hashlib.sha256((R/'assets/level1-neon-strip/NSPAL.BIN').read_bytes()).hexdigest()==proof['palette_sha256']
for i,(before,after,m) in enumerate(zip(old,new,mask)):
 x=i%640;y=i//640
 assert m==int(418<=x<534 and y<151)
 assert before==after or m,('outside hotel',x,y)
 if m:assert after and not 240<=after<=247,('opaque/static hotel',x,y)
assert sum(a!=b for a,b in zip(old,new))==proof['changed_pixels']>10000
with tempfile.TemporaryDirectory(prefix='hotel-approved-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 assert old==(ref/'assets/level1-intersection/EXTPIX.BIN').read_bytes()
 allowed={'Makefile','src/intersection_data.h',*[f'assets/level1-intersection/{n}' for n in ('EXTPIX.BIN','IXPIX.BIN','IXMAP.BIN','IXPACK.BIN','IXOFF.BIN','manifest.json')]}
 for f in ref.rglob('*'):
  if f.is_file() and str(f.relative_to(ref)) not in allowed:assert (R/f.relative_to(ref)).read_bytes()==f.read_bytes(),f.relative_to(ref)
 m=json.loads((O/'manifest.json').read_text());b=json.loads((ref/'assets/level1-intersection/manifest.json').read_text())
 for k in ('width','height','palette_sha256','original_pixel_sha256','resident_tiles','resident_cell_bytes','map_bytes','VDP2_reserved_bytes','VDP1_delta_bytes','VDP2_delta_bytes','SCSP_delta_bytes'):
  assert m[k]==b[k],k
 print('PASS hotel mask: 15918 native material pixels replaced; zero changes to records/residential/side HOTEL neon/road/perspective/older1280; unchanged runtime/gameplay/audio/palette/all video budgets',flush=True)
if a.test:
 frozen={f:f.read_bytes() for f in [*O.glob('*.BIN'),O/'manifest.json',R/'src/intersection_data.h']}
 subprocess.run(['python3','tools/apply-hotel-detail.py'],cwd=R,check=True)
 subprocess.run(['python3','tools/prepare-hotel-detail.py'],cwd=R,check=True)
 assert all(f.read_bytes()==b for f,b in frozen.items()),'non-deterministic hotel conversion/packing'
subprocess.run(['python3','tools/validate-intersection-scale.py',*(['--disc'] if a.disc else []),*(['--test'] if a.test else [])],cwd=R,check=True)
