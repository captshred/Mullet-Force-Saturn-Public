#!/usr/bin/env python3
"""Current native bank/routing validation plus protected baseline regressions."""
from pathlib import Path
import subprocess,hashlib,json,struct,tempfile,argparse
from level1_refinement import read
R=Path(__file__).resolve().parents[1];BASE='38ed9a690f9349f490b5280992fcef882b32aaaf'
ALLOWED={'.github/workflows/build.yml','Makefile','src/game.c','src/game.h','src/music.c','src/music_data.h','assets/cd/FX.SEQ','assets/cd/FX.TON','assets/cd/CUSTOM.MAP','assets/music/report.json','assets/public-runtime-lock.json','tests/slide_pause_transport_test.c'}
def old(n):return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def tone(b,i):
 a=int.from_bytes(b[8+2*i:10+2*i],'big');v=bytearray(b[a:a+36]);sa=((v[7]&15)<<16)|int.from_bytes(v[8:10],'big');n=int.from_bytes(v[12:14],'big');pcm=b[sa:sa+n*(1 if v[7]&16 else 2)];v[7]&=240;v[8:10]=bytes(2);return v,pcm,sa

def validate(disc):
 if subprocess.run(['git','cat-file','-e',BASE],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
 for n in subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=R).decode().splitlines():
  if n not in ALLOWED:assert (R/n).read_bytes()==old(n),('protected baseline changed',n)
 scope=json.loads((R/'docs/human-death-source-scope.json').read_text())
 for n,d in scope['changed_existing_text_files'].items():
  assert n in ALLOWED and hashlib.sha256(old(n)).hexdigest()==d['before_sha256']
  assert hashlib.sha256((R/n).read_bytes()).hexdigest()==d['after_sha256'],('unreviewed text drift',n)
 report=json.loads((R/'assets/sfx/human-death-report.json').read_text());b=(R/'assets/cd/FX.TON').read_bytes();seq=(R/'assets/cd/FX.SEQ').read_bytes()
 for i in range(8):
  assert tone(b,i)[:2]==tone(old('assets/cd/FX.TON'),i)[:2],('original instrument changed',i)
  assert read(seq,i)==read(old('assets/cd/FX.SEQ'),i),('original sequence changed',i)
 assert int.from_bytes(b[:2],'big')==26 and int.from_bytes(seq[:2],'big')==9
 v,pcm,sa=tone(b,8);assert len(pcm)==report['frames']==12274 and v[7]&16 and not v[7]&32 and v[29]==84
 assert hashlib.sha256(pcm).hexdigest()==report['new_pcm_sha256'];assert tone(b,6)[1]==tone(old('assets/cd/FX.TON'),6)[1]
 # Exact old voice PCM occurs once; both approved hit events choose song6.
 assert b.count(tone(b,6)[1])==1
 h,e,end=read(seq,8);notes=[x for x in e if x['kind']=='note'];assert len(notes)==1 and notes[0]['program']==8 and notes[0]['pitch']==60 and notes[0]['velocity']==110
 assert (notes[0]['off']-notes[0]['on'])/960>=len(pcm)/11025+.049
 mp=(R/'assets/cd/CUSTOM.MAP').read_bytes();assert mp[:16]==old('assets/cd/CUSTOM.MAP')[:16] and mp[-8:]==old('assets/cd/CUSTOM.MAP')[-8:]
 last=None
 for at,n in zip((16,24,32,40),('FX.SEQ','FX.TON','STAGE.SEQ','STAGE.TON')):
  addr=int.from_bytes(mp[at+1:at+4],'big');size=int.from_bytes(mp[at+5:at+8],'big');assert addr%4==size%4==0 and size==len((R/'assets/cd'/n).read_bytes())
  if last is not None:assert addr==last
  last=addr+size
 assert last==report['sound_ram_high_water']==516744 and 524288-last==7544
 for n,a in report['outputs'].items():assert hashlib.sha256((R/'assets/cd'/n).read_bytes()).hexdigest()==a['sha256']
 if disc:
  from wingsuit_disc import directory_records
  image=(R/'build/mullet-force.bin').read_bytes();assert image[:16]==b'SEGA SEGASATURN ';files={}
  def scan(rec,prefix=''):
   for name,x in directory_records(image,rec):
    if name in ('.','..'):continue
    if x[25]&2:scan(x,prefix+name+'/')
    else:
     at=struct.unpack_from('<I',x,2)[0]*2048;size=struct.unpack_from('<I',x,10)[0];files[prefix+name]=image[at:at+size]
  scan(image[16*2048+156:16*2048+190])
  for p in (R/'build/cd').rglob('*'):
   if p.is_file():assert files[p.relative_to(R/'build/cd').as_posix().upper()]==p.read_bytes(),p
  assert hashlib.sha256((R/'build/SOURCE-SHA256SUMS.txt').read_bytes()).hexdigest().encode() in files['0.BIN']
  subprocess.run(['sha256sum','--check','build/SOURCE-SHA256SUMS.txt'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 print('PASS current assets: original8 voices/SEQ songs exact, shared old PCM once, new8-bit pitch/gate correct, protected assets/code unchanged; RAM516744/524288 (7544 free)',flush=True)

def tests():
 for name,includes in [('human_death_routing_test',['-include','build/build-info.h','-Isrc']),('slide_pause_transport_test',['-Itests/sound_mock','-Isrc']),('slide_pause_game_test',['-include','build/build-info.h','-Isrc'])]:
  cmd=['cc','-std=c99','-Wall','-Wextra','-Werror',*includes,'tests/'+name+'.c']
  if name=='slide_pause_game_test':cmd+=['src/game.c']
  subprocess.run(cmd+['-o','/tmp/mf-'+name],cwd=R,check=True);subprocess.run(['/tmp/mf-'+name],check=True)
 # Full-state deterministic input replay against the exact approved game.c.
 with tempfile.TemporaryDirectory(prefix='human-death-state-') as d:
  src=Path(d)/'approved-game.c';src.write_bytes(old('src/game.c'));outputs=[]
  for label,game in [('approved',str(src)),('current','src/game.c')]:
   exe=str(Path(d)/label)
   subprocess.run(['cc','-std=c99','-O2','-include','build/build-info.h','-Isrc','tests/human_death_gameplay_snapshot.c',game,'-o',exe],cwd=R,check=True)
   outputs.append(subprocess.check_output([exe]))
  assert outputs[0]==outputs[1],('gameplay state changed',outputs)
  print('PASS24000-frame full-state approved/current gameplay replay:',outputs[0].decode().strip(),flush=True)
 # Existing approved regressions run on the protected baseline snapshot. Current
 # changed collision and transport implementations are exercised above.
 with tempfile.TemporaryDirectory(prefix='human-death-approved-') as d:
  ref=Path(d)
  subprocess.run(['git','clone','--quiet','--shared','--no-checkout',str(R),d],check=True)
  subprocess.run(['git','checkout','--quiet','--detach',BASE],cwd=ref,check=True)
  origin=subprocess.check_output(['git','remote','get-url','origin'],cwd=R).decode().strip();subprocess.run(['git','remote','set-url','origin',origin],cwd=ref,check=True)
  for n in ('.deps','build'):(ref/n).symlink_to(R/n,target_is_directory=True)
  subprocess.run(['python3','tools/validate-slide-pause.py','--test'],cwd=ref,check=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args();validate(a.disc)
 if a.test:tests()
