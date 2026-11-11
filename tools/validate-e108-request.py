#!/usr/bin/env python3
"""Freeze AI 3.0 and all audio content/scheduling outside the notification fix."""
from pathlib import Path
import io,subprocess,sys,tarfile,tempfile
R=Path(__file__).resolve().parents[1]
BASE='0827a42ac863102102ea9dd693109f1483384bdb'
allowed={'Makefile','src/wingsuit_audio.c','src/wingsuit_audio.h','src/wingsuit_runtime.c'}
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='e108-ai3-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 for p in ref.rglob('*'):
  if p.is_file() and str(p.relative_to(ref)) not in allowed:
   assert (R/p.relative_to(ref)).read_bytes()==p.read_bytes(),str(p.relative_to(ref))
 old=(ref/'src/wingsuit_audio.c').read_text();new=(R/'src/wingsuit_audio.c').read_text()
 old_step=old[old.index('void mf_ws_audio_step('):].strip()
 new_step=new[new.index('static void audio_step('):new.index('/* Keep every approved scheduler')].strip().replace('static void audio_step(', 'void mf_ws_audio_step(',1)
 assert old_step==new_step,'approved music/Flame/SFX scheduler changed'
 # Command formatting, sample lease/retirement and event queues remain exact.
 start='/* Fixed capacities';end='/* Pinned 2.10 exports consumed-command cursor'
 assert old.split(start,1)[1].split(end,1)[0]==new.split(start,1)[1].split(end,1)[0]
 for n in ('.git','.deps'):(ref/n).symlink_to(R/n,target_is_directory=True)
 if '--disc' in sys.argv:(ref/'build').symlink_to(R/'build',target_is_directory=True)
 subprocess.run(['python3','tools/validate-punk-ai.py',*[a for a in sys.argv[1:] if a in ('--test','--disc')]],cwd=ref,check=True)
print('PASS E108 scope: exact AI3/gameplay/assets/build profile; exact music/Flame/SFX scheduler and command formatting; four scoped transport/diagnostic integrations',flush=True)
if '--test' in sys.argv:
 subprocess.run(['python3','tools/test-e108-request.py'],cwd=R,check=True)
 subprocess.run(['python3','tools/test-recovered-audio.py'],cwd=R,check=True)
 with tempfile.TemporaryDirectory() as d:
  exe=str(Path(d)/'startup')
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-Itests/wingsuit_audio_mock','-Itests/sound_mock','-Isrc','tests/e008_startup_test.c','-o',exe],cwd=R,check=True)
  subprocess.run([exe],cwd=R,check=True)
  s=(R/'tests/wingsuit_runtime_test.c').read_text().replace('"../src/wingsuit_runtime.c"','"'+str(R/'src/wingsuit_runtime.c')+'"')
  s=s.replace('unsigned short ws_vdp1','mf_ws_startup_trace mf_ws_startup_capture;\nunsigned short ws_vdp1')
  # Add observations to the actual runtime test in this temporary unit only.
  s=s.replace('int main(void)','int runtime_cases(void)')
  s+='''
int main(void){assert(runtime_cases()==0);
 mf_ws_startup_sample *p=&mf_ws_startup_capture.samples[0];
 memset(&mf_ws_startup_capture,0,sizeof(mf_ws_startup_capture));
 assert(!strcmp(startup_evidence(),"NO CAPTURE"));
 mf_ws_startup_capture.count=1;assert(!strcmp(startup_evidence(),"CHECK DRIVER IMAGE"));
 mf_ws_startup_capture.signature=0x53454741;p->gate=0x1038;p->queue[0]=12;
 assert(!strcmp(startup_evidence(),"REQUEST FLAG CLEAR"));
 p->flags=0x8000;assert(!strcmp(startup_evidence(),"NO PROGRESS EVIDENCE"));
 mf_ws_startup_capture.count=2;p->stage=MF_WS_AUDIO_DRIVER_READY;p->boot=1;
 mf_ws_startup_capture.samples[1]=*p;mf_ws_startup_capture.samples[1].timer=1;
 assert(!strcmp(startup_evidence(),"TIMER ALIVE NO ACK"));
 mf_ws_startup_capture.samples[1].cursor=16;
 assert(!strcmp(startup_evidence(),"COMMANDS PROGRESSED"));
 puts("PASS diagnostic evidence labels and mocked runtime load/restart sequences");return 0;}
'''
  p=Path(d)/'runtime.c';p.write_text(s)
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-Itests/wingsuit_mock','-Isrc',str(p),'src/wingsuit.c','-o',exe],cwd=R,check=True)
  for trial in range(16):subprocess.run([exe],cwd=R,check=True)
  print('PASS 16 fresh-process runtime suites with original warm restart/load cases')
