#!/usr/bin/env python3
"""Exact scoped slide/pause fidelity, current ISO and approved regressions."""
from pathlib import Path
import subprocess,json,hashlib,importlib.util,tarfile,tempfile,io,argparse,struct
from level1_refinement import read,signature,curve
R=Path(__file__).resolve().parents[1];BASE='d97b5a9e77f418d16f22e408690f038f727e1828'
ALLOWED={'Makefile','src/music.c','src/wingsuit_audio_data.h','assets/wingsuit/WMUSIC.SEQ','assets/wingsuit/WMUSIC.MAP','assets/wingsuit/WFIRE.MAP'}
def ensure():
 if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
def original(n):return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def validate(disc=False):
 ensure();names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=R).decode().splitlines()
 for n in names:
  if n not in ALLOWED:assert (R/n).read_bytes()==original(n),n
 code=original('src/music.c').decode().replace('Pause/resume owns all other fixed ports 0..6.','Pause/resume owns SFX ports1..6; music control0 keeps running.').replace('for(i=0;i<7;i++)if(i!=4 && !(pause_mask','for(i=1;i<7;i++)if(i!=4 && !(pause_mask').replace('pause_mask!=0x6f','pause_mask!=0x6e')
 assert (R/'src/music.c').read_text()==code
 spec=importlib.util.spec_from_file_location('correction',R/'tools/correct-slide-pause.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 src=original('assets/wingsuit/WMUSIC.SEQ');new=(R/'assets/wingsuit/WMUSIC.SEQ').read_bytes();expected,affected=m.corrected(src);assert new==expected
 h,old,end=read(src);hh,events,ee=read(new);assert h==hh and end==ee
 ons=[n for n in old if n['kind']=='note'];newns=[n for n in events if n['kind']=='note'];assert [signature(n) for n in ons]==[signature(n) for n in newns]
 selected={(a['channel'],a['note_on']) for a in affected}
 for a,b in zip(ons,newns):
  assert a['program']==b['program'] and a['pan']==b['pan']
  c=curve(a,old);d=curve(b,events)
  if (a['channel'],a['on']) in selected:
   assert d==tuple((t if i==0 else 240+2*(t-240),v) for i,(t,v) in enumerate(c))
  else:assert c==d,'Unrelated pitch trajectory changed'
 delta=len(new)-len(src);assert delta==468
 for name in ('WMUSIC.MAP','WFIRE.MAP'):
  mp=bytearray(original('assets/wingsuit/'+name));mp[37:40]=len(new).to_bytes(3,'big')
  for off in (40,48):
   if off<len(mp)-8:mp[off+1:off+4]=(int.from_bytes(mp[off+1:off+4],'big')+delta).to_bytes(3,'big')
  assert bytes(mp)==(R/'assets/wingsuit'/name).read_bytes()
 import re
 hdr=original('src/wingsuit_audio_data.h').decode()
 for key in ('MUSIC_SEQ_BYTES','MUSIC_TON_ADDR','FIRE_TON_ADDR'):hdr=re.sub(r'(#define MF_WS_'+key+r') (\d+)',lambda m:m[1]+' '+str(int(m[2])+delta),hdr)
 assert hdr==(R/'src/wingsuit_audio_data.h').read_text()
 if disc:
  from wingsuit_disc import directory_records
  image=(R/'build/mullet-force.bin').read_bytes();assert image[:16]==b'SEGA SEGASATURN ';files={}
  def scan(rec,prefix=''):
   for name,r in directory_records(image,rec):
    if name in ('.','..'):continue
    if r[25]&2:scan(r,prefix+name+'/')
    else:
     at=struct.unpack_from('<I',r,2)[0]*2048;size=struct.unpack_from('<I',r,10)[0];files[prefix+name]=image[at:at+size]
  scan(image[16*2048+156:16*2048+190])
  for p in (R/'build/cd').rglob('*'):
   if p.is_file():assert files[p.relative_to(R/'build/cd').as_posix().upper()]==p.read_bytes(),p
  assert hashlib.sha256((R/'build/SOURCE-SHA256SUMS.txt').read_bytes()).hexdigest().encode() in files['0.BIN']
  subprocess.run(['sha256sum','--check','build/SOURCE-SHA256SUMS.txt'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 print('PASS203 slide trajectories/102 onsets: hold240, movement240->480 ticks; all notes and unrelated curves exact; pause excludes music only; RAM506660/524288',flush=True)
def historical(tests):
 with tempfile.TemporaryDirectory(prefix='slide-pause-approved-') as d:
  ref=Path(d)
  with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
  # Own index/excludes keep snapshot SDK symlinks out of historical scope checks.
  subprocess.run(['git','init','-q',str(ref)],check=True)
  subprocess.run(['git','remote','add','origin',R.as_uri()],cwd=ref,check=True)
  subprocess.run(['git','fetch','--quiet','--no-tags','--depth=1','origin',BASE],cwd=ref,check=True)
  # Continue older parent fetches from the canonical public remote in shallow CI.
  origin=subprocess.check_output(['git','remote','get-url','origin'],cwd=R).decode().strip()
  subprocess.run(['git','remote','set-url','origin',origin],cwd=ref,check=True)
  subprocess.run(['git','update-ref','refs/heads/approved',BASE],cwd=ref,check=True)
  subprocess.run(['git','symbolic-ref','HEAD','refs/heads/approved'],cwd=ref,check=True)
  subprocess.run(['git','read-tree',BASE],cwd=ref,check=True)
  (ref/'.git/info/exclude').write_text('.deps\nbuild\n')
  for n in ('.deps','build'):(ref/n).symlink_to(R/n,target_is_directory=True)
  subprocess.run(['python3','tools/validate-wristbreaker-refinement.py',*(['--test'] if tests else [])],cwd=ref,check=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args();validate(a.disc)
 if a.test:
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-Itests/sound_mock','-Isrc','tests/slide_pause_transport_test.c','-o','/tmp/mf-slide-pause-test'],cwd=R,check=True);subprocess.run(['/tmp/mf-slide-pause-test'],check=True)
 if a.test:
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-include','build/build-info.h','-Isrc','tests/slide_pause_game_test.c','src/game.c','-o','/tmp/mf-slide-pause-game'],cwd=R,check=True);subprocess.run(['/tmp/mf-slide-pause-game'],check=True)
 historical(a.test)
