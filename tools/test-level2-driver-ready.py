#!/usr/bin/env python3
"""Real loader startup regression plus two deliberate bug reintroductions."""
from pathlib import Path
import subprocess,tempfile,resource
R=Path(__file__).resolve().parents[1]
subprocess.run(['python3',str(R/'tools/audit-level2-driver-ready.py')],check=True)
source=(R/'src/wingsuit_audio.c').read_text()
mutants=[('timer-alias',source.replace('boot_counter=sound_word(0x41a);','boot_counter=sound_word(0x8838);').replace('if(sound_word(0x41a)==boot_counter','if(sound_word(0x8838)==boot_counter')),
 ('late-snapshot',source.replace('    boot_counter=sound_word(0x41a);','').replace('    boot=BOOT_CPU;return 1;','    boot_counter=sound_word(0x41a);boot=BOOT_CPU;return 1;'))]
def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with tempfile.TemporaryDirectory(prefix='mf-ready-') as tmp:
 tmp=Path(tmp)
 for name,s in [('fixed',source),*mutants]:
  audio=tmp/'audio.c';audio.write_text(s)
  harness=(R/'tests/wingsuit_audio_test.c').read_text().replace('"../src/wingsuit_audio.c"','"'+str(audio)+'"').replace('"../src/wingsuit.c"','"'+str(R/'src/wingsuit.c')+'"')
  (tmp/'wingsuit_audio_test.c').write_text(harness)
  test=tmp/'wingsuit_ready_test.c';test.write_text((R/'tests/wingsuit_ready_test.c').read_text())
  exe=tmp/name
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(R/'tests/wingsuit_audio_mock'),'-I'+str(R/'tests/sound_mock'),'-I'+str(R/'src'),str(test),'-o',str(exe)],check=True)
  result=subprocess.run([str(exe)],cwd=R,text=True,capture_output=True,preexec_fn=no_core)
  if name=='fixed':
   assert result.returncode==0,(result.stdout,result.stderr)
   print(result.stdout,end='')
  else:
   assert result.returncode!=0 and 'Assertion' in result.stderr,(name,result.stdout,result.stderr)
   if name=='timer-alias':assert 'ready=-1 cause=DRIVER READY expected=1 actual=0' in result.stdout
   print('PASS readiness mutation rejected:',name)
