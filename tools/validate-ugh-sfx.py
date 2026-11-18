#!/usr/bin/env python3
"""UGH PCM, once-only FX velocity changes, protected source scope and regressions."""
from pathlib import Path
import subprocess,json,hashlib,struct,tempfile,argparse,importlib.util
from level1_refinement import read
R=Path(__file__).resolve().parents[1];BASE='4f37a19dcea7767daa6177706b0aab4c6d1909ad'
ALLOWED={'Makefile','.github/workflows/build.yml','src/main.c','src/music.c','src/music.h','src/music_data.h','assets/cd/FX.SEQ','assets/cd/FX.TON','assets/cd/CUSTOM.MAP','assets/music/report.json','assets/public-runtime-lock.json','tests/sound_mock/SEGA_SND.H'}
def old(n):return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def tone(b,i):
 a=int.from_bytes(b[8+2*i:10+2*i],'big');v=bytearray(b[a:a+36]);sa=((v[7]&15)<<16)|int.from_bytes(v[8:10],'big');n=int.from_bytes(v[12:14],'big');pcm=b[sa:sa+n*(1 if v[7]&16 else 2)];v[7]&=240;v[8:10]=bytes(2);return v,pcm,sa

def validate(disc=False):
 if subprocess.run(['git','cat-file','-e',BASE],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
 for n in subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=R).decode().splitlines():
  if n not in ALLOWED:assert (R/n).read_bytes()==old(n),('protected baseline changed',n)
 assert (R/'src/main.c').read_text()==old('src/main.c').decode().replace('if(game.stage==MF_STAGE_LEVEL2_ENTRY){','if(game.stage==MF_STAGE_LEVEL2_ENTRY && !mf_music_protected()){')
 src=old('assets/cd/FX.SEQ');seq=(R/'assets/cd/FX.SEQ').read_bytes();b=(R/'assets/cd/FX.TON').read_bytes();previous=old('assets/cd/FX.TON');report=json.loads((R/'assets/sfx/ugh-report.json').read_text())
 for i in range(8):
  assert tone(b,i)[:2]==tone(previous,i)[:2],('existing PCM/instrument changed',i)
  h,e,end=read(src,i);hh,ee,xx=read(seq,i)
  for n in e:
   if n['kind']=='note':n['velocity']=min(127,max(1,(115*n['velocity']+50)//100))
  assert (h,e,end)==(hh,ee,xx),('FX timing/control or velocity drift',i)
 v,pcm,sa=tone(b,8);ov,opcm,unused=tone(previous,8);assert b.count(opcm)==0 and b.count(tone(b,6)[1])==1
 assert len(pcm)==10725 and hashlib.sha256(pcm).hexdigest()==report['pcm_sha256'];v[12:14]=ov[12:14];assert v==ov
 h,e,end=read(seq,8);ns=[n for n in e if n['kind']=='note'];assert len(ns)==1 and ns[0]['velocity']==110 and ns[0]['program']==8 and ns[0]['pitch']==60
 assert ns[0]['off']/960>=len(pcm)/11025+.049
 mp=(R/'assets/cd/CUSTOM.MAP').read_bytes();last=148864
 for at,n in zip((16,24,32,40),('FX.SEQ','FX.TON','STAGE.SEQ','STAGE.TON')):
  a=int.from_bytes(mp[at+1:at+4],'big');size=int.from_bytes(mp[at+5:at+8],'big');assert a==last and a%4==0 and size==len((R/'assets/cd'/n).read_bytes());last=a+size
 assert last==report['sound_ram_high_water']==515192 and 524288-last==9096
 assert '#define MF_MUSIC_VOLUME 108' in (R/'src/music_data.h').read_text()
 assert '#define MF_SFX_VOLUME 112' in (R/'src/music_data.h').read_text()
 assert '#define MF_DEATH_MIN_TICKS 59' in (R/'src/music_data.h').read_text()
 if disc:
  from wingsuit_disc import directory_records
  image=(R/'build/mullet-force.bin').read_bytes();files={}
  def scan(rec,prefix=''):
   for name,x in directory_records(image,rec):
    if name in ('.','..'):continue
    if x[25]&2:scan(x,prefix+name+'/')
    else:
     a=struct.unpack_from('<I',x,2)[0]*2048;size=struct.unpack_from('<I',x,10)[0];files[prefix+name]=image[a:a+size]
  scan(image[16*2048+156:16*2048+190])
  for p in (R/'build/cd').rglob('*'):
   if p.is_file():assert files[p.relative_to(R/'build/cd').as_posix().upper()]==p.read_bytes()
  assert hashlib.sha256((R/'build/SOURCE-SHA256SUMS.txt').read_bytes()).hexdigest().encode() in files['0.BIN']
  subprocess.run(['sha256sum','--check','build/SOURCE-SHA256SUMS.txt'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 print('PASS UGH: original8 PCM/tones exact, ARGH removed, only8 FX velocities110->127 once, UGH110 and pitch/envelope unchanged; protected Level1 music/Level2/gameplay; RAM515192/524288 (9096 free)',flush=True)

def tests():
 for n,inc,extra in [('ugh_transport_test',['-Itests/sound_mock','-Isrc'],[]),('human_death_routing_test',['-include','build/build-info.h','-Isrc'],[]),('slide_pause_game_test',['-include','build/build-info.h','-Isrc'],['src/game.c'])]:
  exe='/tmp/mf-ugh-'+n;subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',*inc,'tests/'+n+'.c',*extra,'-o',exe],cwd=R,check=True);subprocess.run([exe],check=True)
 with tempfile.TemporaryDirectory(prefix='ugh-approved-') as d:
  ref=Path(d);subprocess.run(['git','clone','--quiet','--shared','--no-checkout',str(R),d],check=True);subprocess.run(['git','checkout','--quiet','--detach',BASE],cwd=ref,check=True)
  origin=subprocess.check_output(['git','remote','get-url','origin'],cwd=R).decode().strip();subprocess.run(['git','remote','set-url','origin',origin],cwd=ref,check=True)
  for n in ('.deps','build'):(ref/n).symlink_to(R/n,target_is_directory=True)
  subprocess.run(['make','test'],cwd=ref,check=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args();validate(a.disc)
 if a.test:tests()
