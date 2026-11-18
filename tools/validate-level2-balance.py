#!/usr/bin/env python3
"""Only the five existing Level2 SFX note-on velocities may change."""
from pathlib import Path
import subprocess,hashlib,struct,argparse,tempfile
R=Path(__file__).resolve().parents[1];BASE='aa15e10bc0efee0b512f068b04e41b8485c79466'
ALLOWED={'Makefile','src/wingsuit_audio.c','tests/wingsuit_audio_mock/SEGA_SND.H'}
def old(n):return subprocess.check_output(['git','show',BASE+':'+n],cwd=R)
def validate(disc):
 if subprocess.run(['git','cat-file','-e',BASE],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
 for n in subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=R).decode().splitlines():
  if n not in ALLOWED:assert (R/n).read_bytes()==old(n),('unrelated change',n)
 s=old('src/wingsuit_audio.c').decode()
 for a in ['hit_midi(1,60,110)','midi(4+i,1,60,110)','midi(2+selected,1,60,110)','midi(i,1,MF_WS_FLAME_ATTACK_NOTE,110)','midi(i,1,MF_WS_FLAME_LOOP_NOTE,110)']:
  assert s.count(a)==1;s=s.replace(a,a.replace('110','127'))
 assert (R/'src/wingsuit_audio.c').read_text()==s
 m=old('tests/wingsuit_audio_mock/SEGA_SND.H').decode().replace('typedef struct {unsigned short mode;unsigned char stat;} SndSeqStat;\n','').replace('void SND_GetSeqStat(SndSeqStat *,int);\n','');assert (R/'tests/wingsuit_audio_mock/SEGA_SND.H').read_text()==m
 for name,end in [('assets/cd/CUSTOM.MAP',521304),('assets/wingsuit/WFIRE.MAP',506660)]:
  b=(R/name).read_bytes();a=len(b)-16;assert int.from_bytes(b[a+1:a+4],'big')+int.from_bytes(b[a+5:a+8],'big')==end
 if disc:validate_disc()
 print('PASS exact5-value audio delta: five Level2 SFX110->127; music control0 volume108 unchanged; Level1/POOWAH/all PCM+SEQ/slides/gameplay/priorities/schedulers/cleanup exact; RAM unchanged',flush=True)
def validate_disc():
 from wingsuit_disc import directory_records
 image=(R/'build/mullet-force.bin').read_bytes();files={}
 def scan(rec,prefix=''):
  for n,r in directory_records(image,rec):
   if n in ('.','..'):continue
   if r[25]&2:scan(r,prefix+n+'/')
   else:
    a=struct.unpack_from('<I',r,2)[0]*2048;size=struct.unpack_from('<I',r,10)[0];files[prefix+n]=image[a:a+size]
 scan(image[16*2048+156:16*2048+190])
 for p in (R/'build/cd').rglob('*'):
  if p.is_file():assert files[p.relative_to(R/'build/cd').as_posix().upper()]==p.read_bytes()
 assert hashlib.sha256((R/'build/SOURCE-SHA256SUMS.txt').read_bytes()).hexdigest().encode() in files['0.BIN'];subprocess.run(['sha256sum','--check','build/SOURCE-SHA256SUMS.txt'],cwd=R,check=True,stdout=subprocess.DEVNULL)
def tests():
 subprocess.run(['python3','tools/test-level2-balance.py'],cwd=R,check=True)
 subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-Itests/sound_mock','-Isrc','tests/ugh_transport_test.c','-o','/tmp/mf-balance-poowah'],cwd=R,check=True);subprocess.run(['/tmp/mf-balance-poowah'],check=True)
 with tempfile.TemporaryDirectory(prefix='level2-balance-working-') as d:
  ref=Path(d);subprocess.run(['git','clone','--quiet','--shared','--no-checkout',str(R),d],check=True);subprocess.run(['git','checkout','--quiet','--detach',BASE],cwd=ref,check=True);origin=subprocess.check_output(['git','remote','get-url','origin'],cwd=R).decode().strip();subprocess.run(['git','remote','set-url','origin',origin],cwd=ref,check=True)
  for n in ('.deps','build'):(ref/n).symlink_to(R/n,target_is_directory=True)
  subprocess.run(['make','test'],cwd=ref,check=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args();validate(a.disc)
 if a.test:tests()
