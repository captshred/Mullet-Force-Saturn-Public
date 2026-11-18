#!/usr/bin/env python3
"""Strict sample-only delta against the exact working protected UGH build."""
from pathlib import Path
import subprocess,json,struct,hashlib,argparse,tempfile
from level1_refinement import read
R=Path(__file__).resolve().parents[1];BASE='517c7f790f1b11f4abddf9908b83cb5acfbf5c5b'
ALLOW={'Makefile','assets/cd/FX.SEQ','assets/cd/FX.TON','assets/cd/CUSTOM.MAP','src/music_data.h','assets/music/report.json','assets/public-runtime-lock.json'}
def old(n):return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def validate(disc=False):
 if subprocess.run(['git','cat-file','-e',BASE],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
 for n in subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=R).decode().splitlines():
  if n not in ALLOW:assert (R/n).read_bytes()==old(n),('unrelated baseline change',n)
 a=old('assets/cd/FX.TON');b=(R/'assets/cd/FX.TON').read_bytes();p=int.from_bytes(a[24:26],'big')+4;sa=((a[p+3]&15)<<16)|int.from_bytes(a[p+4:p+6],'big');prefix=bytearray(a[:sa]);prefix[p+3]&=239;prefix[p+8:p+10]=(8420).to_bytes(2,'big');assert b[:sa]==prefix
 report=json.loads((R/'assets/sfx/poowah-report.json').read_text());assert hashlib.sha256(b[sa:sa+16840]).hexdigest()==report['pcm_sha256'];assert b.count(a[sa:sa+10725])==0
 src=old('assets/cd/FX.SEQ');seq=(R/'assets/cd/FX.SEQ').read_bytes()
 for i in range(8):
  x=int.from_bytes(src[2+i*4:6+i*4],'big');y=int.from_bytes(src[6+i*4:10+i*4],'big');xx=int.from_bytes(seq[2+i*4:6+i*4],'big');yy=int.from_bytes(seq[6+i*4:10+i*4],'big');assert src[x:y]==seq[xx:yy]
 h,e,end=read(seq,8);oldh,olde,_=read(src,8);assert e[2]['velocity']==olde[2]['velocity']==110 and e[2]['pitch']==60 and e[2]['program']==8;assert e[2]['off']==e[3]['on']==782
 oldh=bytearray(oldh);oldh[8:12]=(782).to_bytes(4,'big');assert h==oldh
 hdr=old('src/music_data.h').decode().replace('MF_FX_TON_BYTES 193684','MF_FX_TON_BYTES 199796').replace('MF_STAGE_SEQ_ADDR 342916','MF_STAGE_SEQ_ADDR 349028').replace('MF_STAGE_TON_ADDR 383044','MF_STAGE_TON_ADDR 389156').replace('MF_DEATH_MIN_TICKS 59','MF_DEATH_MIN_TICKS 46').replace('{25,11,47,8,7,28,32,49,63}','{25,11,47,8,7,28,32,49,50}');assert (R/'src/music_data.h').read_text()==hdr
 mp=(R/'assets/cd/CUSTOM.MAP').read_bytes();last=148864
 for at,name in zip((16,24,32,40),('FX.SEQ','FX.TON','STAGE.SEQ','STAGE.TON')):
  addr=int.from_bytes(mp[at+1:at+4],'big');n=int.from_bytes(mp[at+5:at+8],'big');assert addr==last and n==len((R/'assets/cd'/name).read_bytes());last=addr+n
 assert last==521304 and 524288-last==2984
 if disc:
  from wingsuit_disc import directory_records
  image=(R/'build/mullet-force.bin').read_bytes();files={}
  def scan(rec,prefix=''):
   for name,r in directory_records(image,rec):
    if name in ('.','..'):continue
    if r[25]&2:scan(r,prefix+name+'/')
    else:
     a=struct.unpack_from('<I',r,2)[0]*2048;n=struct.unpack_from('<I',r,10)[0];files[prefix+name]=image[a:a+n]
  scan(image[16*2048+156:16*2048+190])
  for p in (R/'build/cd').rglob('*'):
   if p.is_file():assert files[p.relative_to(R/'build/cd').as_posix().upper()]==p.read_bytes()
  assert hashlib.sha256((R/'build/SOURCE-SHA256SUMS.txt').read_bytes()).hexdigest().encode() in files['0.BIN'];subprocess.run(['sha256sum','--check','build/SOURCE-SHA256SUMS.txt'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 print('PASS sample-only POOWAH: PCM16 mono11025Hz,8420frames/16840bytes; protection code/all8 other FX raw songs+PCM+tones/velocities/music/Level2 exact; min46; RAM521304/524288,2984free',flush=True)
def tests():
 for name,args,extra in [('ugh_transport_test',['-Itests/sound_mock','-Isrc'],[]),('human_death_routing_test',['-include','build/build-info.h','-Isrc'],[]),('slide_pause_game_test',['-include','build/build-info.h','-Isrc'],['src/game.c'])]:
  exe='/tmp/poowah-'+name;subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',*args,'tests/'+name+'.c',*extra,'-o',exe],cwd=R,check=True);subprocess.run([exe],check=True)
 with tempfile.TemporaryDirectory(prefix='poowah-working-') as d:
  ref=Path(d);subprocess.run(['git','clone','--quiet','--shared','--no-checkout',str(R),d],check=True);subprocess.run(['git','checkout','--quiet','--detach',BASE],cwd=ref,check=True);origin=subprocess.check_output(['git','remote','get-url','origin'],cwd=R).decode().strip();subprocess.run(['git','remote','set-url','origin',origin],cwd=ref,check=True)
  for n in ('.deps','build'):(ref/n).symlink_to(R/n,target_is_directory=True)
  subprocess.run(['make','test'],cwd=ref,check=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args();validate(a.disc)
 if a.test:tests()
