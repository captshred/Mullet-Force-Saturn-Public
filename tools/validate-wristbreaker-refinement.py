#!/usr/bin/env python3
"""Current-disc/fidelity checks plus unchanged approved historical regressions."""
from pathlib import Path
import subprocess,json,hashlib,struct,collections,argparse,tempfile,tarfile,io,re
from level1_refinement import read,signature,curve,peak
R=Path(__file__).resolve().parents[1];BASE='17445b421bcafd8d5c974d624ddc2a34e768d725'
def sha(b):return hashlib.sha256(b).hexdigest()
def ensure_base():
 if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
def original(n):ensure_base();return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def voices(b):
 result=[]
 for i in range((int.from_bytes(b[:2],'big')-8)//2):
  a=int.from_bytes(b[8+2*i:10+2*i],'big');result.append((b[a:a+4],[b[a+4+j*32:a+36+j*32] for j in range(b[a+2]+1)]))
 return result
def pcm(b,l):
 a=(l[3]&15)*65536+int.from_bytes(l[4:6],'big');n=int.from_bytes(l[8:10],'big')*(1 if l[3]&16 else 2);return b[a:a+n+4]
ALLOWED={'Makefile','assets/wingsuit/WDEATH.MAP','assets/wingsuit/WDEATH.SEQ','assets/wingsuit/WDEATH.TON','assets/wingsuit/WFIRE.MAP','assets/wingsuit/WMUSIC.MAP','assets/wingsuit/WMUSIC.SEQ','assets/wingsuit/WMUSIC.TON','assets/wingsuit/manifest.json','src/wingsuit_audio.c','src/wingsuit_audio_data.h'}
def validate(disc):
 ensure_base()
 lock=json.loads((R/'docs/wristbreaker-refinement-lock.json').read_text());assert lock['baseline']==BASE and set(lock['changed'])==ALLOWED
 for n,h in lock['frozen'].items():assert sha((R/n).read_bytes())==h,n
 for n,h in lock['changed'].items():assert sha((R/n).read_bytes())==h,n
 report=json.loads((R/'assets/wingsuit/wristbreaker-refinement.json').read_text());assert report['baseline']==BASE
 baseline_names=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=R).decode().splitlines())
 assert set(lock['frozen'])==baseline_names-ALLOWED
 current=set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=R).decode().splitlines())
 additions=current-baseline_names
 for n in additions:
  assert Path(n).suffix.lower() not in ('.mid','.midi','.gp','.gpx','.gp5','.wav','.aiff','.sf2'),n
  assert n.startswith(('docs/wristbreaker-','tests/wristbreaker/')) or n in {'assets/wingsuit/wristbreaker-refinement.json','tools/refine-level2-wristbreaker.py','tools/validate-wristbreaker-refinement.py','tools/analyze-wristbreaker-playback.py','tools/build-wristbreaker-driver-stress.py','tools/run-wristbreaker-playback.sh','downloads/mullet-force-level2-wristbreaker-full-refinement.zip'},n
 if (R/'downloads/mullet-force-level2-wristbreaker-full-refinement.zip').exists():
  import zipfile
  with zipfile.ZipFile(R/'downloads/mullet-force-level2-wristbreaker-full-refinement.zip') as z:
   assert all(Path(n).suffix.lower() not in ('.mid','.midi','.gp','.gpx','.gp5','.wav','.aiff','.sf2') for n in z.namelist()),'Private authoring media in delivery'
 for n,info in report['outputs'].items():assert sha((R/n).read_bytes())==info['sha256'] and (R/n).stat().st_size==info['bytes'],n
 oldh,old,end=read(original('assets/wingsuit/WMUSIC.SEQ'));h,new,end2=read((R/'assets/wingsuit/WMUSIC.SEQ').read_bytes());assert h==oldh and end==end2==541440
 oldns=[n for n in old if n['kind']=='note'];newns=[n for n in new if n['kind']=='note'];mel=[n for n in newns if n['channel']!=0];dr=[n for n in newns if n['channel']==0]
 left=[n for n in oldns if n['program']==0 and n['pan']==0];right=[n for n in oldns if n['program']==0 and n['pan']==127]
 def k(n):return tuple(n[x] for x in ('on','off','pitch','velocity','program'))+(curve(n,old),)
 counts=collections.Counter(k(n) for n in left);removed=set()
 for n in right:
  key=k(n)
  if counts[key]:removed.add(id(n));counts[key]-=1
 kept=[n for n in oldns if id(n) not in removed];assert len(removed)==1372 and len(right)-len(removed)==298
 assert [signature(n) for n in kept]==[signature(n) for n in mel]
 for a,b in zip(kept,mel):
  assert a['program']==b['program'] and a['velocity']==b['velocity'];assert curve(a,old)==curve(b,new)
  assert b['pan']==64
 assert len(dr)==2803 and peak(mel+dr)==22 and peak(mel+dr,165)==25
 assert all(n['program']==1 for n in dr)
 aliases=report['drum_key_aliases'];roles={key:role for role,keys in aliases.items() for key in keys}
 perf=sorted((n['on'],roles[n['pitch']],n['velocity']) for n in dr);assert sha(json.dumps(perf,separators=(',',':')).encode())==report['compiled_drum_performance_sha256']
 expected=collections.Counter()
 for source,count in report['drum_note_counts'].items():expected[report['mapping'][source]]+=count
 assert collections.Counter(roles[n['pitch']] for n in dr)==expected
 for key in roles:
  hits=[n for n in dr if n['pitch']==key];assert all(a['off']<=b['on'] for a,b in zip(hits,hits[1:])),'Overlapping alias keys'
  assert hits[-1]['off']<=end+hits[0]['on'],'Alias overlaps next loop'
 for path in ['assets/wingsuit/WMUSIC.SEQ','assets/wingsuit/WDEATH.SEQ']:
  for e in read((R/path).read_bytes())[1]:assert not(e['kind']=='event' and e['payload'][0]&240==176 and e['payload'][1] in (120,123))
 oldfx=original('assets/wingsuit/WDEATH.SEQ');fxseq=(R/'assets/wingsuit/WDEATH.SEQ').read_bytes();diff=[i for i,(a,b) in enumerate(zip(oldfx,fxseq)) if a!=b];assert len(diff)==1 and oldfx[diff[0]]==123 and fxseq[diff[0]]==32
 b=original('assets/cd/STAGE.TON');bv=voices(b);tone=(R/'assets/wingsuit/WMUSIC.TON').read_bytes();v=voices(tone);assert len(v)==3
 for i in (0,2):
  assert v[i][0]==bytes([6])+bv[i][0][1:]
  a=bv[i][1][0];c=v[i][1][0];assert pcm(b,a)==pcm(tone,c)
  assert all(a[j]==c[j] for j in range(32) if j not in (3,4,5));assert a[3]&240==c[3]&240
 sm={s['role']:s for s in json.loads(original('assets/music/level1-custom-report.json'))['samples']}
 assert len(v[1][1])==39
 for layer in v[1][1]:
  key=layer[0];assert key==layer[1] and key in roles;a=bv[sm[roles[key]]['program']][1][0]
  assert pcm(b,a)==pcm(tone,layer)
  assert layer[25]==a[25]+key-sm[roles[key]]['root']
  assert all(a[j]==layer[j] for j in range(32) if j not in (0,1,3,4,5,25));assert layer[3]&240==a[3]&240
 oldfx=original('assets/wingsuit/WDEATH.TON');fx=(R/'assets/wingsuit/WDEATH.TON').read_bytes()
 for (a,ls),(b,rs) in zip(voices(oldfx),voices(fx)):
  assert a==b
  for l,r in zip(ls,rs):
   assert pcm(oldfx,l)==pcm(fx,r);assert all(l[j]==r[j] for j in range(32) if j not in (3,4,5));assert l[3]&240==r[3]&240
 assert (R/'src/wingsuit_audio.c').read_text()==original('src/wingsuit_audio.c').decode().replace('SND_SetSeqVl(0,127,0)','SND_SetSeqVl(0,108,0)')
 header=(R/'src/wingsuit_audio_data.h').read_text();const={k:int(n) for k,n in re.findall(r'#define MF_WS_(\w+) (\d+)\n',header)}
 mp=(R/'assets/wingsuit/WFIRE.MAP').read_bytes();high=148864
 for off,name,prefix in [(16,'WDEATH.SEQ','SEQ'),(24,'WDEATH.TON','TON'),(32,'WMUSIC.SEQ','MUSIC_SEQ'),(40,'WMUSIC.TON','MUSIC_TON'),(48,'WFIRE.TON','FIRE_TON')]:
  address=int.from_bytes(mp[off+1:off+4],'big');size=int.from_bytes(mp[off+5:off+8],'big');assert address==high and size==(R/'assets/wingsuit'/name).stat().st_size and size%4==address%4==0
  assert const[prefix+'_ADDR']==address and const[prefix+'_BYTES']==size;high=address+size
 assert high==report['sound_ram_high_water']==506192 and 524288-high==18096
 for i,label in [(2,'ATTACK'),(3,'LOOP')]:
  a=int.from_bytes(fx[8+2*i:10+2*i],'big');l=voices(fx)[i][1][0];sa=(l[3]&15)*65536+int.from_bytes(l[4:6],'big')
  assert const['FLAME_'+label+'_LAYER_ADDR']==const['TON_ADDR']+a+4
  assert const['FLAME_'+label+'_PCM_ADDR']==const['TON_ADDR']+sa
 if disc:
  from wingsuit_disc import directory_records
  image=(R/'build/mullet-force.bin').read_bytes();files={}
  def scan(record,prefix=''):
   for name,rec in directory_records(image,record):
    if name in ('.','..'):continue
    if rec[25]&2:scan(rec,prefix+name+'/')
    else:
     at=struct.unpack_from('<I',rec,2)[0]*2048;n=struct.unpack_from('<I',rec,10)[0];files[prefix+name]=image[at:at+n]
  scan(image[16*2048+156:16*2048+190])
  for path in (R/'build/cd').rglob('*'):
   if path.is_file():assert files[path.relative_to(R/'build/cd').as_posix().upper()]==path.read_bytes(),path
  for name in ('STAGE.SEQ','STAGE.TON','FX.SEQ','FX.TON','CUSTOM.MAP'):assert files[name]==original('assets/cd/'+name)
  assert sha((R/'build/SOURCE-SHA256SUMS.txt').read_bytes()).encode() in files['0.BIN']
  subprocess.run(['sha256sum','--check','build/SOURCE-SHA256SUMS.txt'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 print('PASS Wristbreaker: 1372 duplicates removed, 298 differing events retained, 2803 drums exact; original melodic gates/pitches/velocity/bends preserved; PCM/SFX/gameplay/Level1 protected; RAM506192/524288',flush=True)
def historical(tests):
 ensure_base()
 with tempfile.TemporaryDirectory(prefix='wristbreaker-approved-') as d:
  ref=Path(d)
  with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as archive:archive.extractall(ref,filter='data')
  for name in ('.git','.deps','build'):(ref/name).symlink_to(R/name,target_is_directory=True)
  subprocess.run(['python3','tools/validate-level1-refinement.py',*(['--test'] if tests else [])],cwd=ref,check=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args();validate(a.disc);historical(a.test)
