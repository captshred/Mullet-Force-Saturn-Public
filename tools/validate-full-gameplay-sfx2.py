#!/usr/bin/env python3
"""Lock the complete approved gameplay/visual base and exact SFX2 payloads."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile,shutil,struct
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--allow-sparse',action='store_true',help='local diagnostics only: verify missing files by index blob; never used by builds/CI');a=p.parse_args()
m=json.loads((r/'assets/full-gameplay-sfx2/preservation.json').read_text());missing=[]
def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
# Explicit, hash-pinned art integration exceptions; retain every original lock.
art=json.loads((r/'assets/arcade-fx/preservation.json').read_text())
allowed={'assets/cd/HIT.TGA','src/main.c','src/animation_preview.c','tools/build.sh','tools/build-native.sh','tools/audit-sprite-memory.py'}
updates=art['authorized_base_updates']
assert set(updates)==allowed
for name,change in updates.items():assert change['before']==m['preserved_base_blobs'][name],name
for name,sha in m['preserved_base_blobs'].items():
 sha=updates[name]['after'] if name in updates else sha
 path=r/name
 if not path.exists() and a.allow_sparse:
  indexed=subprocess.check_output(['git','ls-files','-s','--',name],cwd=r,text=True).split();assert indexed[1]==sha,(name,'index differs from approved base');missing.append(name);continue
 assert path.is_file(),(name,'missing approved base file')
 assert blob(path.read_bytes())==sha,(name,'approved gameplay/visual base changed')
for name,sha in m['sfx2_blobs'].items():assert blob((r/name).read_bytes())==sha,(name,'SFX2 payload differs')
assert hashlib.sha256((r/'tests/full_gameplay_sfx2_baseline/game.c').read_bytes()).hexdigest()==m['gameplay_baseline_sha256']
# Audit the real wrapper chain without fetching an SDK or starting a build.
with tempfile.TemporaryDirectory(prefix='mf-profile-check-') as d:
 t=Path(d);(t/'tools').mkdir()
 for src in (r/'tools').glob('build-*.sh'):shutil.copy(src,t/'tools'/src.name)
 names=m['profile_flags']
 (t/'tools/build.sh').write_text("#!/usr/bin/env bash\npython3 - <<'CODE'\nimport json,os\nprint(json.dumps({k:os.environ.get(k) for k in "+repr(list(names))+"}))\nCODE\n")
 flags=json.loads(subprocess.check_output(['bash',str(t/'tools/build-gameplay-parallax.sh'),'--native'],text=True))
 assert flags==names,(flags,names)
wrapper=(r/'tools/build-full-gameplay-sfx2.sh').read_text();assert 'bash tools/build-gameplay-parallax.sh "$@"' in wrapper and 'export MF_PRESERVE_AUDIO=1' in wrapper
workflow=(r/'.github/workflows/build.yml').read_text();assert 'full-gameplay-sfx2) bash tools/build-full-gameplay-sfx2.sh --native ;;' in workflow
assert 'workflow_dispatch:' in workflow and '\n  push:' not in workflow and '\n  pull_request:' not in workflow
subprocess.run(['python3','tools/validate-sfx2.py'],cwd=r,check=True)
# Byte budgets of the unchanged allocation plan, including SDK ownership.
assert 106496+65536+262144==434176 and 524288-434176==90112
if a.disc:
 assert not missing
 for name in ['live-city-mode.txt','city-cleanup-mode.txt','city-neon-mode.txt','punch-combo-mode.txt','preserve-audio-mode.txt']:assert (r/'build'/name).read_text().strip()=='1',name
 image=(r/'build/mullet-force.bin').read_bytes();files={}
 def scan(directory,prefix=''):
  pos=0
  while pos<len(directory):
   length=directory[pos]
   if not length:pos=(pos//2048+1)*2048;continue
   rec=directory[pos:pos+length];pos+=length;name=rec[33:33+rec[32]]
   if name in (b'\0',b'\1'):continue
   name=name.decode().split(';')[0];start=struct.unpack_from('<I',rec,2)[0]*2048;size=struct.unpack_from('<I',rec,10)[0];data=image[start:start+size]
   if rec[25]&2:scan(data,prefix+name+'/')
   else:files[prefix+name]=data
 rec=image[16*2048+156:16*2048+190];start=struct.unpack_from('<I',rec,2)[0]*2048;size=struct.unpack_from('<I',rec,10)[0];scan(image[start:start+size])
 for name in ['CICELL.BIN','CIMAP.BIN','CIPAL.BIN','DR0.TGA','DR1.TGA','DR2.TGA']:assert files[name]==(r/'assets/city-cleanup'/name).read_bytes(),name
 for name in ['LCSKY.BIN','LCMAP.BIN']:assert files[name]==(r/'assets/city-gameplay-parallax'/name).read_bytes(),name
 for name in ['FX.TON','FX.SEQ','CUSTOM.MAP','STAGE.TON','STAGE.SEQ']:assert files[name]==(r/'assets/cd'/name).read_bytes(),name
 assert files['COMBO/XC0.TGA']==(r/'assets/punch-combo/XC0.TGA').read_bytes()
 assert files['COMBO/XC1.TGA']==(r/'assets/punch-combo/XC1.TGA').read_bytes()
 print('PASS actual unified disc: approved cleanup/skyline/props/combos and SFX2/music payloads coexist')
print('PASS approved base preservation, original sprite/background/scroll code, exact SFX2 samples and full wrapper profile')
if missing:print('BLOCKED byte checks for sparse local files (original Git blobs retained): '+', '.join(missing))
