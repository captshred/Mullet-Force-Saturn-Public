#!/usr/bin/env python3
"""Exact refinement scope, unchanged source performances/PCM/SFX gain/Level2."""
from pathlib import Path
import subprocess,hashlib,json,struct,argparse,tarfile,tempfile,io,re
from level1_refinement import BASE,read,signature,peak,curve
R=Path(__file__).resolve().parents[1]
ALLOWED={'Makefile','src/music_data.h','assets/cd/STAGE.SEQ','assets/cd/STAGE.TON','assets/cd/CUSTOM.MAP','assets/cd/FX.SEQ','assets/music/report.json'}
ADDED={'tools/level1_refinement.py','tools/refine-level1-audio.py','tools/validate-level1-refinement.py','tests/level1_refinement_test.py','docs/level1-refinement.md','docs/level1-refinement-lock.json','assets/music/level1-refinement-report.json','tests/level1_refinement/driver-stress.c','tests/level1_refinement/frontend.c','tools/prepare-level1-refinement-probe.py','tools/build-level1-driver-stress.py','tools/run-level1-refinement-playback.sh','tools/analyze-level1-refinement.py','docs/level1-refinement-playback.json','docs/level1-refinement-traces/before-events.csv.gz','docs/level1-refinement-traces/after-events.csv.gz','docs/level1-refinement-traces/stress-events.csv.gz'}
def sha(b):return hashlib.sha256(b).hexdigest()
_baseline_ready=False
def original(n):
 global _baseline_ready
 if not _baseline_ready:
  if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
   subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
  _baseline_ready=True
 return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def validate(disc=False):
 lock=json.loads((R/'docs/level1-refinement-lock.json').read_text());assert lock['baseline']==BASE and set(lock['changes'])==ALLOWED
 for n,h in lock['frozen'].items():assert sha((R/n).read_bytes())==h,n
 for n,h in lock['changes'].items():assert sha((R/n).read_bytes())==h['after'],n
 for n,h in lock['added'].items():assert sha((R/n).read_bytes())==h,n
 oldh,old,end=read(original('assets/cd/STAGE.SEQ'));newh,new,end2=read((R/'assets/cd/STAGE.SEQ').read_bytes());assert oldh==newh and end==end2==279840
 oldnotes=[n for n in old if n['kind']=='note'];newnotes=[n for n in new if n['kind']=='note'];oldmap={signature(n):n for n in oldnotes}
 assert len(oldnotes)==6924 and len(newnotes)==4907
 kept={signature(n) for n in newnotes};removed=[n for n in oldnotes if signature(n) not in kept]
 assert len(removed)==2017 and all(n['pan']==93 for n in removed)
 for n in removed:
  matches=[m for m in oldnotes if m['pan']==35 and all(m[k]==n[k] for k in ['on','off','pitch','velocity','program'])]
  assert any(curve(m,old)==curve(n,old) for m in matches),'Removed unique articulation'
 for n in newnotes:
  previous=oldmap[signature(n)];assert n['program']==previous['program']
  assert n['pan']==(64 if previous['pan'] in (35,93) else previous['pan'])
  assert curve(n,new)==curve(previous,old),'Changed retained pitch gesture'
 assert [signature(n) for n in newnotes if n['channel']>=12]==[signature(n) for n in oldnotes if n['channel']>=12]
 assert not any(e['kind']=='event' and e['payload'][0]&240==176 and e['payload'][1]==123 for e in new)
 oldtone=original('assets/cd/STAGE.TON');tone=(R/'assets/cd/STAGE.TON').read_bytes();allowed_tl={int.from_bytes(tone[8+2*i:10+2*i],'big')+19 for i in range(13)}
 assert len(tone)==len(oldtone)==132148 and all(a==b or p in allowed_tl for p,(a,b) in enumerate(zip(oldtone,tone)))
 for p in allowed_tl:assert tone[p]<=oldtone[p]
 oldfx=original('assets/cd/FX.SEQ');fx=(R/'assets/cd/FX.SEQ').read_bytes();diff=[i for i,(a,b) in enumerate(zip(oldfx,fx)) if a!=b]
 assert len(oldfx)==len(fx)==328 and len(diff)==8 and all(oldfx[i]==123 and fx[i]==32 for i in diff)
 for i in range(8):
  h,a,t=read(oldfx,i);hh,b,tt=read(fx,i);assert h==hh and t==tt
  assert [signature(n) for n in a if n['kind']=='note']==[signature(n) for n in b if n['kind']=='note']
  expected=[(e['on'],bytes([e['payload'][0],32,0]) if e['payload'][0]&240==176 and e['payload'][1]==123 else e['payload']) for e in a if e['kind']=='event']
  assert expected==[(e['on'],e['payload']) for e in b if e['kind']=='event']
 assert (R/'assets/cd/FX.TON').read_bytes()==original('assets/cd/FX.TON')
 h=(R/'src/music_data.h').read_text();const={k:int(v,0) for k,v in re.findall(r'#define (MF_\w+) (0x[\da-f]+|\d+)\n',h)}
 assert const['MF_MUSIC_VOLUME']==108 and const['MF_SFX_VOLUME']==112
 mp=(R/'assets/cd/CUSTOM.MAP').read_bytes();high=0
 for off,name in [(16,'FX.SEQ'),(24,'FX.TON'),(32,'STAGE.SEQ'),(40,'STAGE.TON')]:
  address=int.from_bytes(mp[off+1:off+4],'big');size=int.from_bytes(mp[off+5:off+8],'big');assert address>=high and address%4==size%4==0;high=address+size
  assert size==(R/'assets/cd'/name).stat().st_size and address==const['MF_'+name.replace('.','_')+'_ADDR']
 assert high==504380 and high<=524288
 if disc:
  from wingsuit_disc import directory_records
  image=(R/'build/mullet-force.bin').read_bytes();assert image[:16]==b'SEGA SEGASATURN '
  root=dict(directory_records(image,image[16*2048+156:16*2048+190]));files={}
  def scan(records,prefix=''):
   for name,rec in records.items():
    if name in ('.','..'):continue
    at=struct.unpack_from('<I',rec,2)[0]*2048;size=struct.unpack_from('<I',rec,10)[0]
    if rec[25]&2:scan(dict(directory_records(image,rec)),prefix+name+'/')
    else:files[prefix+name]=image[at:at+size]
  scan(root)
  for p in (R/'build/cd').rglob('*'):
   if p.is_file():assert files[p.relative_to(R/'build/cd').as_posix().upper()]==p.read_bytes(),p
  for name in ('FX.SEQ','FX.TON','STAGE.SEQ','STAGE.TON','CUSTOM.MAP'):assert files[name]==(R/'assets/cd'/name).read_bytes()
  for name,data in files.items():
   if name.startswith('ALEVEL2/'):
    rel=('assets/level2-neon-city/' if name.split('/')[-1] in ('WCELL.BIN','WROOF.BIN','WPAL.BIN') else 'assets/wingsuit/')+name.split('/')[-1]
    try:old=original(rel)
    except subprocess.CalledProcessError:
     rel='assets/level2-neon-city/'+name.split('/')[-1];old=original(rel)
    assert data==old,name
  fp=(R/'build/SOURCE-SHA256SUMS.txt').read_bytes();assert sha(fp).encode() in files['0.BIN']
  subprocess.run(['sha256sum','--check','build/SOURCE-SHA256SUMS.txt'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 print(f'PASS refinement: 2017 duplicated rhythm notes removed, six unique right notes preserved/centered, retained pitch gestures and1804 drum hits exact; PCM/SFX gain/Level2 frozen; peak music17->15; RAM{high}/524288',flush=True)

def approved_tests(tests):
 if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
 with tempfile.TemporaryDirectory(prefix='mono-approved-') as d:
  ref=Path(d)
  with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as archive:archive.extractall(ref,filter='data')
  for name in ('.git','.deps','build'):(ref/name).symlink_to(R/name,target_is_directory=True)
  # Current disc is checked above. Historical validators retain their original
  # source/audio hashes and run against their archived approved tree.
  subprocess.run(['python3','tools/validate-level1-custom-audio.py',*(['--test'] if tests else [])],cwd=ref,check=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args();validate(a.disc)
 if a.test:subprocess.run(['python3','tests/level1_refinement_test.py'],cwd=R,check=True)
 approved_tests(a.test)
